#!/bin/bash
INPUT_PATH=$1
SIGNAL_WINDOW_LENGTH=$2
BATCH_SIZE=$3

echo "Input Path: $INPUT_PATH"
echo "Batch Size: $BATCH_SIZE"

bash run_caller.sh ./model.chkpt "$INPUT_PATH" "$SIGNAL_WINDOW_LENGTH" /output_sample/ "$BATCH_SIZE"

bash /jetson-basecalling/metrics/db/call_db.py SACALL_STATS /jetson-basecalling/SACall/execution_statistics.csv /jetson-basecalling/SACall/jetson_metrics.csv