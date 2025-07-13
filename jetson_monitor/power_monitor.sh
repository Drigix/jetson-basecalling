#!/bin/bash

PID_FILE="/tmp/power_monitor.pid"

start_monitor() {
    echo "Start monitor (log power_log.log)..."
    > power_log.log
    nohup bash -c '
    while true; do
        p0=$(sudo cat /sys/bus/i2c/drivers/ina3221x/6-0040/iio:device0/in_power0_input 2>/dev/null || echo "0")
        p1=$(sudo cat /sys/bus/i2c/drivers/ina3221x/6-0040/iio:device0/in_power1_input 2>/dev/null || echo "0")
        p2=$(sudo cat /sys/bus/i2c/drivers/ina3221x/6-0040/iio:device0/in_power2_input 2>/dev/null || echo "0")
        total=$(echo "scale=6; ($p0 + $p1 + $p2) / 1000000" | bc)
        echo "$total" >> power_log.log
        sleep 1
    done
    ' > /dev/null 2>&1 &
    
    echo $! > "$PID_FILE"
    echo "Monitor working (PID: $(cat "$PID_FILE")). Saving data to power_log.log"
}

stop_monitor() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null
        rm "$PID_FILE"
        echo "Stop monitoring (PID: $PID)."
    else
        echo "Monitoring don't working."
    fi
}

case "$1" in
    start)
        start_monitor
        ;;
    stop)
        stop_monitor
        ;;
    *)
        echo "Use: $0 {start|stop}"
        exit 1
        ;;
esac