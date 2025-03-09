#!/bin/bash
INPUT_PATH=$1
SIGNAL_WINDOW_LENGTH=$2
BATCH_SIZE=$3

echo "Input Path: $INPUT_PATH"
echo "Signal Window Length: $SIGNAL_WINDOW_LENGTH"
echo "Batch Size: $BATCH_SIZE"

bash run_caller.sh ./model.chkpt "$INPUT_PATH" "$SIGNAL_WINDOW_LENGTH" /output_sample/ "$BATCH_SIZE"
