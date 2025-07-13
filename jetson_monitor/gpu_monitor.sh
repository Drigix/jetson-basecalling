#!/bin/bash

LOG_FILE="gpu_log.log"

tegrastats --interval 1000 | while IFS= read -r line
do
    if [[ "$line" =~ GR3D_FREQ[[:space:]]+([0-9]+)% ]]; then
        echo "${BASH_REMATCH[1]}" >> "$LOG_FILE"
    fi
done