#!/bin/bash
python3.5 plot_sensors.py -t 1 -p 8085 -c 3&
sleep 1s
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./SimEnter3Doors/SimEnter3Doors.json -d L -c red -n sim0 -i 127.0.0.1 -p 8085&
sleep 1s
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./SimEnter3Doors/SimEnter3Doors.json -d M -c green -n sim1 -i 127.0.0.1 -p 8086&
sleep 1s
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./SimEnter3Doors/SimEnter3Doors.json -d N -c blue -n sim2 -i 127.0.0.1 -p 8087&
