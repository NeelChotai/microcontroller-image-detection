from datetime import datetime        
import tkinter
import argparse
import os
import numpy
import time
import smbus
import RPi.GPIO as GPIO
from constants import *
from PIL import Image, ImageDraw, ImageTk

IMAGE_DETECTIONS = 0
MICROPHONE_DETECTIONS = 0
CAMERA_STATUS = "Inactive"
MICROPHONE_STATUS = "Inactive"
PWM_STATE = "Manual"
DATE_TIME = None

def captureImage(repeat):
    if (not repeat):
        yetAnotherImageModule()
    else:
        try:
            while True:
                yetAnotherImageModule()
        except KeyboardInterrupt:
            log("Image", DATE_TIME)

def yetAnotherImageModule():
    global CAMERA_STATUS
    if LED_ACTIVE: #built in failsafe due to LEDs being temperamental
        LEDControl(1)
        CAMERA_STATUS = "Active"
        os.system("fswebcam -r " + RESOLUTION + " -S 4 --no-banner image.jpg")
        LEDControl(0)
    else:
        CAMERA_STATUS = "Active"
        os.system("fswebcam -r " + RESOLUTION + " -S 4 --no-banner image.jpg")
    CAMERA_STATUS = "Inactive"
    imageDetection("image.jpg")
    os.remove("image.jpg")

def captureMicrophone():
    global MICROPHONE_STATUS
    if (LED_ACTIVE):
        LEDControl(1)
        MICROPHONE_STATUS = "Active"
        microphoneDetection()
        MICROPHONE_STATUS = "Inactive"
        LEDControl(0)
    else:
        MICROPHONE_STATUS = "Active"
        microphoneDetection()
        MICROPHONE_STATUS = "Inactive"
    
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
            comparison = switch & 0x0FFF

            if comparison > THRESHOLD:
                global DATE_TIME
                DATE_TIME = datetime.now()

                print("Microphone: Bug detected - " + DATE_TIME.strftime("%H:%M:%S %d/%m/%y"))

                global MICROPHONE_DETECTIONS
                MICROPHONE_DETECTIONS += 1
                break
    except KeyboardInterrupt:
        log("Microphone", DATE_TIME)

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
    LED_ON = 0x00
    LED_OFF = 0xFF
    bus = smbus.SMBus(1)
    if control == 0:
        bus.write_byte(I2C_YELLOW_LED, LED_OFF)
    elif control == 1:
        bus.write_byte(I2C_YELLOW_LED, LED_ON)

def GUI():
    root = tkinter.Tk(className="Bug ID")
    cameraStatus = tkinter.Label(root, text="Camera: " + CAMERA_STATUS).pack()
    cameraDetections = tkinter.Label(root, text="Camera Detections: " + str(IMAGE_DETECTIONS)).pack()
    microphoneStatus = tkinter.Label(root, text="Microphone: " + MICROPHONE_STATUS).pack()
    microphoneDetections = tkinter.Label(root, text="Microphone Detections: " + str(MICROPHONE_DETECTIONS)).pack()
    systemState = tkinter.Label(root, text="System State: " + PWM_STATE).pack()
    PWM = tkinter.Button(root, text="Toggle PWM", action=togglePWM).pack()
    snap = tkinter.Button(root, text="Snap", action=captureImage(False)).pack()

    photo = ImageTk.PhotoImage(Image.open(DATE_TIME.strftime("%H-%M-%S_%d.%m.%Y") + ".ppm"))
    panel = tkinter.Label(root, image = photo).pack(side="bottom", fill="both", expand="yes")

    root.mainloop()

def togglePWM():
    global PWM_STATE
    PWM_STATE = "Automatic"
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(10, GPIO.OUT)
    p = GPIO.PWM(10, 50)
    p.start(7.5)

    try:
        while True:
            p.ChangeDutyCycle(7.5)
            time.sleep(1)
            p.ChangeDutyCycle(12.5)
            time.sleep(1)
            p.ChangeDutyCycle(2.5)
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup

def log(type, now):
    with open("log.csv", "a") as log:
        log.write(type + "," + now.strftime("%d/%m/%y") + "," + now.strftime("%H:%M:%S\n"))

detector = argparse.ArgumentParser(description="Cockroach detection")
detector.add_argument("--image", help="Single image detection.", action="store_true")
detector.add_argument("--repeat", help="Repeated image detection.", action="store_true")
detector.add_argument("--microphone",help="Microphone detection.", action="store_true")
detector.add_argument("--monitor", help="Monitor volume", action="store_true")
detector.add_argument("--gui", help="GUI", action="store_true")
detector.add_argument("--toggle", help="Toggle PWM", action="store_true")
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
elif args.toggle:
    togglePWM()
