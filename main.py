from datetime import datetime        
import tkinter
import argparse
import os
import numpy
from constants import *
import smbus
from PIL import Image, ImageFilter, ImageDraw

def captureImage():
    while True:
        #LEDControl(1)
        os.system("fswebcam -r " + RESOLUTION + " -S 4 --no-banner image.jpg") #capture
        #LEDControl(0)
        imageDetection("image.jpg")
        os.remove("image.jpg") #cleanup
        
def captureMicrophone():
    #LEDControl(1)
    microphoneDetection() #change GUI state
    #LEDControl(0)
    
def imageDetection(file):
    
    image = Image.open(file)
    pixels = numpy.array(image).reshape(-1, 3)
        
    for i in range(0, len(pixels) - 1):
        if(pixels[i, 0] < 20 and pixels[i, 1] > pixels[i, 0] and pixels[i, 1] > pixels[i, 2]): #g > r, g > b, r < 150 #10, 40, 50
            dt = datetime.now()
            log("Image", dt)
            draw(file, dt)
            break
        i += 1
    
def draw(file, now):
    image = Image.open(file)
    width, height = image.size
    dimX = []
    dimY = []
    for x in range(0, width):
        for y in range (0, height):
            r, g, b = image.getpixel((x, y))
            if(r  < 20 and g > r and g > b):#if(r < 20 and g < 40 and b < 50):
                dimX.append(x)
                dimY.append(y)
            y += 1
        x += 1
    ImageDraw.Draw(image).rectangle([min(dimX), min(dimY), max(dimX), max(dimY)], outline="red")
    image.save(now.strftime("%H-%M-%S_%d.%m.%Y") + ".ppm")
    

def microphoneDetection():
    bus = smbus.SMBus(1)
    while True:
        bus.write_byte(I2CADDRESS, 0x20)
        tmp = bus.read_word_data(I2CADDRESS, 0x00)
        firstHalf = tmp >> 8
        secondHalf = tmp << 8
        switched = firstHalf | secondHalf
        comparisonValue = switched & 0x0FFF

        if comparisonValue > THRESHOLD:
            log("Microphone", datetime.now())
        break

def LEDControl(control):
    if (control == 0):
        #OFF
        #Red LED
        return;
    elif (control == 1):
        #ON
        #Yellow LED
        return;
    else:
        raise Exception("Out of range.")
    

def GUI():
    root = tkinter.Tk(className="Cockroach ID")
    cameraStatus = tkinter.Label(root, text="Camera: ").pack()
    cameraDetections = tkinter.Label(root, text="Camera Detections: ").pack()
    microphoneStatus = tkinter.Label(root, text="Microphone: ").pack()
    microphoneDetections = tkinter.Label(root, text="Microphone Detections: ").pack()
    systemState = tkinter.Label(root, text="System State: ").pack()
    PWM = tkinter.Button(root, text="Toggle PWM").pack()
    servo = tkinter.Button(root, text="Toggle Servo Motor Supply").pack()
    root.mainloop()

#def togglePWM():
#def toggleServo():
        
    
def log(type, now):
    print(type + ": Bug detected - " + now.strftime("%H:%M:%S %d/%m/%y"))
    with open("log.csv", "a") as log:
        log.write(type + "," + now.strftime("%d/%m/%y") + "," + now.strftime("%H:%M:%S\n"))
    
#def imageProcessing():

#unnecessary for the moment    
#detector = argparse.ArgumentParser(description="Cockroach detection")
#detector.add_argument() #one image

#detector.add_argument() #repeatedly take images


imageDetection("./images/image3.jpg")