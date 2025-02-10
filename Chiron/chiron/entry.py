# Copyright 2017 The Chiron Authors. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Created on Mon Aug 14 18:38:18 2017
import argparse
import sys
import logging
from os import path
import chiron
from chiron import chiron_eval
from chiron import chiron_rcnn_train
from chiron.utils import raw
from chiron.utils.extract_sig_ref import extract
import time
import psutil
import os
import threading
import csv


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
            'file_size', 'time', 'ram', 'cpu'
        ])
        if not file_exists:
            writer.writeheader()
        else:
            file.write("#\n")
        for metric in metrics:
            writer.writerow(metric)


def monitor_metrics(stop_event, start_time, file_size, metrics_list):
    """Monitor system metrics every ... seconds and save to the list."""
    while not stop_event.is_set():
        metrics = {
            'file_size': file_size,
            'time': time.time() - start_time,
            'ram': psutil.virtual_memory().used / (1024 ** 2),
            # 'gpu': stats['GPU1'],
            'cpu': psutil.cpu_percent(interval=1),
            # 'cpu2': stats['CPU2'],
            # 'cpu3': stats['CPU3'],
            # 'cpu4': stats['CPU4'],
            # 'temperature_cpu': stats['Temp CPU'],
            # 'temperature_gpu': stats['Temp GPU'],
            # 'power_avg': stats['power avg'],
        }
        metrics_list.append(metrics)
        time.sleep(5)


