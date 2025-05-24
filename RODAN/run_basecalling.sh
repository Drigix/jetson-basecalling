#!/bin/bash
INPUT_PATH=$1
BATCH_SIZE=$2
JETSON_MODE=$4

echo "Input Path: $INPUT_PATH"
echo "Batch Size: $BATCH_SIZE"
echo "Jetson mode: $JETSON_MODE"

python3 basecall.py "$INPUT_PATH" > /output_sample/output -b "$BATCH_SIZE" "$JETSON_MODE"