#!/bin/bash
python3.5 plot_sensors.py -t 1 -p 8085 -c 3&
sleep 1s
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./Sim200/sim200.json -d A -c red -n sim0 -i 127.0.0.1 -p 8085&
sleep 1s
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./Sim200/sim200.json -d B -c green -n sim1 -i 127.0.0.1 -p 8086&
sleep 1s
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./Sim200/sim200.json -d C -c blue -n sim2 -i 127.0.0.1 -p 8087&

