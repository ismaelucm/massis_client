#!/bin/bash
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./Sim400/data_sim1_400a.json -d A -c red -n sim0&
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./Sim400/data_sim1_400a.json -d B -c green -n sim1&
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./Sim400/data_sim1_400a.json -d C -c blue -n sim2&
python3.5 plot_sensors.py -f ./Sim400/sensor_400_A.data#./Sim400/sensor_400_B.data#./Sim400/sensor_400_C.data -t 1
