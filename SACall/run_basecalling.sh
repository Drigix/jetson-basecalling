#!/bin/bash
INPUT_PATH=$1
BATCH_SIZE=$2

echo "Input Path: $INPUT_PATH"
echo "Batch Size: $BATCH_SIZE"

bash run_caller.sh ./model.chkpt "$INPUT_PATH" "$BATCH_SIZE" /output_sample/

bash /jetson-basecalling/metrics/db/call_db.py SACALL_STATS /jetson-basecalling/SACall/execution_statistics.csv /jetson-basecalling/SACall/jetson_metrics.csv