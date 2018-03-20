Available simulations are:

- evacuation.json. Evacuation of 5 classes of students
- entranceclass.json. Daily routine with 210 students.
- entrance_two_waves.json. Daily routine with 420 students entering in two waves of 210 students.


Presence sensor configurations are labeled from A to N. 

To launch a simple client for reading data from ./Sim200/evacuation.json with a sensor layout A and printing out in the standard output the effectiveness of the sensors

	python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./sims/evacuation.json -d A  -n sim0

To launch the same simulation while storing results in file "test.txt"

	python3.5 client_p_v1.0.6_read_from_file.py -s scene.json -f ./sims/evacuation.json -d A  -n sim0 -o test.txt

Into another console, type the following to track the changes. The first number is the sim time, the second the accumulated error, the third the average precission (per iteration)

	tail -f test.txt

The file is made of lines where

	sim time, average error, average precision

Average precision is the average of times the sensor was right. It is right if it identifies presence when there is someone within the square that represents the corridor. The number of correct guessings are averaged by the number of iterations.

Average error accounts the average squared error the sensors make. This time, the number of agents within the sensor perimeter against the number of agents within the ideal square are accounted.  The square of the difference is averaged by the number of iterations

To compare different sensor deployment simulations, run the following

	bash comparesims.sh sims/sim200.json C O P

The syntax is

	bash comparesims.sh SimulationFileInJSON LABEL_LAYOUT_1 LABEL_LAYOUT_2 LABEL_LAYOUT_3

There are layouts of sensors for a corridor from A to P. There is a chart showing the compared precision of each file. 
