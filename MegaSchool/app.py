import os
import RPi.GPIO as GPIO
import time
from flask import Flask, render_template, request
import thread

app = Flask(__name__)

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

PATHTEMP = '/sys/bus/w1/devices/28-8000001fbd6b/w1_slave'
FAN = 17
LIGHTS = 18
PIR = 22
start = time.time()
start2  = time.time()
occupancy= 0
maxOccupied = 0
maxUnoccupied = 0
def backgroundLoop():
    while(True):
        global maxOccupied
        global maxUnoccupied
        time.sleep(0.5)
        global occupancy
        temp = getTemp()
        occupancy = checkOccupancy(10,occupancy)
        controlFan(temp,maxOccupied,maxUnoccupied)
        controlLights(occupancy, 20)

def setup():
    global maxOccupied
    global maxUnoccupied
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(FAN, GPIO.OUT)
    GPIO.setup(LIGHTS, GPIO.OUT)
    GPIO.setup(PIR, GPIO.IN)
    GPIO.setwarnings(False)
def getTemp():
    init = 0
    while init == 0:
        f = open(PATHTEMP, 'r')
        lines = f.readlines()
        f.close()
        if(lines[0].strip()[-3] == 'YES'):
            init = 1
        tempOut = lines[1].find('t=')
        if tempOut != -1:
            tempOut = lines[1].strip()[tempOut+2:]
            return float(tempOut)/1000.0
        return 0

def controlFan(temp,maxOccupied,maxUnoccupied):
    global occupancy
    threshold = int(maxUnoccupied)
    if(occupancy == int(1)):
        threshold = int(maxOccupied)
    if(threshold == 0):
        return 0
    if(temp > threshold):
        GPIO.output(FAN, GPIO.HIGH)
    else:
        GPIO.output(FAN, GPIO.LOW)

def checkOccupancy(threshold, currentState):
    global start
    if(time.time()-start > 10):
        if(GPIO.input(22)):
            start = time.time()
            return 1
        else:
            return 0
    else:
        return currentState

def controlLights(occupancy, threshold):
    global start2
    if(occupancy):
        start2 = time.time()
        GPIO.output(LIGHTS, GPIO.HIGH)
    if(occupancy == 0 and time.time() - start2 > threshold):
        GPIO.output(LIGHTS, GPIO.LOW)

setup()
thread.start_new_thread(backgroundLoop, ())
@app.route("/", methods =["GET","POST"])
def index():
    global occupancy
    global maxOccupied
    global maxUnoccupied
    if(request.method == "POST"):
        maxOccupied = request.form["occupied"]
        maxUnoccupied = request.form["unoccupied"]
    temp = getTemp()
    occupancy = checkOccupancy(10, occupancy)
    templateData = {
            'temperature' : temp,
            'occupancy' : occupancy,
            'maxOccupied': maxOccupied,
            'maxUnoccupied': maxUnoccupied
            }
    return render_template('index.html', **templateData)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port = 4444, debug = True)
        
