#!/bin/bash
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./Sim200/data_sim0_200a.json -d A -c red -n sim0&
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./Sim200/data_sim0_200a.json -d B -c green -n sim1&
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./Sim200/data_sim0_200a.json -d C -c blue -n sim2&
python3.5 plot_sensors.py -f ./Sim200/sensor_200_A.data#./Sim200/sensor_200_B.data#./Sim200/sensor_200_C.data -t 1
