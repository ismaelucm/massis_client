import numpy as np
import matplotlib.pyplot as plt
import argparse
import textwrap

#plt.axis([0, 10, 0, 1])
#plt.ion()
CONST_TITLE = "Accuracy of sensors of different simulations"
CONST_X_LABEL = "Time"
CONST_Y_LABEL = "Accuracy"
CONST_LINE_SIZE = 4
CONST_FONT_TITLE_SIZE = 22
CONST_AXIS_SIZE = 16

class Plotting:

    def __init__(self, xSize, ySize, plt, size):
        self.xSize = xSize
        self.ySize = ySize
        self.size = size
        self.y = []
        for i in range(size):
            self.y.append([])
        self.plt = plt
        self.plt.xlabel(CONST_X_LABEL, fontsize=CONST_AXIS_SIZE)
        self.plt.ylabel(CONST_Y_LABEL, fontsize=CONST_AXIS_SIZE)

        self.plt.title(CONST_TITLE, fontsize=CONST_FONT_TITLE_SIZE)
        self.plt.axis([0, xSize, 0, ySize])
        self.plt.ion()


    def DrawPlot(self, i, value, color, label):
        self.y[i].append(value)
        self.plt.plot(self.y[i], color=color, label = label, linewidth=CONST_LINE_SIZE)
        self.plt.show()

    def Refresh(self, x, sleep):
        self.plt.pause(float(sleep))

        if x > self.xSize :
            self.plt.axis([x-self.xSize, x, 0, self.ySize])

    def ShowLeyend(self):
        legend = self.plt.legend(loc='upper left', shadow=True)
        frame = legend.get_frame()
        frame.set_facecolor('0.90')


def Readline(file):
    return file.readline()


def OpenFiles(files):
    f = []
    for i in range(len(files)):
        f.append(open(files[i],"r"))
    return f;


def CloseFiles(f):
    for i in range(len(f)):
        f[i].close()



#Parsing arguments

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        MASSIS-SIM Plotter
        '''),
    epilog='''ColosAAL 2017'''
)


parser.add_argument('-f', '--file', help='Files from read the Error', required=True)
parser.add_argument('-t', '--time', help='Simulation time', required=True)

args = parser.parse_args()

#end parsing arguments

__file = ''
__time = 0

if args.file is not None:
    __file = str(args.file)

if args.time is not None:
    __time = str(args.time)

files = __file.split("#")


print("Ficheros "+str(len(files)))

plot = Plotting(10,1,plt,len(files))

colors = ["red", "green", "blue", "black", "pink", "yellow"]

f = OpenFiles(files)


x = 0
stop = False

while not stop:

    print("files "+str(len(f)))
    for i in range(len(f)):
        data = Readline(f[i])
        if data is None:
            stop = True
        else:
            dataSplit = data.split(" ")
            print("Precision "+dataSplit[1])
            plot.DrawPlot(i,float(dataSplit[1]), colors[i] , "Sim "+str(i))

    if not stop:
        if x == 0:
            plot.ShowLeyend()
        plot.Refresh(x,__time)
        x += 1
