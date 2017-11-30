
import json
from tkinter import *
import urllib3
import time, io
import argparse
import textwrap
from requests import get

NUM_POOLS = 100
QUERY = "components=position&components=human"

class Download:
    def __init__(self,simId, host, port, file, scene, time):
        self.simId = simId
        self.host = host
        self.port = port
        self.file = file
        self.scene = scene
        self.time = time
        self.firstTime = -1
        self.currentTime = 0


    def DownloadSim(self):
        outputFile = open(self.file, 'w+')
        outputFile.close()
        print("Simulation time "+str(self.currentTime) + " de "+str(self.time))
        self.getSceneInfo()
        while self.currentTime < self.time:
            url = '/live/'+str(self.simId)+'/changes?'+QUERY
            self.streamFast(url)

    def getSceneInfo(self):
        url = 'http://'+self.host+':'+str(self.port)+api+'/info/scene/'+str(self.simId)
        print("Command "+url)
        jsonScene = get(url, stream=False).text;
        with io.FileIO(self.scene, "w+") as file:
            file.write(jsonScene.encode())
            file.close()
        return  json.loads(jsonScene)

    def streamFast(self, endpoint):
        if not(endpoint.startswith('/')):
            endpoint = '/'+endpoint
        http = urllib3.PoolManager(num_pools=NUM_POOLS)
        url = 'http://'+self.host+':'+str(self.port)+endpoint
        print(url)

        for line in http.request('GET', url, preload_content=False):
            with io.FileIO(self.file, "a") as file:
                if line.startswith(b'data: '):
                    file.write(line)
                    data = json.loads(line[len(b'data: '):].decode('utf-8'))
                    #print(data[0]['components'][0]['data'])

                    time = float(data[0]['timestamp'])
                    if self.firstTime < 0:
                        self.firstTime = time
                    self.currentTime = time - self.firstTime
                    print("Time: "+str(self.currentTime)+"/"+str(self.time) + " timestamp "+str(time))
                    if self.currentTime > self.time:
                        return




#Parsing arguments

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        MASSIS-SIM Creating simulation files
        '''),
    epilog='''ColosAAL 2017'''
)

parser.add_argument('-s', '--simid', help='ID for Simulation (Default: 3)', required=False)
parser.add_argument('-c', '--host', help='host server for Simulation (Default: 147.96.80.41)', required=False)
parser.add_argument('-p', '--port', help='port for Simulation (Default 8080)', required=False)
parser.add_argument('-a', '--api', help='Api for Simulation (Default "/massis")', required=False)
parser.add_argument('-e', '--scene', help='Scene file', required=True)
parser.add_argument('-f', '--file', help='Simulation file', required=True)
parser.add_argument('-t', '--time', help='Simulation time', required=False)
args = parser.parse_args()

#end parsing arguments



#==============================================================================
#--------------------------------EXAMPLE CODE----------------------------------
#==============================================================================
#==============================================================================


__simId = 0
__host = 'localhost'
__port = 80
__scene = ""
__file =  ""
__time = 0


if args.simid is not None:
    __simId = int(args.simid)

if args.host is not None:
    __host = str(args.host)

if args.port is not None:
    __port = int(args.port)


if args.api is not None:
    api = str(args.api)

if args.scene is not None:
    __scene = str(args.scene)

if args.file is not None:
    __file = str(args.file)

if args.time is not None:
    __time = float(args.time)

download = Download(simId=__simId, host=__host, port=__port, file = __file, scene = __scene, time = __time)
download.DownloadSim()
