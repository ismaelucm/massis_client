import time
import json
from tkinter import *
import urllib3
import time, io
import argparse
import textwrap
import requests
from requests import get

NUM_POOLS = 100
QUERY = "components=position&components=human"

class Download:
    def __init__(self,simId, host, port, file, out, time, deltatime):
        self.simId = simId
        self.host = host
        self.port = port
        self.file = file
        self.time = time
        self.deltatime = deltatime
        self.out = out;
        self.firstTime = -1
        self.currentTime = 0


    def DownloadSim(self):
        outputFile = open(self.file, 'w+')
        outputFile.close()
        print("Simulation time "+str(self.currentTime) + " de "+str(self.time))
        self.getSceneInfo()
        self.streamFast()
        while self.currentTime < self.time:
        	self.streamFast()


    def getSceneInfo(self):
    	url = 'http://'+self.host+':'+str(self.port)+'/api/simulations/'+str(self.simId)+'/environment/rooms/'
    	print("Command "+url)
    	jsonScene = get(url, stream=False).text
    	with io.FileIO(self.out, "w+") as file:
    		file.write(jsonScene.encode())
    		file.close()

    	return  json.loads(jsonScene)

    def streamFast(self):
        url = 'http://'+self.host+':'+str(self.port)+'/api/simulations/'+str(self.simId)+'/human-agent/allHumanInfo/'
        print("command "+url);
        http = requests.get(url)
        if http.status_code == 200:
        	jsonResponse = http.json()
        	newTime = jsonResponse['result']['simTime']
        	
        	arrayLeft = ""

        	if self.firstTime == -1:
        		self.firstTime = newTime
        		arrayLeft = "["

        	newAccumulatedTime = newTime - self.firstTime
        	currentRequestTime = newAccumulatedTime - self.currentTime

        	self.currentTime = newAccumulatedTime

        	print('Time '+str(self.currentTime)+' status '+str(http.status_code))

        	arrayRight = ","
        	if self.currentTime >= self.time:
        		arrayRight = "]"

        	if currentRequestTime < self.deltatime:
        		timeToSleep = (self.deltatime-currentRequestTime)/1000.0
        		print('Time to sleep '+str(timeToSleep))
        		time.sleep(timeToSleep)
        	with io.open(self.file, "a") as file:
        		file.write(arrayLeft+http.text+arrayRight)
        #with io.FileIO(self.file, "a") as file:
        #print(http.status_code)
        #print(http.json())




#Parsing arguments

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        MASSIS-SIM Creating simulation files
        '''),
    epilog='''ColosAAL 2017'''
)

parser.add_argument('-s', '--simid', help='ID for Simulation (Default: 0)', required=False)
parser.add_argument('-c', '--host', help='host server for Simulation (Default: 127.0.0.1)', required=False)
parser.add_argument('-p', '--port', help='port for Simulation (Default 8080)', required=False)
parser.add_argument('-a', '--api', help='Api for Simulation (Default "/massis")', required=False)
parser.add_argument('-f', '--file', help='Simulation file', required=True)
parser.add_argument('-o', '--out', help='Scene file', required=True)
parser.add_argument('-t', '--time', help='Simulation time', required=False)
parser.add_argument('-d', '--deltatime', help='Request time interval (Default 1000)', required=False)
args = parser.parse_args()

#end parsing arguments



#==============================================================================
#--------------------------------EXAMPLE CODE----------------------------------
#==============================================================================
#==============================================================================


__simId = 0
__host = 'localhost'
__port = 80
__file =  ""
__time = 0
__deltatime = 1000


if args.simid is not None:
    __simId = int(args.simid)

if args.host is not None:
    __host = str(args.host)

if args.port is not None:
    __port = int(args.port)


if args.api is not None:
    api = str(args.api)


if args.file is not None:
    __file = str(args.file)

if args.out is not None:
    __out = str(args.out)

if args.time is not None:
    __time = float(args.time)

if args.deltatime is not None:
	__deltatime = float(args.deltatime)

download = Download(simId=__simId, host=__host, port=__port, file = __file, out = __out, time = __time, deltatime=__deltatime)
download.DownloadSim()
