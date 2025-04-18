import argparse
import os
import copy
import time
import datetime
import numpy as np
from litetr_encoder import LiteTransformerEncoder
import torch
import torch.nn as nn
import torch.utils.data as Data
import constants as Constants
import psutil
import threading
from ctc_decoder import BeamCTCDecoder, GreedyDecoder
from tqdm import tqdm
from torch import multiprocessing as mp
torch.multiprocessing.set_sharing_strategy('file_system')


os.environ['CUDA_VISIBLE_DEVICES'] = '0' #need change


class Call(nn.Module):  #delete
    def __init__(self, opt):
        super(Call, self).__init__()
        checkpoint = torch.load(opt.model, map_location=opt.device)
        model_opt = checkpoint['settings']
        self.model = LiteTransformerEncoder(d_model=model_opt.d_model,
                                            d_ff=model_opt.d_ff,
                                            n_head=model_opt.n_head,
                                            num_encoder_layers=model_opt.n_layers,
                                            label_vocab_size=model_opt.label_vocab_size,
                                            dropout=model_opt.dropout)
        state_dict = checkpoint['model']
        from collections import OrderedDict
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            name = k[7:] # remove `module.`
            new_state_dict[name] = v
        self.model.load_state_dict(new_state_dict)  
        print('[Info] Trained model state loaded.')
    def forward(self, signal, signal_lengths):
        return self.model(signal, signal_lengths)


class CallDataset(Data.Dataset):
    def __init__(self, argv):
        self.records_dir = argv.records_dir
        self.filenames = os.listdir(argv.records_dir)
        self.count = len(self.filenames)
        self.half = argv.half

    def __len__(self):
        return self.count

    def __getitem__(self, idx):
        fname = self.filenames[idx]
        signal = np.load(self.records_dir + '/' + fname)
        if self.half:
            signal = signal.astype(np.float16)
        read_id = os.path.splitext(fname)[0]
        return read_id, signal

def writer(argv,item,write_mutex):
    read_id_list, row_num_list, log_probs_list, output_lengths_list = item
    assert len(read_id_list) == len(row_num_list)
    start_decode = datetime.datetime.now()
    print('reads = {}, start to decode'.format(len(read_id_list)))
    probs = torch.cat(log_probs_list).to(argv.device)
    lengths = torch.cat(output_lengths_list).to(argv.device)
    decoder = BeamCTCDecoder('-ATCG ', blank_index=0, alpha=0.0, lm_path=None, beta=0.0, cutoff_top_n=6,
                             cutoff_prob=1.0, beam_width=3, num_processes=8)  #cutoff_top_n=6
    decoded_output, offsets = decoder.decode(probs, lengths)

    while write_mutex.value != 1:
        time.sleep(0.2)

    fw=open(argv.outpath,'a')
    write_mutex.value = 0
    idx=0
    for x in range(len(row_num_list)):
        row_num=row_num_list[x]
        read_id = read_id_list[x]
        transcript = [v[0] for v in decoded_output[idx:idx + row_num]]
        idx = idx + row_num
        transcript = ''.join(transcript)
        transcript = transcript.replace(' ', '')
        if len(transcript) > 0:
            fw.write('>' + str(read_id) + '\n')
            fw.write(transcript + '\n')
    fw.close()
    print('\n end decode, time = ', datetime.datetime.now()-start_decode)
    write_mutex.value = 1

def decode_process(argv, qdecoder):
    pool = mp.Pool(argv.threads)
    manager = mp.Manager()
    write_mutex = manager.Value('i', 1)
    while True:
        item = qdecoder.get(timeout=200)
        try:
            qdecoder_size = qdecoder.qsize()
            print('\n current qdecoder size: ', qdecoder_size)
        except NotImplementedError:
            pass
        if item is None:
            print('decoder, qdoceder is None')
            pool.close()
            pool.join()
            return
        pool.apply_async(func=writer, args=(argv, item, write_mutex))
        
