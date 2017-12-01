
from requests import post
from requests import get
import json
from tkinter import *
from multiprocessing import Queue
import threading
import math
from time import sleep
import urllib3
import time, io
import argparse
import textwrap
import socket
from enum import Enum
import base64

from urllib.parse import urlencode # Python 2

#try:
#    from urllib.parse import urlparse
#except ImportError:
#     from urlparse import urlparse
class WriterType(Enum):
    FILE = 1
    SOCKET = 2

SIM_ID_COLORS = ["white","green","yellow","red"]
api = "/massis"
#==============================================================================
# Based on http://stackoverflow.com/a/22837522/3315914
# a subclass of Canvas for dealing with resizing of windows
class ResizingCanvas(Canvas):
    def __init__(self,parent,**kwargs):
        Canvas.__init__(self,parent,**kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self,event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas 
        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.scale("all",0,0,wscale,hscale)

    def create_circle(self, x, y, r, **kwargs):
        return self.create_oval(x-r, y-r, x+r, y+r, **kwargs)

#==============================================================================


def add(a, b):
    return {'x': a['x']+b['x'],'y': a['y']+b['y'],'z': a['z']+b['z']}


def sub(a, b):
    return {'x': a['x']-b['x'],'y': a['y']-b['y'],'z': a['z']-b['z']}


def mult(a, multiplier):
    return {'x': a['x']*multiplier,'y': a['y']*multiplier,'z': a['z']*multiplier}


def lerp(start, end, percent):
    diff = sub(end,start)
    return add(start, mult(diff, percent))


class MassisClient:

    def __init__(self, file, scene, out, ip, port, simId, host, hostPort,api):
        self.file = file
        self.scene = scene
        self.out = out
        self.ip = ip
        self.simId = simId
        self.host = host
        self.hostPort = hostPort
        self.port = port
        self.api = api
        self.readFromServer = host != ""
        self.has_output = not ( self.out != None and self.out != "" and self.port > 0 and self.ip != None and self.ip != "")

        print("MassisClient.Outout configuration: file "+self.out+" port "+str(self.port) + " ip "+self.ip + " has output "+str(self.has_output))

        if self.has_output:
            if self.out != "":
                self.writer = Writer(WriterType.FILE,self.out,"",0)
            else:
                self.writer = Writer(WriterType.SOCKET,"",self.ip,self.port)

            self.writer.Open()
        # self.http = urllib3.HTTPConnectionPool('http://' + str(self.host) + ":" + str(self.port) + api, maxsize=20)
        #self.http = urllib3.PoolManager(num_pools=20)

    def fileFast(self):
        filePath = self.file;
        with open(filePath, "r") as file:
            for line in file:
                s_line = line
                if s_line.startswith("data: "):
                    s_line = line.replace("data: ","")
                yield json.loads(s_line)


    def getSceneInfo(self):
        url = 'http://'+self.host+':'+str(self.hostPort)+self.api+'/info/scene/'+str(self.simId)
        jsonScene = get(url, stream=False).text;
        return  json.loads(jsonScene)

    def streamFast(self, endpoint):
        if not(endpoint.startswith('/')):
            endpoint = '/'+endpoint
        http = urllib3.PoolManager(num_pools=20)
        url = 'http://'+self.host+':'+str(self.hostPort)+self.api+endpoint
        #creo la simulacion
        for line in http.request('GET', url, preload_content=False):
            if line.startswith(b'data: '):
                yield json.loads(line[len(b'data: '):].decode('utf-8'))

    def getSceneInfoWithFile(self):
        file = open(self.scene, "r")
        s_sceneSim = file.read();
        try:
            return json.loads(s_sceneSim)
        except ValueError:
            return None

    def queryChanges(self, components):

        if(self.readFromServer):
            url = '/live/'+str(self.simId)+'/changes?'+urlencode([("components", x) for x in components])
            return self.streamFast(url)
        else:
            return self.fileFast();

    def hasOutput(self):
        return self.has_output

    def write(self, data):
        self.writer.Write(data)

    def closeWriter(self):
        if self.has_output:
            self.writer.close()


class ComponentQuery:

    def __init__(self, client,components):
        self.components = components
        self.client = client
        self.running = True
        self._agentData = dict()
        self.queue = Queue()

    def start(self):
        self.t = threading.Thread(target=self.doQuery)
        #self.t.daemon=True
        self.t.start()

    def agentData(self):
        return dict(self._agentData)

    def updateAgent(self, data):
        #print(data)
        entityId = data['entityId']
        if data['changeType'] == 'REMOVED':
                del  self._agentData[entityId]
                return
        cmps = None
        if not (entityId in self._agentData):
            cmps = dict()
        else:
            cmps = self._agentData[entityId]
        for cmp in data['components']:
            cmps[cmp['type']] = cmp['data']
        cmps['timestamp'] = data['timestamp']
        self._agentData[entityId] = cmps

    def doQuery(self):
        lastUpdate=-1
        for dataList in self.client.queryChanges(self.components):
            if(self.running):
                for data in dataList:
                    #sleep(0.1)
                    while lastUpdate>0 and lastUpdate < data['timestamp']:
                        sleep(0.0001)
                        lastUpdate+=0.0001
                    lastUpdate=data['timestamp']
                    self.updateAgent(data)
            else:
                break

    def stop(self):
         self.running=False


class EnvironmentGUI:

    def __init__(self, client, color, colorSim, name, sensorPos=((37, 37))):
        self.colors=dict()
        self.client=client
        self.root = Tk()
        self.frame = Frame(self.root)
        self.mouseX=0
        self.mouseY=0
        self.colorSim = colorSim
        self.name = name
        self.lastTimestamp = 0
        self.currenTime = 0
        self.width=850
        self.height=400
        self.frame.pack(fill=BOTH, expand=YES)
        self.canvas = ResizingCanvas(self.frame,width=self.width, height=self.height, bg=SIM_ID_COLORS[color%len(SIM_ID_COLORS)], highlightthickness=0)
        self.canvas.pack(fill=BOTH, expand=YES)
        if client.readFromServer:
            self.sceneInfo=client.getSceneInfo()
        else:
            self.sceneInfo=client.getSceneInfoWithFile()
        #self.sceneInfo=client.getSceneInfo()
        (self.minX,self.minY,self.maxX,self.maxY)=self.findMinMax()
        self.listeners=list()
        self.simLabel = Label(self.frame, text=name, font=("Helvetica", 16))
        self.simLabel.place(x =self.width-100, y = self.height-45)
        self.coordLabel = Label(self.frame, text="()")
        self.timeLabel  = Label(self.frame, text="()")
        self.timeLabel.place(x =self.width-100, y = 0)
        self.coordLabel.place(x =10, y = 10)
        self.sensorPos = sensorPos
        self.ticks = 0
        self.acumulatedError = 0
        self.iterations = 0
        self.acumulatedPrecision = 0



    def scale(self):
        scaleX=self.canvas.width/(self.maxX-self.minX)
        scaleY=self.canvas.height/(self.maxY-self.minY)
        return min(scaleX,scaleY)*0.9

    def simulationToScreen(self,x,y,z):
        return ((x-self.minX)*self.scale(),y,(z-self.minY)*self.scale())

    def screenToSimulation(self,x,z):
        return (x/self.scale()+self.minX,z/self.scale()+self.minY)

    def findMinMax(self):
        minX=float('inf')
        maxX=float('-inf')
        minY=float('inf')
        maxY=float('-inf')
        if self.sceneInfo is not None:
            for wall in self.sceneInfo['walls']:
                points=wall['bottomPoints']
                for i,elem in enumerate(points):
                    point=elem
                    maxY=max(point['z'],maxY)
                    maxX=max(point['x'],maxX)
                    minX=min(point['x'],minX)
                    minY=min(point['z'],minY)
            return (minX,minY,maxX,maxY)

    def redrawWalls(self):
        if self.sceneInfo is not None:
            circle=self.canvas.create_circle(self.width-30,self.height-30, 15, fill=self.colorSim, outline="#DDD", width=0.8, tags=str(self.name))
            self.simLabel.configure(text=str(self.name))
            self.canvas.delete("wall")
            for wall in self.sceneInfo['walls']:
                points=wall['bottomPoints']
                for i,elem in enumerate(points):
                    c,n = elem,points[(i + 1) % len(points)]
                    (c_x,c_y,c_z)=self.simulationToScreen(c['x'],c['y'],c['z'])
                    (n_x,n_y,n_z)=self.simulationToScreen(n['x'],c['y'],n['z'])
                    line=self.canvas.create_line(c_x,c_z,n_x,n_z)
                    self.canvas.addtag_below("all", line)
                    self.canvas.addtag_below("wall",line)

    def redrawFurniture(self):
        if self.sceneInfo is not None:
            self.canvas.delete("furniture")
            for f in self.sceneInfo['furniture']:
                w=f['localScale']['x']
                d=f['localScale']['z']
                color="brown"
                if f['isDoorOrWindow']:
                    color="green"
                (x,y,z)= self.simulationToScreen(f['localTranslation']['x'], 0,f['localTranslation']['z'])
                poly=self.canvas.create_oval(x-d*self.scale(), z-d*self.scale(), x+d*self.scale(), z+d*self.scale(),fill=color)
                self.canvas.addtag_below("all", poly)
                self.canvas.addtag_below("furniture",poly)

    def setAgentColor(self,entityId,color):
        self.colors[entityId]=color

    def redrawSensor(self, sensorPos):
        self.canvas.delete("sensor")
        for pos in sensorPos:
            (x,y,z)= self.simulationToScreen(pos[0], 0, pos[1])
            radius = pos[2]
            d = 0.2
            sensor1 = self.canvas.create_oval(x-d * self.scale(), z-d * self.scale(), x+d * self.scale(), z+d * self.scale(),fill="red")
            sensor2 = self.canvas.create_oval(x-radius * self.scale(), z-radius * self.scale(), x+radius * self.scale(), z+radius * self.scale(), outline="red")
            self.canvas.addtag_below("all", sensor1)
            self.canvas.addtag_below("sensor",sensor1)
            self.canvas.addtag_below("all", sensor2)
            self.canvas.addtag_below("sensor",sensor2)

    def minRect(self,circleItems):
        minX=float('inf')
        maxX=float('-inf')
        minY=float('inf')
        maxY=float('-inf')
        for c in circleItems:
            minX=min(minX,c[0]-c[2])
            minY=min(minY,c[1]-c[2])
            maxX=max(maxX,c[0]+c[2])
            maxY=max(maxY,c[1]+c[2])
        return (minX,minY,maxX,maxY)

    def drawMinRect(self,sensorPos):
        self.canvas.delete("minRect")
        (minX,minY,maxX,maxY) = self.minRect(sensorPos)
        (x0,y0,z0)=self.simulationToScreen(minX, 0, minY)
        (x1,y1,z1)=self.simulationToScreen(maxX, 0, maxY)
        rect=self.canvas.create_rectangle(x0, z0, x1, z1,width=2,outline="orange")
        self.canvas.addtag_below("all", rect)
        self.canvas.addtag_below("minRect",rect)
        
    def redrawAgents(self):
        self.canvas.delete("agent")
        agentData = self.getAgents()
        currentTimeStamp=10000
        for entityId in agentData:
            currentTimeStamp = min(agentData[entityId]['timestamp'],currentTimeStamp)
            pos=agentData[entityId]['position']
            (x,y,z)=self.simulationToScreen(pos['x'],pos['y'],pos['z'])
            detectorPos=(40,20)
            color="blue"
            if entityId in self.colors:
                color=self.colors[entityId]
            radius=self.scale()*0.35
            circle=self.canvas.create_circle(x,z, radius, fill=color, outline="#DDD", width=0.8, tags=str(entityId))
            self.canvas.addtag_below("agent",circle)
            self.canvas.addtag_below("AGENT_" + str(entityId),circle)
            self.canvas.addtag_below("all",circle)
        self.timeLabel.configure(text = str(currentTimeStamp))
    
    def redrawCoordLabel(self):
        #self.coordLabel.place(x = self.mouseX, y = self.mouseY)
        (x_sim,z_sim)=self.screenToSimulation(self.mouseX, self.mouseY)
        self.coordLabel.configure(text="(x="+("%.2f" % x_sim)+",z="+("%.2f" % z_sim)+")")

    def redrawLoop(self):
        if self.ticks == 0 :
            self.redrawFurniture()
            self.redrawWalls()
            self.redrawSensor(self.sensorPos)
        self.redrawAgents()
        self.redrawCoordLabel()

        self.drawMinRect(self.sensorPos)
        self.root.after(50, self.redrawLoop)
        self.ticks = self.ticks + 1

    def execListeners(self):
        for l in self.listeners:
            l(self)
        self.root.after(1000, self.execListeners)

    def addTickListener(self,listener):
        self.listeners.append(listener)

    def removeTickListener(self,listener):
        self.listeners.remove(listener)

    def getAgents(self):
        return self.query.agentData()

    def mouseMotion(self,event):
        x, y = event.x, event.y
        self.mouseX=x
        self.mouseY=y


    def getMouseCoords(self):
        return (self.mouseX,self.mouseY)

    def getMouseCoordsInSimulation(self):
        return self.screenToSimulation(self.mouseX,self.mouseY)

    
    def run(self):
        self.query=ComponentQuery(self.client,["position","human"])
        self.query.start()
        self.root.after(10, self.redrawLoop)
        self.root.after(10, self.execListeners)
        self.root.bind('<Motion>', self.mouseMotion)
        self.root.mainloop()
        self.query.stop()

    def WriteOutput(self,time, average, averagePrecision):
        if self.client.hasOutput() :
            self.client.write(str(time) + " " + str(average) + " " + str(averagePrecision))
        else:
            print ("Time"+str(time)+"Average Error "+str(average) + " Precision " + str(averagePrecision))

    def closeWriter(self):
        self.client.closeWriter()


class WriterFile:
    def __init__(self,file):
        self.fileName = file

    def Open(self):
        self.file = open(self.fileName, 'w+')

    def Write(self,data):
        self.file.write(data+"\n")

    def Close(self):
        self.file.close()


class WriterSocket:
    def __init__(self,ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port

    def Open(self):
        self.socket.connect((self.ip, self.port))

    def Write(self,data):
        data = data + ";"
        binary = data.encode('utf-8')
        self.socket.send(binary)

    def Close(self):
        self.socket.close()


class Writer:
    def __init__(self, writerType, file, ip, port):
        self.writerType = writerType
        if self.writerType == WriterType.FILE:
            self.writer = WriterFile(file)
        else:
            self.writer = WriterSocket(ip, port)

    def Open(self):
        self.writer.Open()

    def Write(self,data):
        self.writer.Write(data)

    def Close(self):
        self.writer.Close()


#endclass EnvironmentGUI

#Parsing arguments

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        MASSIS-SIM Server
        --------------------------------
        Simulations from server SICOSSYS.
            - 1: Simulations number 1
            - 2: Simulations number 2
            - 3: Simulations number 3 of positions sensor
        '''),
    epilog='''ColosAAL 2017'''
)

parser.add_argument('-d', '--dist', help='Distribution of sensor on the red simulations (Default: A)', required=False)
parser.add_argument('-f', '--file', help='File from read the Simulation', required=False)
parser.add_argument('-s', '--scene', help='File describe de Scene', required=False)
parser.add_argument('-a', '--api', help='Api for Simulation (Default "/massis")', required=False)
parser.add_argument('-o', '--out', help='Sensor output results', required=False)
parser.add_argument('-c', '--color', help='Sim color', required=False)
parser.add_argument('-i', '--ip', help='Sim color', required=False)
parser.add_argument('-p', '--port', help='Sim color', required=False)
parser.add_argument('-q', '--net', help='Query Network configuration IP:PORT:SIM', required=False)
parser.add_argument('-n', '--name', help='Sim name', required=False)
args = parser.parse_args()

#end parsing arguments



#==============================================================================
#--------------------------------EXAMPLE CODE----------------------------------
#==============================================================================
#==============================================================================


data_obj = []


def dist(a, b):
    (x1, z1) = a
    (x2, z2) = b
    return math.hypot(x2 - x1, z2 - z1)


def detectorFn(env):
    agentData = env.getAgents()
    inTheSquare = 0
    numAgentsDetected=0
    timestamp = 0.0
    #paa cada agente
    for entityId in agentData:
        pos = (agentData[entityId]['position']['x'],agentData[entityId]['position']['z'])
        timestamp = agentData[entityId]['timestamp']
        env.setAgentColor(entityId, "blue")
        (minX,minY,maxX,maxY) = env.minRect(env.sensorPos)
        if ((pos[0] >= minX and pos[0] <= maxX) and (pos[1] >= minY and pos[1] <= maxY)):
            # si entra en el cuadrado
            #i = 1
            inTheSquare += 1
            detected = False
            for sPos in env.sensorPos:
                if detected == False:
                    distance = dist(pos, (sPos[0], sPos[1]))
                    if distance < sPos[2]:
                        env.setAgentColor(entityId, "black")
                        numAgentsDetected += 1
                        detected = True
                    else:
                        env.setAgentColor(entityId, "blue")

    error = inTheSquare - numAgentsDetected
    error = error*error;
    if inTheSquare == 0:
        if numAgentsDetected == 0:
            precision = 1
        else:
            precision = 0
    else:
        precision = numAgentsDetected/inTheSquare

    env.acumulatedError += error
    env.iterations += 1
    env.acumulatedPrecision += precision
    if env.lastTimestamp != 0:
        deltaTime = timestamp-env.lastTimestamp
    else:
        deltaTime = 0
    env.lastTimestamp = timestamp
    env.currenTime += deltaTime
    average = env.acumulatedError/env.iterations
    averagePrecision = env.acumulatedPrecision/env.iterations

    #print("Debug inTheSquare "+str(inTheSquare)+" numAgentsDetected "+str(numAgentsDetected) + " error "+ str(error)+ " env.acumulatedError "+str(env.acumulatedError) + " env.iterations "+str(env.iterations)+ " average error "+str(average) + " precision "+str(precision))

    env.WriteOutput(env.currenTime, average, averagePrecision)




def example(file, scene, out, colorSim, name, ip, port, sim, host, hostPort, sPositions):
    env = EnvironmentGUI(client=MassisClient(file=file, scene=scene, out = out, ip = ip, port = port, simId=sim, host=host, api = api, hostPort=hostPort), color = 0, colorSim = colorSim, name = name, sensorPos=sPositions)
    env.addTickListener(detectorFn)
    env.run()

    env.closeWriter()

__simId = 0
__file = ''
__scene = None
__dist = 'C'
__out = ""
__color = ""
__name = ""
__ip = ""
__port = 0
__network = ""

#==============================================================================================================
# sensorPosMul_A = ((40, 38.7,1.3), (40, 41.3,1.3), (51, 38.7,1.3), (51, 41.3,1.3), (64, 38.7,1.3), (64, 41.3,1.3))
# sensorPosMul_B = ((40, 38.7,1.3), (51, 38.7,1.3), (64, 38.7,1.3))
# sensorPosMul_C = ((40, 38.7,1.3), (40, 41.3,1.3), (64, 38.7,1.3), (64, 41.3,1.3))
# sensorPosMul_D = ((40, 38.7,1.3), (40, 41.3,1.3))

sensorPosMul = {
    'A': [[40, 38.7, 1.3], [40, 41.3, 1.3]],
    'B': [[40, 38.7, 1.3], [40, 41.3, 1.3], [51, 38.7, 1.3], [51, 41.3, 1.3]],
    'C': [[40, 38.7, 1.3], [40, 41.3, 1.3], [51, 38.7, 1.3], [51, 41.3, 1.3], [64, 38.7,1.3], [64, 41.3, 1.3]],
    'D': [[40, 38.7, 1.3], [51, 38.7, 1.3], [64, 38.7, 1.3]],
    'E': [[40, 41.3, 1.3], [51, 41.3, 1.3], [64, 41.3, 1.3]],
    'F': [[40, 40, 2.3]],
    'G': [[40, 40, 2.3], [51, 40, 2.3]],
    'H': [[40, 40, 2.3], [51, 40, 2.3], [64, 40, 2.3]],
    'I': [[45, 38.7, 1.3], [45, 41.3, 1.3], [65, 38.7, 1.3], [65, 41.3, 1.3]],
    'J': [[45, 38.7, 1.3], [45, 41.3, 1.3], [55, 38.7, 1.3], [55, 41.3, 1.3], [65, 38.7, 1.3], [65, 41.3, 1.3]],
    'K': [[45, 38.7, 1.3], [45, 41.3, 1.3], [50, 38.7, 1.3], [50, 41.3, 1.3], [55, 38.7, 1.3], [55, 41.3, 1.3], [60, 38.7, 1.3], [60, 41.3, 1.3], [65, 38.7, 1.3], [65, 41.3, 1.3]],
    'L': [[22, 62, 1.3], [22, 67, 1.3], [73, 62, 1.3], [73, 67, 1.3], [93, 62, 1.3], [93, 67, 1.3]],
    'M': [[22, 62, 1.3], [22, 67, 1.3], [28, 62, 1.3], [28, 67, 1.3], [73, 62, 1.3], [73, 67, 1.3], [88, 62, 1.3], [88, 67, 1.3], [93, 62, 1.3], [93, 67, 1.3]],
    'N': [[22, 62, 1.3], [22, 67, 1.3], [28, 62, 1.3], [28, 67, 1.3], [73, 62, 1.3], [73, 67, 1.3], [88, 62, 1.3], [88, 67, 1.3], [90, 62, 1.3], [90, 67, 1.3], [93, 62, 1.3], [93, 67, 1.3]]
}
#==============================================================================================================



if args.file is not None:
    __file = str(args.file)

if args.scene is not None:
    __scene = str(args.scene)

if args.dist is not None:
    __dist = str(args.dist).upper()

if args.api is not None:
    api = str(args.api)


if args.out is not None:
    __out = str(args.out)

if args.color is not None:
    __color = str(args.color)


if args.name is not None:
    __name = str(args.name)

if args.ip is not None:
    __ip = str(args.ip)

if args.port is not None:
    __port = int(args.port)


if args.net is not None:
    __network = str(args.net)

if __network != "":
    networkConfig = __network.split(':')
    __simId = networkConfig[2]
    __host = networkConfig[0]
    __hostPort = networkConfig[1]
else:
    __simId = 0
    __host = ""
    __hostPort = 0

example(file=__file, scene=__scene, out = __out, colorSim=__color, name=__name, ip= __ip, port = __port, sim = __simId, host = __host, hostPort = __hostPort,  sPositions=sensorPosMul[__dist])


