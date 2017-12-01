import numpy as np
import matplotlib.pyplot as plt
import argparse
import textwrap
import socket
import base64
from enum import Enum

#plt.axis([0, 10, 0, 1])
#plt.ion()
CONST_TITLE = "Accuracy of sensors of different simulations"
CONST_X_LABEL = "Time"
CONST_Y_LABEL = "Accuracy"
CONST_LINE_SIZE = 4
CONST_FONT_TITLE_SIZE = 22
CONST_AXIS_SIZE = 16

class ReaderType(Enum):
    FILE = 1
    SOCKET = 2

TCP_IP = '127.0.0.1'
BUFFER_SIZE = 256

class ServerSocket:
    def __init__(self, ip, port, connections, buffer):
        self.port = port
        self.ip = ip
        self.connections = connections
        self.sockets = []
        self.buffer = buffer
        self.data = []


    def WaitingForClients(self):
        for i in range(self.connections):
            print ("Number clients connected "+str(i)+"/"+str(self.connections))
            print ("Waiting for clients...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.ip, self.port))
            s.listen(1)
            conn, addr = s.accept()
            self.sockets.append((conn,addr))
            self.data.append("")
            i += 1
            self.port += 1
        print ("Number clients connected "+str(self.connections)+"/"+str(self.connections))

    def Read(self,i):
        binary = self.sockets[i][0].recv(self.buffer)
        dataStr = binary.decode('utf-8')
        self.data[i] = self.data[i] + str(dataStr)
        print("buffer ["+self.data[i]+"]")

        strArr = self.data[i][:self.data[i].index(";")]
        self.data[i] = self.data[i][(self.data[i].index(";")+1):]

        if strArr != None:
            return strArr
        return None


    def Close(self):
        for i in range(self.connections):
            self.sockets[i][0].close()

    def GetNumConnections(self):
        return self.connections

class Plotting:

    def __init__(self, xSize, ySize, plt, size):
        self.xSize = xSize
        self.ySize = ySize
        self.size = size
        self.yVector = []
        self.xVector = []
        for i in range(size):
            self.yVector.append([])
            self.xVector.append([])
        self.plt = plt
        self.plt.xlabel(CONST_X_LABEL, fontsize=CONST_AXIS_SIZE)
        self.plt.ylabel(CONST_Y_LABEL, fontsize=CONST_AXIS_SIZE)

        self.plt.title(CONST_TITLE, fontsize=CONST_FONT_TITLE_SIZE)
        self.plt.axis([0, xSize, 0, ySize])
        self.plt.ion()


    def DrawPlot(self, i, time, value, color, label):
        self.yVector[i].append(value)
        self.xVector[i].append(time)
        self.plt.plot(self.xVector[i],self.yVector[i], color=color, label = label, linewidth=CONST_LINE_SIZE)
        self.plt.show()

    def Refresh(self, x, sleep):
        self.plt.pause(float(sleep))

        if x > self.xSize :
            self.plt.axis([x-self.xSize, x, 0, self.ySize])

    def ShowLeyend(self):
        legend = self.plt.legend(loc='upper left', shadow=True)
        frame = legend.get_frame()
        frame.set_facecolor('0.90')


class FileManager:
    def __init__(self,file):
        self.fileNames = file;
        self.files = [];

    def Readline(self,i):
        return self.files[i].readline()

    def OpenFiles(self):
        for i in range(self.GetNumFiles()):
            self.files.append(open(self.fileNames[i],"r"))

    def CloseFiles(self):
        for i in range(len(self.files)):
            self.files[i].close()

    def GetNumFiles(self):
        return len(self.fileNames)



class Reader:
    def __init__(self,readerType, files, ip, port, connections, buffer ):
        self.readerType = readerType
        if self.readerType == ReaderType.FILE:
            self.fileMgr = FileManager(files)
        else:
            self.socketMgr = ServerSocket(ip, port, connections, buffer)

    def Open(self):
        if self.readerType == ReaderType.FILE:
            self.fileMgr.OpenFiles()
        else:
            self.socketMgr.WaitingForClients()

    def Close(self):
        if self.readerType == ReaderType.FILE:
            self.fileMgr.CloseFiles()
        else:
            self.socketMgr.Close()


    def Read(self,i):
        if self.readerType == ReaderType.FILE:
            return self.fileMgr.Readline(i)
        else:
            return self.socketMgr.Read(i)


    def GetNumSources(self):
        if self.readerType == ReaderType.FILE:
            return self.fileMgr.GetNumFiles()
        else:
            return self.socketMgr.GetNumConnections()


class Program:
    def __init__(self, ip, bufferSize):
        self.fileSrt = ""
        self.time = 0
        self.connections = 0
        self.port = 0
        self.files = None
        self.ip = ip
        self.bufferSize = bufferSize
        self.colors = ["red", "green", "blue", "black", "pink", "yellow"]
        self.ParsingArgs()

    def ParsingArgs(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent('''\
        MASSIS-SIM Plotter
        '''),
            epilog='''ColosAAL 2017'''
        )

        parser.add_argument('-f', '--file', help='Files from read the Error', required=False)
        parser.add_argument('-p', '--port', help='Port where the server listen the connections', required=False)
        parser.add_argument('-c', '--connections', help='Number of expected connections', required=False)
        parser.add_argument('-t', '--time', help='Simulation time', required=True)
        args = parser.parse_args()

        if args.file is not None:
            print("Configure using files")
            self.fileSrt = str(args.file)

        if args.time is not None:
            self.time = str(args.time)

        if args.connections is not None:
            print("Configure using conections")
            self.connections = int(args.connections)

        if args.port is not None:
            print("Configure using conections")
            self.port = int(args.port)

        print("Debug: fileName "+self.fileSrt+" port "+str(self.port)+ " connections "+str(self.connections) + " time "+str(self.time))

    def Main(self):
        error = False
        if self.fileSrt != "":
            print("Spliting file format")
            self.files = self.fileSrt.split("#")

        if self.files != None:
            self.reader = Reader(ReaderType.FILE, self.files,self.ip,self.port,self.connections, self.bufferSize)
            print("using files")
        elif self.port != 0 and self.connections > 0:
            self.reader = Reader(ReaderType.SOCKET, None,self.ip,self.port,self.connections, self.bufferSize)
            print("using sockets")
        else:
            print("Error, you must define the files or the port to wait the source data. See help -h for more information")
            error = True

        if not error:
            self.plot = Plotting(10,1,plt,self.reader.GetNumSources())
            self.reader.Open()
            x = 0
            stop = False
            xTime = 0.0
            while not stop:

                #print("files "+str(self.fileMgr.GetNumFiles()))
                for i in range(self.reader.GetNumSources()):
                    data = self.reader.Read(i)
                    if data is None:
                        stop = True
                    else:
                        dataSplit = data.split(" ")
                        print("Precision "+dataSplit[2])
                        xTime = float(dataSplit[0])
                        self.plot.DrawPlot(i,float(dataSplit[0]),float(dataSplit[2]), self.colors[i] , "Sim "+str(i))

                if not stop:
                    if x == 0:
                        self.plot.ShowLeyend()

                    self.plot.Refresh(x,self.time)
                    x = xTime

            self.reader.Close()







program = Program(TCP_IP,BUFFER_SIZE)
program.Main()
#end parsing arguments








