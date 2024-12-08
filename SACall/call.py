#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Filename: call.py
# @Date    : 05/07/2019
# @Author  : Neng Huang
# @Email   : csuhuangneng@gmail.com


import argparse
from generate_dataset.trim_raw import trim_and_segment_raw
from statsmodels import robust
import shutil
import os
import copy
import numpy as np
from ctc.ctc_encoder import Encoder
import torch
import torch.nn as nn
import torch.utils.data as Data
import generate_dataset.constants as Constants
from ctc.ctc_decoder import BeamCTCDecoder, GreedyDecoder
from tqdm import tqdm
from multiprocessing import Process, Manager
import time
import psutil
from jtop import jtop
import csv
from datetime import datetime
import threading

read_id_list, log_probs_list, output_lengths_list, row_num_list = [], [], [], []
encode_mutex = True
decode_mutex = True


class Model(nn.Module):
    def __init__(self, d_model, d_ff, n_head, n_layers, dropout, label_vocab_size):
        super(Model, self).__init__()
        self.encoder = Encoder(d_model=d_model,
                               d_ff=d_ff,
                               n_head=n_head,
                               num_encoder_layers=n_layers,
                               dropout=dropout)
        self.final_proj = nn.Linear(d_model, label_vocab_size)

    def forward(self, signal, signal_lengths):
        """
                :param signal: a tensor shape of [batch, length, 1]
                :param signal_lengths:  a tensor shape of [batch,]
                :return:
                """
        enc_output, enc_output_lengths = self.encoder(
            signal, signal_lengths)  # (N,L,C), [32, 256, 256]
        out = self.final_proj(enc_output)  # (N,L,C), [32, 256, 6]
        return out, enc_output_lengths


class Call(nn.Module):
    def __init__(self, opt):
        super(Call, self).__init__()
        checkpoint = torch.load(opt.model)
        model_opt = checkpoint['settings']

        self.model = Model(d_model=model_opt.d_model,
                           d_ff=model_opt.d_ff,
                           n_head=model_opt.n_head,
                           n_layers=model_opt.n_layers,
                           dropout=model_opt.dropout,
                           label_vocab_size=model_opt.label_vocab_size)
        self.model.load_state_dict(checkpoint['model'])
        print('[Info] Trained model state loaded.')

    def forward(self, signal, signal_lengths):
        return self.model(signal, signal_lengths)


class CallDataset(Data.Dataset):
    def __init__(self, records_dir):
        self.records_dir = records_dir
        self.filenames = os.listdir(records_dir)
        self.count = len(self.filenames)

    def __len__(self):
        return self.count

    def __getitem__(self, idx):
        fname = self.filenames[idx]
        signal = np.load(self.records_dir + '/' + fname)
        read_id = os.path.splitext(fname)[0]
        return read_id, signal


def encode(model, opt):
    global read_id_list, log_probs_list, output_lengths_list, row_num_list
    manager = Manager()
    # read_id_list = manager.list()
    # log_probs_list = manager.list()
    # output_lengths_list = manager.list()
    # row_num_list = manager.list()
    encode_mutex = manager.Value('i', 1)
    decode_mutex = manager.Value('i', 1)
    write_mutex = manager.Value('i', 1)

    model.eval()
    call_dataset = CallDataset(opt.records_dir)
    data_iter = Data.DataLoader(
        dataset=call_dataset, batch_size=1, num_workers=0)
    if not os.path.exists(opt.output):
        os.makedirs(opt.output)
    else:
        shutil.rmtree(opt.output)
        os.makedirs(opt.output)
    outpath = os.path.join(opt.output, 'call.fasta')
    encoded_read_num = 0
    for batch in tqdm(data_iter):
        read_id, signal = batch
        read_id = read_id[0]
        signal = signal[0]
        read_id_list.append(read_id)
        signal_segs = signal.shape[0]
        row_num = 0
        encoded_read_num += 1
        while encode_mutex.value != 1:
            time.sleep(0.2)
        for i in range(signal_segs // 10 + 1):
            if i != signal_segs // 10:
                signal_batch = signal[i * 10:(i + 1) * 10]
            elif signal_segs % 10 != 0:
                signal_batch = signal[i * 10:]
            else:
                continue
            signal_batch = torch.FloatTensor(
                signal_batch).to(opt.device)
            signal_lengths = signal_batch.squeeze(
                2).ne(Constants.SIG_PAD).sum(1)
            output, output_lengths = model(
                signal_batch, signal_lengths)

            log_probs = output.log_softmax(2)
            row_num += signal_batch.size(0)
            log_probs_list.append(log_probs.cpu().detach())
            output_lengths_list.append(output_lengths.cpu().detach())
        row_num_list.append(row_num)
        if encoded_read_num == 100:
            encode_mutex.value = 0
            p = Process(target=decode_process, args=(
                outpath, encode_mutex, decode_mutex, write_mutex))
            p.start()
            while encode_mutex.value != 1:
                time.sleep(0.2)
            read_id_list[:] = []
            log_probs_list[:] = []
            output_lengths_list[:] = []
            row_num_list[:] = []
            encoded_read_num = 0
    if encoded_read_num > 0:
        encode_mutex.value = 0
        while decode_mutex.value != 1:
            time.sleep(0.2)
        p = Process(target=decode_process, args=(
            outpath, encode_mutex, decode_mutex, write_mutex))
        p.start()
        p.join()


def decode_process(outpath, encode_mutex, decode_mutex, write_mutex):
    global read_id_list, log_probs_list, output_lengths_list, row_num_list
    while decode_mutex.value != 1:
        time.sleep(0.2)
    decode_mutex.value = 0
    probs = torch.cat(log_probs_list)
    lengths = torch.cat(output_lengths_list)
    decode_read_id_list = read_id_list
    decode_row_num_list = row_num_list
    encode_mutex.value = 1
    decoder = BeamCTCDecoder('-ATCG ', blank_index=0, alpha=0.0, lm_path=None, beta=0.0, cutoff_top_n=6,
                             cutoff_prob=1.0, beam_width=3, num_processes=8)
    decoded_output, offsets = decoder.decode(probs, lengths)
    idx = 0
    while write_mutex.value != 1:
        time.sleep(0.2)
    fw = open(outpath, 'a')
    write_mutex.value = 0
    for x in range(len(decode_row_num_list)):
        row_num = decode_row_num_list[x]
        read_id = decode_read_id_list[x]
        transcript = [v[0] for v in decoded_output[idx:idx + row_num]]
        idx = idx + row_num
        transcript = ''.join(transcript)
        transcript = transcript.replace(' ', '')
        if len(transcript) > 0:
            fw.write('>' + str(read_id) + '\n')
            fw.write(transcript + '\n')
    fw.close()
    write_mutex.value = 1
    decode_mutex.value = 1

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


def save_metrics_to_csv(filepath, metrics):
    file_exists = os.path.isfile(filepath)
    with open(filepath, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'file_size', 'time', 'ram', 'gpu', 'cpu1', 'cpu2', 'cpu3', 'cpu4',
            'temperature_cpu', 'temperature_gpu', 'power_avg'
        ])
        if not file_exists:
            writer.writeheader()
        for metric in metrics:
            writer.writerow(metric)

