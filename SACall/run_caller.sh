#!/bin/bash


model_path=$1
fast5_dir=$2
signal_window_length=$3
basecalled_filename=$4
batch_size=$5
jetson_mode=$6
tmp_records_dir="tmp_data_dir"

# data preprocessing
python3 generate_dataset/inference_data.py -fast5 ${fast5_dir} -records_dir ${tmp_records_dir} -raw_len ${signal_window_length}

# caller
python3 call.py -model ${model_path} -records_dir ${tmp_records_dir} -output ${basecalled_filename} -batch_size ${batch_size} -jetson_mode ${jetson_mode}

# delete tmp records
rm -rf ${tmp_records_dir}