def evaluation(args):
    try:
        records_size_mb = get_size(args.input)
        print(f"Sample data size: {records_size_mb:.2f} MB")
    except ValueError as e:
        print(e)

    metric_file = os.path.join('./', 'jetson_metrics.csv')

    # Monitor RAM usage
    ram_usage_before = psutil.virtual_memory().used / (1024 ** 2)

    if args.preset is None:
        default_p = {'start': 0, 'batch_size': 400,
                     'segment_len': 500, 'jump': 490, 'threads': 0, 'beam': 30}
    elif args.preset == 'dna-pre':
        default_p = {'start': 0, 'batch_size': 400,
                     'segment_len': 400, 'jump': 390, 'threads': 0, 'beam': 30}
        if args.mode == 'rna':
            raise ValueError(
                'Try to use the DNA preset parameter setting in RNA mode.')
    elif args.preset == 'rna-pre':
        default_p = {'start': 0, 'batch_size': 300,
                     'segment_len': 2000, 'jump': 1900, 'threads': 0, 'beam': 30}
        if args.mode == 'dna':
            raise ValueError(
                'Attempt to use the RNA preset parameter setting in DNA mode, enable RNA basecalling by --mode rna')
    else:
        raise ValueError('Unknown presetting %s undifiend' % (args.preset))

    system_metrics = []
    stop_event = threading.Event()

    # Start time
    start_time = time.time()
    print(
        f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    monitoring_thread = threading.Thread(target=monitor_metrics, args=(
        stop_event, start_time, records_size_mb, system_metrics))
    monitoring_thread.start()

    try:
        args = set_paras(args, default_p)
        FLAGS = args
        FLAGS.input_dir = FLAGS.input
        FLAGS.output_dir = FLAGS.output
        FLAGS.unit = False
        FLAGS.recursive = True
        FLAGS.polya = None
        FLAGS.idname = False
        FLAGS.delimiter = "\n"
        if args.mode == 'rna':
            args.reverse_fast5 = True
        else:
            args.reverse_fast5 = False
        extract(FLAGS)
        FLAGS.input = FLAGS.output + '/raw/'
        chiron_eval.run(args)
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

    # Save collected metrics to CSV
    save_metrics_to_csv(metric_file, system_metrics)


def export(args):
    raw.run(args)


def set_paras(args, p):
    args.start = p['start'] if args.start is None else args.start
    args.batch_size = p['batch_size'] if args.batch_size is None else args.batch_size
    args.segment_len = p['segment_len'] if args.segment_len is None else args.segment_len
    args.jump = p['jump'] if args.jump is None else args.jump
    args.threads = p['threads'] if args.threads is None else args.threads
    args.beam = p['beam'] if args.beam is None else args.beam
    return args


def main(arguments=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        prog='chiron', description='A deep neural network basecaller.')
    parser.add_argument('-v', '--version', action='version',
                        version='Chiron version '+chiron.__version__, help="Print out the version.")
    subparsers = parser.add_subparsers(
        title='sub command', help='sub command help')
    model_default_path = path.join(path.abspath(
        path.dirname(__file__)), 'model', 'DNA_default')

    # parser for 'call' command
    parser_call = subparsers.add_parser(
        'call', description='Perform basecalling', help='Perform basecalling.')
    parser_call.add_argument('-i', '--input', required=True,
                             help="File path or Folder path to the fast5 file.")
    parser_call.add_argument(
        '-o', '--output', required=True, help="Output folder path")
    parser_call.add_argument('-m', '--model', type=str,
                             default=model_default_path, help="model folder path")
    parser_call.add_argument('-s', '--start', type=int,
                             default=None, help="Start index of the signal file.")
    parser_call.add_argument('-b', '--batch_size', type=int, default=None,
                             help="Batch size for run, bigger batch_size will increase the processing speed but require larger RAM load")
    parser_call.add_argument('-l', '--segment_len', type=int,
                             default=None, help="Segment length to be divided into.")
    parser_call.add_argument('-j', '--jump', type=int,
                             default=None, help="Step size for segment")
    parser_call.add_argument('-t', '--threads', type=int, default=None,
                             help="Threads number, default is 0, which use all the available threads.")
    parser_call.add_argument(
        '-e', '--extension', default='fastq', help="Output file type.")
    parser_call.add_argument('--beam', type=int, default=None,
                             help="Beam width used in beam search decoder, default is 50, set to 0 to use a greedy decoder. Large beam width give better decoding result but require longer decoding time.")
    parser_call.add_argument('--concise', action='store_true',
                             help="Concisely output the result, the meta and segments files will not be output.")
    parser_call.add_argument('--mode', default='dna',
                             help="Output mode, can be chosen from dna or rna.")
    parser_call.add_argument('--test_number',
                             default=None,
                             type=int,
                             help="Extract test_number reads, default is None, extract all reads.")
    parser_call.add_argument('-p', '--preset', default=None,
                             help="Preset evaluation parameters. Can be one of the following: dna-pre, rna-pre")
    parser_call.set_defaults(func=evaluation)

    # parser for 'extract' command
    parser_export = subparsers.add_parser('export', description='Export signal and label from the fast5 file.',
                                          help='Extract signal and label in the fast5 file.')
    parser_export.add_argument(
        '-i', '--input', required=True, help='Input folder contain fast5 files.')
    parser_export.add_argument(
        '-o', '--output', required=True, help='Output folder.')
    parser_export.add_argument(
        '-f', '--tffile', default="train.tfrecords", help="tfrecord file")
    parser_export.add_argument('--basecall_group', default='Basecall_1D_000',
                               help='Basecall group Nanoraw resquiggle into. Default is Basecall_1D_000')
    parser_export.add_argument('--basecall_subgroup', default='BaseCalled_template',
                               help='Basecall subgroup Nanoraw resquiggle into. Default is BaseCalled_template')
    parser_export.set_defaults(func=export)

    # parser for 'train' command
    parser_train = subparsers.add_parser(
        'train', description='Model training', help='Train a model.')
    parser_train.add_argument('-i', '--data_dir', required=True,
                              help="Directory that store the tfrecord files.")
    parser_train.add_argument('-o', '--log_dir', required=True,
                              help="log directory that store the training model.")
    parser_train.add_argument('-m', '--model_name', required=True,
                              help='model_name')
    parser_train.add_argument('-v', '--validation', default=None,
                              help="validation tfrecord file, default is None, which conduct no validation")
    parser_train.add_argument('-f', '--tfrecord', default="train.tfrecords",
                              help='tfrecord file')
    parser_train.add_argument(
        '--train_cache', default=None, help="Cache file for training dataset.")
    parser_train.add_argument(
        '--valid_cache', default=None, help="Cache file for validation dataset.")
    parser_train.add_argument('-s', '--sequence_len', type=int, default=400,
                              help='the length of sequence')
    parser_train.add_argument('-b', '--batch_size', type=int, default=300,
                              help='Batch size')
    parser_train.add_argument('-t', '--step_rate', type=float, default=4e-3,
                              help='Step rate')
    parser_train.add_argument('-x', '--max_steps', type=int, default=10000,
                              help='Maximum step')
    parser_train.add_argument('-n', '--segments_num', type=int, default=None,
                              help='Maximum number of segments read into the training queue, default(None) read all segments.')
    parser_train.add_argument('--configure', default=None,
                              help="Model structure configure json file.")
    parser_train.add_argument(
        '-k', '--k_mer', default=1, help='Output k-mer size')
    parser_train.add_argument('--resample_after_epoch',
                              type=int,
                              default=0,
                              help='Resample the reads data every n epoches, with an increasing initial offset.')
    parser_train.add_argument('--threads',
                              type=int,
                              default=0,
                              help='The threads that available, if 0 use all threads that can be found.')
    parser_train.add_argument('--offset_increment',
                              type=int,
                              default=3,
                              help='The increament of initial offset if the resample_after_epoch has been set.')
    parser_train.add_argument('--retrain', dest='retrain', action='store_true',
                              help='Set retrain to true')
    parser_train.add_argument('--read_cache', dest='read_cache', action='store_true',
                              help="Read from cached hdf5 file.")
    parser_train.set_defaults(func=chiron_rcnn_train.run)

    args = parser.parse_args(arguments)
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # print(sys.argv[1:])
    main()
