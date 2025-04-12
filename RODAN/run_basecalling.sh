#!/bin/bash
INPUT_PATH=$1
BATCH_SIZE=$2

echo "Input Path: $INPUT_PATH"
echo "Batch Size: $BATCH_SIZE"

python3 basecall.py "$INPUT_PATH" > /output_sample/output -b "$BATCH_SIZE"