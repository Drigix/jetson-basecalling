#!/usr/bin/env python
#
# RODAN
# v1.0
# (c) 2020,2021,2022 Don Neumann
#

import torch
import numpy as np
import os, sys, re, argparse, pickle, time, glob
from torch.utils.data import Dataset, DataLoader
from ctcdecode import CTCBeamDecoder
from ont_fast5_api.fast5_interface import get_fast5_file
from torch.multiprocessing import Queue, Process
import model as network
import ont
import psutil
import csv
import threading
import time

def segment(seg, s):
    seg = np.concatenate((seg, np.zeros((-len(seg)%s))))
    nrows=((seg.size-s)//s)+1
    n=seg.strides[0]
    return np.lib.stride_tricks.as_strided(seg, shape=(nrows,s), strides=(s*n, n))

def convert_statedict(state_dict):
    from collections import OrderedDict
    new_checkpoint = OrderedDict()
    for k, v in state_dict.items():
        name = k[7:] # remove module.
        new_checkpoint[name] = v
    return new_checkpoint

def load_model(modelfile, config = None, args = None):
    if config.amp:
        from apex import amp
        if args.debug: print("Using apex amp")
    if modelfile == None:
        sys.stderr.write("No model file specified!")
        sys.exit(1)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.debug: print("Using device:", device)
    if args.arch is not None:
        model = network.network(config=config, arch=args.arch).to(device)
    else:
        model = network.network(config=config).to(device)
    if args.debug: print("Loading pretrained weights:", modelfile)
    state_dict = torch.load(modelfile)["state_dict"]
    if "state_dict" in state_dict:
        model.load_state_dict(convert_statedict(state_dict["state_dict"]))
    else:
        model.load_state_dict(torch.load(modelfile)["state_dict"])
    if args.debug: print(model)

    model.eval()
    torch.set_grad_enabled(False)
    optimizer = torch.optim.Adam(model.parameters(), lr = config.lr)
    if config.amp:
        model, optimizer = amp.initialize(model, optimizer, opt_level="O1", verbosity=0)
    return model, device

def mp_files(dir, queue, config, args):
    chunkname = []
    chunks = None
    queuechunks = None
    chunkremainder = None
    for file in glob.iglob(dir+"/**/*.fast5", recursive=True):
        f5 = get_fast5_file(file, mode="r")
        for read in f5.get_reads():
            while queue.qsize() >= 100:
                time.sleep(1)
            #outfile = os.path.splitext(os.path.basename(file))[0]
            try:
                signal = read.get_raw_data(scale=True)
                if args.debug: print("mp_files:", file)
            except:
                continue
            signal_start = 0
            signal_end = len(signal)
            med, mad = ont.med_mad(signal[signal_start:signal_end])
            signal = (signal[signal_start:signal_end] - med) / mad
            newchunks = segment(signal, config.seqlen)
            if chunks is not None:
                chunks = np.concatenate((chunks, newchunks), axis=0)
                queuechunks += [read.read_id] * newchunks.shape[0]
            else:
                chunks = newchunks
                queuechunks = [read.read_id] * newchunks.shape[0]
            if chunks.shape[0] >= args.batchsize:
                for i in range(0, chunks.shape[0]//args.batchsize, args.batchsize):
                    queue.put((queuechunks[:args.batchsize], chunks[:args.batchsize]))
                    chunks = chunks[args.batchsize:]
                    queuechunks = queuechunks[args.batchsize:]
        f5.close()
    if len(queuechunks) > 0:
        if args.debug: print("queuechunks:", len(queuechunks), chunks.shape[0])
        for i in range(0, int(np.ceil(chunks.shape[0]/args.batchsize)), args.batchsize):
            start = i * args.batchsize
            end = start + args.batchsize
            if end > chunks.shape[0]: end = chunks.shape[0]
            queue.put((queuechunks[start:end], chunks[start:end]))
            if args.debug: print("put last chunk", chunks[start:end].shape[0])
    queue.put(("end", None))


def mp_gpu(inqueue, outqueue, config, args):
    model, device = load_model(args.model, config, args)
    shtensor = None
    while True:
        time1 = time.perf_counter()
        read = inqueue.get()
        file = read[0]
        if type(file) == str: 
            outqueue.put(("end", None))
            break
        chunks = read[1]
        for i in range(0, chunks.shape[0], config.batchsize):
            end = i+config.batchsize
            if end > chunks.shape[0]: end = chunks.shape[0]
            event = torch.unsqueeze(torch.FloatTensor(chunks[i:end]), 1).to(device, non_blocking=True)
            out=model.forward(event)
            if shtensor is None:
                shtensor = torch.empty((out.shape), pin_memory=True, dtype=out.dtype)
            if out.shape[1] != shtensor.shape[1]:
                shtensor = torch.empty((out.shape), pin_memory=True, dtype=out.dtype)
            logitspre = shtensor.copy_(out).numpy()
            if args.debug: print("mp_gpu:", logitspre.shape)
            outqueue.put((file, logitspre))
            del out
            del logitspre

def mp_write(queue, config, args):
    files = None
    chunks = None
    totprocessed = 0
    finish = False
    while True:
        if queue.qsize() > 0:
            newchunk = queue.get()
            if type(newchunk[0]) == str:
                if not len(files): break
                finish = True
            else:
                if chunks is not None:
                    chunks = np.concatenate((chunks, newchunk[1]), axis=1)
                    files = files + newchunk[0]
                else:
                    chunks = newchunk[1]
                    files = newchunk[0]
            while files.count(files[0]) < len(files) or finish:
                totlen = files.count(files[0])
                callchunk = chunks[:,:totlen,:]
                logits = np.transpose(np.argmax(callchunk, -1), (1, 0))
                label_blank = np.zeros((logits.shape[0], logits.shape[1] + 200))
                try:
                    out,outstr = ctcdecoder(logits, label_blank, pre=callchunk, beam_size=args.beamsize)
                except:
                    # failure in decoding
                    out = ""
                    outstr = ""
                    pass
                seq = ""
                if len(out) != len(outstr):
                    sys.stderr.write("FAIL:", len(out), len(outstr), files[0])
                    sys.exit(1)
                for j in range(len(out)):
                    seq += outstr[j]
                readid = os.path.splitext(os.path.basename(files[0]))[0]
                print(">"+readid)
                if args.reverse:
                    print(seq[::-1])
                else:
                    print(seq)
                newchunks = chunks[:,totlen:,:]
                chunks = newchunks
                files = files[totlen:]
                totprocessed+=1
                if finish and not len(files): break
            if finish: break
                
alphabet = ["N", "A", "C", "G", "T"]

def ctcdecoder(logits, label, blank=False, beam_size=5, alphabet=["N", "A", "C", "G", "T"], pre=None):
    ret = np.zeros((label.shape[0], label.shape[1]+50))
    retstr = []
    
    # Dekoder CTC
    if pre is not None:
        decoder = CTCBeamDecoder(alphabet, beam_width=beam_size, blank_id=0)

    for i in range(logits.shape[0]):
        if pre is not None:
            softmaxed = torch.softmax(torch.tensor(pre[:, i, :]), dim=-1).unsqueeze(0)
            beamcur, _, _, out_seq_len = decoder.decode(softmaxed)
            beamcur = "".join([alphabet[idx] for idx in beamcur[0, 0, :out_seq_len[0, 0].item()].tolist()])
        
        prev = None
        cur = []
        pos = 0
        for j in range(logits.shape[1]):
            if not blank:
                if logits[i, j] != prev:
                    prev = logits[i, j]
                    if prev != 0 and 0 <= prev < len(alphabet):  # Zabezpieczenie przed błędnym indeksem
                        ret[i, pos] = prev
                        pos += 1
                        cur.append(alphabet[prev])
            else:
                if logits[i, j] == 0:
                    break
                if 0 <= logits[i, j] < len(alphabet):
                    ret[i, pos] = logits[i, j]
                    cur.append(alphabet[logits[i, j]])
                    pos += 1
        
        if pre is not None:
            retstr.append(beamcur)
        else:
            retstr.append("".join(cur))

    return ret, retstr

def get_size(path):
    if os.path.isdir(path):
        size = sum(os.path.getsize(os.path.join(dirpath, filename))
                   for dirpath, _, filenames in os.walk(path)
                   for filename in filenames)
    elif os.path.isfile(path):
        size = os.path.getsize(path)
    else:
        raise ValueError(f"Path {path} doesn't exist!")
    return size / (1024 ** 2)

def save_execution_stats_to_csv(filepath, metrics):
    with open(filepath, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['file_size', 'execution_time', 'batch_size'])
        writer.writeheader() 
        for metric in metrics:
            writer.writerow(metric)

def save_metrics_to_csv(filepath, metrics):
    with open(filepath, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['time', 'ram', 'cpu', 'temp_cpu'])
        writer.writeheader()
        for metric in metrics:
            writer.writerow(metric)

def monitor_metrics(stop_event, start_time, metrics_list):
    """Monitor system metrics every ... seconds and save to the list."""
    while not stop_event.is_set():
        temps = psutil.sensors_temperatures()
        metrics = {
            'time': time.time() - start_time,
            'ram': psutil.virtual_memory().used / (1024 ** 2),
            # 'gpu': stats['GPU1'],
            'cpu': psutil.cpu_percent(interval=None),
            'temp_cpu': temps["thermal-fan-est"][0].current
            # 'cpu2': stats['CPU2'],
            # 'cpu3': stats['CPU3'],
            # 'cpu4': stats['CPU4'],
            # 'temperature_cpu': stats['Temp CPU'],
            # 'temperature_gpu': stats['Temp GPU'],
            # 'power_avg': stats['power avg'],
        }
        metrics_list.append(metrics)
        time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Basecall fast5 files')
    parser.add_argument("fast5dir", default=None, type=str)
    parser.add_argument("-a", "--arch", default=None, type=str, help="architecture settings")
    parser.add_argument("-m", "--model", default="rna.torch", type=str, help="default: rna.torch")
    parser.add_argument("-r", "--reverse", default=True, action="store_true", help="reverse for RNA (default: True)")
    parser.add_argument("-b", "--batchsize", default=200, type=int, help="default: 200")
    parser.add_argument("-B", "--beamsize", default=5, type=int, help="CTC beam search size (default: 5)")
    parser.add_argument("-e", "--errors", default=False, action="store_true")
    parser.add_argument("-d", "--debug", default=False, action="store_true")
    args = parser.parse_args()

    try:
        records_size_mb = get_size(args.fast5dir)
        print(f"Sample data size: {records_size_mb:.2f} MB")
    except ValueError as e:
        print(e)

    execution_stats_file = os.path.join('./', 'execution_statistic.csv')
    metric_file = os.path.join('./', 'jetson_metrics.csv')

    # Monitor RAM usage
    ram_usage_before = psutil.virtual_memory().used / (1024 ** 2)

    # Start time
    start_time = time.time()
    print(
        f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    system_metrics = []
    stop_event = threading.Event()

    monitoring_thread = threading.Thread(target=monitor_metrics, args=(
        stop_event, start_time, system_metrics))
    monitoring_thread.start()

    # Start processing
    try:
        torchdict = torch.load(args.model, map_location="cpu")
        origconfig = torchdict["config"]

        if args.debug: print(origconfig)
        origconfig["debug"] = args.debug
        config = network.objectview(origconfig)
        config.batchsize = args.batchsize

        if args.arch != None:
            if args.debug: print("Loading architecture from:", args.arch)
            args.arch = eval(open(args.arch, "r").read())
        else:
            args.arch = eval(config.arch)

        if args.debug: print("Using sequence len:", int(config.seqlen))
        
        torch.backends.cudnn.enabled = True
        torch.backends.cudnn.deterministic = True

        call_queue = Queue()
        write_queue = Queue()
        p1 = Process(target=mp_files, args=(args.fast5dir, call_queue, config, args,))
        p2 = Process(target=mp_gpu, args=(call_queue, write_queue, config, args,))
        p3 = Process(target=mp_write, args=(write_queue, config, args,))
        p1.start()
        p2.start()
        p3.start()
        p1.join()
        p2.join()
        p3.join()
    except KeyboardInterrupt:
        print("\nInterrupted! Stopping processes...")
        stop_event.set()
        monitoring_thread.join()
    finally:
        # Stop monitoring
        stop_event.set()
        monitoring_thread.join()
        
        print("Collect system metrics...")

    # Monitor RAM and GPU usage after
    ram_usage_after = psutil.virtual_memory().used / (1024 ** 2)

    # Resource usage summary
    print(
        f"RAM usage before: {ram_usage_before:.2f} MB, after: {ram_usage_after:.2f} MB")

    # End time
    end_time = time.time()
    print(
        f"End time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")

    # Execution time
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.2f} sekund")
    
    # Save execution stats to CSV
    save_execution_stats_to_csv(execution_stats_file, [{'file_size': records_size_mb, 'execution_time': execution_time, 'batch_size': args.batchsize}])

    # Save collected metrics to CSV
    save_metrics_to_csv(metric_file, system_metrics)