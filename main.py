from datetime import datetime        
import tkinter
import argparse
import os
import numpy
#import smbus #UNCOMMENT AFTER TESTING
#import RPi.GPIO as GPIO #UNCOMMENT AFTER TESTING
from constants import *
from PIL import Image, ImageDraw

IMAGE_DETECTIONS = 0
MICROPHONE_DETECTIONS = 0
TOTAL_DETECTIONS = IMAGE_DETECTIONS + MICROPHONE_DETECTIONS
DATE_TIME = None

def captureImage(repeat):
    if (not repeat):
        yetAnotherImageModule()
    else:
        try:
            while True:
                yetAnotherImageModule()
        except KeyboardInterrupt:\
            log("Image", DATE_TIME)

def yetAnotherImageModule():
    LEDControl(1)
    os.system("fswebcam -r " + RESOLUTION + " -S 4 --no-banner image.jpg")
    LEDControl(0)
    imageDetection("./images/image.jpg") #CHANGE
    try:
        os.remove("image.jpg")
    except FileNotFoundError:
        print("Fuck.")

def captureMicrophone():
    LEDControl(1)
    microphoneDetection()
    LEDControl(0)
    
def imageDetection(file):
    image = Image.open(file)
    pixels = numpy.array(image).reshape(-1, 3)
    for i in range(0, len(pixels) - 1):
        if pixels[i, 0] < 50 and pixels[i, 1] > pixels[i, 0] and pixels[i, 1] > pixels[i, 2]: #r < 50, g > r, g > b
            global DATE_TIME
            DATE_TIME = datetime.now()

            print("Image: Bug detected - " + DATE_TIME.strftime("%H:%M:%S %d/%m/%y"))
            draw(file)

            global IMAGE_DETECTIONS
            IMAGE_DETECTIONS += 1
            break
        i += 1
    
def draw(file):
    image = Image.open(file)
    width, height = image.size
    dimX = []
    dimY = []
    for x in range(0, width):
        for y in range(0, height):
            r, g, b = image.getpixel((x, y))
            if r  < 50 and g > r and g > b:
                dimX.append(x)
                dimY.append(y)
            y += 1
        x += 1
    ImageDraw.Draw(image).rectangle([min(dimX), min(dimY), max(dimX), max(dimY)], outline="red")
    image.save(DATE_TIME.strftime("%H-%M-%S_%d.%m.%Y") + ".ppm")

def microphoneDetection():
    try:
        while True:
            bus = smbus.SMBus(1)
            bus.write_byte(I2CADDRESS, 0x20)

            temp = bus.read_word_data(I2CADDRESS, 0x00)

            first = temp >> 8
            second = temp << 8

            switch = first | second
            comparisonValue = switch & 0x0FFF

            if comparisonValue > THRESHOLD:
                global DATE_TIME
                DATE_TIME = datetime.now()
                print("Microphone: Bug detected - " + DATE_TIME.strftime("%H:%M:%S %d/%m/%y"))

                global MICROPHONE_DETECTIONS
                MICROPHONE_DETECTIONS += 1
                break
    except KeyboardInterrupt:
        log("Microphone", dt)

def monitorLevels():
    for value in SOUND_CONTROL:
        GPIO.setup(value, GPIO.OUT)
    bus = smbus.SMBus(1)

    while True:
        bus.write_byte(I2CADDRESS, 0x20)

        temp = bus.read_word_data(I2CADDRESS, 0x00)

        first = temp >> 8
        second = temp << 8

        switch = first | second

        for i in range(len(SOUND_CONTROL)):
            if switch > THRESHOLD_VALUES[i]:
                GPIO.output(SOUND_CONTROL[i], True)
            else:
                GPIO.output(SOUND_CONTROL, False)

def LEDControl(control):
    if control == 0:
        #OFF
        #Red LED
        return
    elif control == 1:
        #ON
        #Yellow LED
        return

def GUI():
    root = tkinter.Tk(className="Bug ID")
    cameraStatus = tkinter.Label(root, text="Camera: ").pack()
    cameraDetections = tkinter.Label(root, text="Camera Detections: " + str(IMAGE_DETECTIONS)).pack()
    microphoneStatus = tkinter.Label(root, text="Microphone: ").pack()
    microphoneDetections = tkinter.Label(root, text="Microphone Detections: " + str(MICROPHONE_DETECTIONS)).pack()
    systemState = tkinter.Label(root, text="System State: ").pack()
    PWM = tkinter.Button(root, text="Toggle PWM").pack()
    servo = tkinter.Button(root, text="Toggle Servo Motor Supply").pack()
    snap = tkinter.Button(root, text="Snap", action = captureImage(False))

    photo = tkinter.PhotoImage(file="image.ppm")
    cv = tkinter.Canvas()
    cv.pack(side='bottom', fill='both', expand='yes')
    cv.create_image(10, 10, image=photo, anchor='nw')

    root.mainloop()

#def togglePWM():
#def toggleServo():
    
def log(type, now):
    with open("log.csv", "a") as log:
        log.write(type + "," + now.strftime("%d/%m/%y") + "," + now.strftime("%H:%M:%S\n"))
    
#def imageProcessing():

detector = argparse.ArgumentParser(description="Cockroach detection")
detector.add_argument("--image", help="Single image detection.", action="store_true")
detector.add_argument("--repeat", help="Repeated image detection.", action="store_true")
detector.add_argument("--microphone",help="Microphone detection.", action="store_true")
detector.add_argument("--monitor", help="Monitor volume", action="store_true")
detector.add_argument("--gui", help="GUI", action="store_true")
args = detector.parse_args()

if args.image:
    captureImage(False)
elif args.repeat:
    captureImage(True)
elif args.microphone:
    captureMicrophone()
elif args.monitor:
    monitorLevels()
elif args.gui:
    GUI()