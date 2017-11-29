
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

from urllib.parse import urlencode # Python 2

#try:
#    from urllib.parse import urlparse
#except ImportError:
#     from urlparse import urlparse

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


class MassisHttpClient:

    def __init__(self, host, port, file , scene, simId=0, record=False, recordFile=""):
        self.host = host
        self.port = port
        self.simId = simId
        self.file = file
        self.scene = scene
        # self.http = urllib3.HTTPConnectionPool('http://' + str(self.host) + ":" + str(self.port) + api, maxsize=20)
        #self.http = urllib3.PoolManager(num_pools=20)

    def sendInmediate(self, endpoint, params={}):
        r = post('http://'+self.host+':'+str(self.port) + api + endpoint, params=params, stream=False)
        return json.loads(r.text)

    def sendStream(self, endpoint, params={}):
        if not(endpoint.startswith('/')):
            endpoint = '/'+endpoint
        headers = {'Accept': 'text/event-stream'}
        http = urllib3.PoolManager(num_pools=20)
        url = 'http://'+self.host+':'+ str(self.port)+api+endpoint
        return http.request('GET', url, fields=params, preload_content=False)
        #return get('http://'+self.host+':'+str(self.port)+endpoint,params=params,stream=True)

    def streamFast(self, endpoint):
        if not(endpoint.startswith('/')):
            endpoint = '/'+endpoint
        http = urllib3.PoolManager(num_pools=20)
        url = 'http://'+self.host+':'+str(self.port)+api+endpoint
        print(url)
        #creo la simulacion
        filePath =self.file;
        createFile = open(filePath, 'w+')
        createFile.close()
        for line in http.request('GET', url, preload_content=False):
            if (True):
                with io.FileIO(filePath, "a") as file:
                    if line.startswith(b'data: '):
                        file.write(line)
            if line.startswith(b'data: '):
                yield json.loads(line[len(b'data: '):].decode('utf-8'))

    def getSceneInfo(self):
        url = 'http://'+self.host+':'+str(self.port)+api+'/info/scene/'+str(self.simId)
        print("Command "+url)
        jsonScene = get(url, stream=False).text;
        with io.FileIO(self.scene, "w+") as file:
            file.write(jsonScene.encode())
            file.close()
        return  json.loads(jsonScene)

    def queryChanges(self, components):
        url = '/live/'+str(self.simId)+'/changes?'+urlencode([("components", "human") for x in components])
        return self.streamFast(url)


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
                    #print(data)
                    while lastUpdate>0 and lastUpdate < data['timestamp']:
                        sleep(0.001)
                        lastUpdate+=0.001
                    lastUpdate=data['timestamp']
                    self.updateAgent(data)
            else:
                break

    def stop(self):
         self.running=False


class EnvironmentGUI:

    def __init__(self, client, sensorPos=((37, 37))):
        self.colors=dict()
        self.client=client
        self.root = Tk()
        self.frame = Frame(self.root)
        self.mouseX=0
        self.mouseY=0
        width=850
        height=400
        self.frame.pack(fill=BOTH, expand=YES)
        self.canvas = ResizingCanvas(self.frame,width=width, height=height, bg=SIM_ID_COLORS[self.client.simId%len(SIM_ID_COLORS)], highlightthickness=0)
        self.canvas.pack(fill=BOTH, expand=YES)
        self.sceneInfo=client.getSceneInfo()
        (self.minX,self.minY,self.maxX,self.maxY)=self.findMinMax()
        self.listeners=list()
        self.coordLabel = Label(self.frame, text="()")
        self.timeLabel  = Label(self.frame, text="()")
        self.timeLabel.place(x =width-100, y = 0)
        self.coordLabel.place(x =10, y = 10)
        self.sensorPos = sensorPos


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
        return
        #self.redrawFurniture()
        #self.redrawWalls()
        #self.redrawAgents()
        #self.redrawCoordLabel()
        #self.redrawSensor(self.sensorPos)
        #self.drawMinRect(self.sensorPos)
        #self.root.after(50, self.redrawLoop)

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

#endclass EnvironmentGUI


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
        while self.currentTime < self.time:
            url = '/live/'+str(self.simId)+'/changes?'+"components=position"
            self.streamFast(url)

    def streamFast(self, endpoint):
        if not(endpoint.startswith('/')):
            endpoint = '/'+endpoint
        http = urllib3.PoolManager(num_pools=20)
        url = 'http://'+self.host+':'+str(self.port)+endpoint
        print(url)
        #request = http.request('GET', url,  preload_content=False)
        #print ("Status "+str(request.status))
        #print ("-------")
        #print("+"+request.data.decode('utf-8'))
        #line = request.data
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
        MASSIS-SIM Server
        --------------------------------
        Simulations from server SICOSSYS.
            - 1: Simulations number 1
            - 2: Simulations number 2
            - 3: Simulations number 3 of positions sensor
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


data_obj = []


def dist(a, b):
    (x1, z1) = a
    (x2, z2) = b
    return math.hypot(x2 - x1, z2 - z1)


def detectorFn(env):
    agentData = env.getAgents()
    count = 1
    for entityId in agentData:
        pos = (agentData[entityId]['position']['x'],agentData[entityId]['position']['z'])
        env.setAgentColor(entityId, "blue")
        if ((pos[0] >= 22 and pos[0] <= 86) and (pos[1] >= 28 and pos[1] <= 45)):
            # detectorPos=(40,37)
            i = 1
            for sPos in env.sensorPos:
                distance = dist(pos, (sPos[0], sPos[1]))
                count += 1
                if distance < sPos[2]:
                    print(str(int(time.time()*1000)) + "\t S" + str(i) + "\tAgent\t#" + str(entityId) + "\t[" + str(pos) + "]\t has been detected. Distance: \t" + str(distance) + "\t 1")
                    env.setAgentColor(entityId, "black")
                    #data_obj.append([count+1, 1])
                else:
                    #print(str(int(time.time()*1000)) + "\t S" + str(i) + "\tAgent\t#" + str(entityId) + "\t 0.0 \t is not detected. Distance: \t NaN \t 0")
                    env.setAgentColor(entityId, "blue")
                    #data_obj.append([count+1, 0])
                i += 1


def example(simId, host, port, file, scene, sPositions):
    env = EnvironmentGUI(client=MassisHttpClient(host=host, port=port, file = file, scene = scene, simId=simId), sensorPos=sPositions)
    env.addTickListener(detectorFn)
    env.run()






__simId = 0
__host = 'localhost'
__port = 80
__scene = ""
__file =  ""
__time = 0

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
    'H': [[40, 40, 2.3], [51, 40, 2.3], [64, 40, 2.3]]
}
#==============================================================================================================

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

#example(simId=__simId, host=__host, port=__port, file = __file, scene = __scene, sPositions=sensorPosMul[__dist])
download = Download(simId=__simId, host=__host, port=__port, file = __file, scene = __scene, time = __time)
download.DownloadSim()
