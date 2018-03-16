#!/bin/bash

function message() {
        echo "Press enter key to end."
}

trap message SIGINT

python3.5 plot_sensors.py -t 1 -p 8085 -c 3&
last_pid=$!
sleep 1s
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f $1 -d $2 -c red -n sim0 -i 127.0.0.1 -p 8085&
sim0_pid=$!
sleep 1s
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f $1 -d $3 -c green -n sim1 -i 127.0.0.1 -p 8086&
sim1_pid=$!
sleep 1s
python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f $1 -d $4 -c blue -n sim2 -i 127.0.0.1 -p 8087&
sim2_pid=$!

read -p "Press any key to finish... " samplevar
kill -KILL $last_pid $sim0_pid $sim1_pid $sim2_pid