def get_size(path):
    if os.path.isdir(path):
        size = sum(os.path.getsize(os.path.join(dirpath, filename))
                   for dirpath, _, filenames in os.walk(path)
                   for filename in filenames)
    elif os.path.isfile(path):
        size = os.path.getsize(path)
    else:
        raise ValueError(f"Path {path} doesn't exist!")
    return round(size / (1024 ** 2), 2)

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
            'time': datetime.datetime.now() - start_time,
            'ram': psutil.virtual_memory().used / (1024 ** 2),
            # 'gpu': stats['GPU1'],
            'cpu': psutil.cpu_percent(interval=1),
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-model', required=True)
    parser.add_argument('-records_dir', required=True)
    parser.add_argument('-output', required=True)
    parser.add_argument('-no_cuda', action='store_true')
    parser.add_argument('-threads', type=int,default=1)
    parser.add_argument('-half', action='store_true', default=False)
    parser.add_argument('-batch_size', required=True)
    argv = parser.parse_args()

    argv.cuda = not argv.no_cuda
    device = torch.device('cuda' if argv.cuda else 'cpu')
    argv.device = device
    print("device", device)

    if not os.path.exists(argv.output):
        os.makedirs(argv.output)
    if os.path.exists(os.path.join(argv.output, 'out.fasta')):
        os.remove(os.path.join(argv.output, 'out.fasta'))
    argv.outpath = os.path.join(argv.output, 'out.fasta')

    try:
        records_size_mb = get_size(argv.records_dir)
        print(f"Sample data size: {records_size_mb:.2f} MB")
    except ValueError as e:
        print(e)
        return
    
    execution_stats_file = os.path.join('./', 'execution_statistic.csv')
    metric_file = os.path.join('./', 'jetson_metrics.csv')

    # Monitor RAM usage
    ram_usage_before = psutil.virtual_memory().used / (1024 ** 2)
    
    # Start time
    start_time = datetime.datetime.now()

    system_metrics = []
    stop_event = threading.Event()

    monitoring_thread = threading.Thread(target=monitor_metrics, args=(
        stop_event, start_time, system_metrics))
    monitoring_thread.start()

    #load model and prepare dataloader
    torch.set_grad_enabled(False)
    model = Call(argv).to(argv.device)
    model.eval()
    model.share_memory()
    if argv.half:
        model.half()

    try:
        #create queue and process
        qdecoder = mp.Queue()
        decoder_proc = mp.Process(target=decode_process, args=(argv, qdecoder))
        decoder_proc.start()
        
        batch_size = int(argv.batch_size)
        
        call_dataset = CallDataset(argv)
        data_iter = Data.DataLoader(dataset=call_dataset, batch_size=batch_size, num_workers=0)
        with torch.no_grad():
            read_id_list = []
            row_num_list = []
            log_probs_list = []
            output_lengths_list = []
            # encoded_num = 0
            for batch in tqdm(data_iter):
                read_id, signal = batch
                read_id = read_id[0]
                signal = signal[0]
                row_num = 0
                signal_segs = signal.shape[0]
                for i in range(signal_segs // 32 + 1):
                    if i != signal_segs // 32:
                        signal_batch = signal[i * 32:(i + 1) * 32]
                    elif signal_segs % 32 != 0:
                        signal_batch = signal[i * 32:]
                    else:
                        continue
                    if argv.half:
                        signal_batch = torch.HalfTensor(signal_batch).to(argv.device)
                    else:
                        signal_batch = torch.FloatTensor(signal_batch).to(argv.device)
                    signal_lengths = signal_batch.squeeze(2).ne(Constants.SIG_PAD).sum(1)
                    output, output_lengths = model(signal_batch, signal_lengths)
                    log_probs = output.log_softmax(2)
                    row_num += log_probs.shape[0]
                    log_probs_list.append(log_probs.cpu().detach())
                    output_lengths_list.append(output_lengths.cpu().detach())
                read_id_list.append(read_id)
                row_num_list.append(row_num)
                # encoded_num += 1
                # print('\r encoded_num={}'.format(encoded_num),end="")
                if len(read_id_list) == 50:
                    qdecoder.put((read_id_list, row_num_list, log_probs_list, output_lengths_list))
                    read_id_list = []
                    row_num_list = []
                    log_probs_list = []
                    output_lengths_list = []
            if len(read_id_list) > 0:
                qdecoder.put((read_id_list, row_num_list, log_probs_list, output_lengths_list))
    finally:
        qdecoder.put(None)
        decoder_proc.join()
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
    end_time = datetime.datetime.now()
    print(
        f"End time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")

    # Execution time
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.2f} sekund")
    
    # Save execution stats to CSV
    save_execution_stats_to_csv(execution_stats_file, [{'file_size': records_size_mb, 'execution_time': execution_time, 'batch_size': argv.batch_size}])

    # Save collected metrics to CSV
    save_metrics_to_csv(metric_file, system_metrics)

if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    main()
