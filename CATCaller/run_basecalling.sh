#!/bin/bash
INPUT_PATH=$1
BATCH_SIZE=$2

echo "Input Path: $INPUT_PATH"
echo "Batch Size: $BATCH_SIZE"

bash ./test/run_caller.sh ./model/model.2048.chkpt "$INPUT_PATH" "$BATCH_SIZE" /output_sample/