def monitor_metrics(stop_event, start_time, file_size, metrics_list, filepath, jetson):
    """Monitor system metrics every ... seconds and save to the list."""
    while not stop_event.is_set():
        stats = jetson.stats
        metrics = {
            'file_size': file_size,
            'time': time.time() - start_time,
            'ram': psutil.virtual_memory().used / (1024 ** 2),
            'gpu': stats['GPU1'],
            'cpu1': stats['CPU1'],
            'cpu2': stats['CPU2'],
            'cpu3': stats['CPU3'],
            'cpu4': stats['CPU4'],
            'temperature_cpu': stats['Temp CPU'],
            'temperature_gpu': stats['Temp GPU'],
            'power_avg': stats['power avg'],
        }
        metrics_list.append(metrics)
        time.sleep(5)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-model', required=True)
    parser.add_argument('-records_dir', required=True)
    parser.add_argument('-output', required=True)
    parser.add_argument('-no_cuda', action='store_true')
    argv = parser.parse_args()

    # Start time
    start_time = time.time()
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    try:
        records_size_mb = get_size(argv.records_dir)
        print(f"Sample data size: {records_size_mb:.2f} MB")
    except ValueError as e:
        print(e)
        return

    if not os.path.exists(argv.output):
        os.makedirs(argv.output)
    if os.path.exists(os.path.join(argv.output, 'call.fasta')):
        os.remove(os.path.join(argv.output, 'call.fasta'))
    argv.cuda = not argv.no_cuda
    device = torch.device('cuda' if argv.cuda else 'cpu')
    argv.device = device

    metric_file = os.path.join('./', 'jetson_metrics.csv')

    # Monitor RAM usage
    ram_usage_before = psutil.virtual_memory().used / (1024 ** 2) 

    # Monitor GPU and system metrics
    with jtop() as jetson:
        system_metrics = []
        stop_event = threading.Event()

        monitoring_thread = threading.Thread(target=monitor_metrics, args=(stop_event, start_time, records_size_mb, system_metrics, metric_file, jetson))
        monitoring_thread.start()
        
        # Start processing
        try:
            call_model = Call(argv).to(device)
            encode(call_model, argv)
        finally:
            # Stop monitoring
            stop_event.set()
            monitoring_thread.join()

        print("Collect Jetson system metrics...")
        
        # Monitor RAM and GPU usage after
        #ram_usage_after = psutil.virtual_memory().used / (1024 ** 2)
        #ram_usage = ram_usage_after - ram_usage_before

        # Resource usage summary
        #print(f"RAM usage before: {ram_usage_before:.2f} MB, after: {ram_usage_after:.2f} MB")

        # End time
        end_time = time.time()
        print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")

        # Execution time
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time:.2f} sekund")
            
        # stats = jetson.stats
        # system_metrics.append({
        #     'file_size': records_size_mb,
        #     'time': execution_time,
        #     'ram': ram_usage,
        #     'gpu': stats['GPU1'],
        #     'cpu1': stats['CPU1'],
        #     'cpu2': stats['CPU2'],
        #     'cpu3': stats['CPU3'],
        #     'cpu4': stats['CPU4'],
        #     'temperature_cpu': stats['Temp CPU'],
        #     'temperature_gpu': stats['Temp GPU'],
        #     'power_avg': stats['power avg'],
        # })

        print(f"Metrics length: {len(system_metrics)}")
        # Save collected metrics to CSV
        save_metrics_to_csv(metric_file, system_metrics)

    # Save or display system metrics
 #   for metric in system_metrics:
 #       print(metric)  # Replace with saving to a file if needed


if __name__ == "__main__":
    main()
