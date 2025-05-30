#!/bin/bash
INPUT_PATH=$1
BATCH_SIZE=$2
JETSON_MODE=$3

echo "Input Path: $INPUT_PATH"
echo "Batch Size: $BATCH_SIZE"
echo "Jetson mode: $JETSON_MODE"

python3 /jetson-basecalling/Chiron/chiron/entry.py call -i "$INPUT_PATH" -o /output_sample/ -m /jetson-basecalling/Chiron/chiron/model/DNA_default --preset dna-pre -b "$BATCH_SIZE" --jetson_mode "$JETSON_MODE"