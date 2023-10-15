from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
from threading import Thread

import serial
import time
import math
import numpy

serialCommunication = serial.Serial('COM4', 115200, timeout=1.0)


scalar = float


def HSVtoRGB(h: scalar, s: scalar, v: scalar) -> tuple:
    if s:
        if h == 1.0:
            h = 0.0
        MOD = int(h*6.0)
        F = h * 6.0 - MOD

        W = v * (1.0 - s)
        Q = v * (1.0 - s * F)
        T = v * (1.0 - s * (1.0 - F))

        match MOD:
            case 0: return (v, T, W)
            case 1: return (Q, v, W)
            case 2: return (W, v, T)
            case 3: return (W, Q, v)
            case 4: return (T, W, v)
            case 5: return (v, W, Q)
            case _: return (v, v, v)


class VirtualEncoder():
    def __init__(self, OSCDirectory: str, hue: scalar = 0, steps=32, maxValue=1, minValue=0, ledCount=4, ledBitDepth=8):
        self.OSCDirectory = OSCDirectory
        self.ledCount = ledCount
        self.bitDepth = ledBitDepth
        self.bitMask = ledBitDepth - 1
        self.bitCount = int(math.log2(ledBitDepth))
        self.steps = steps * 4
        self.maxValue = maxValue
        self.minValue = minValue

        self.counter = 0
        self.currentInputtedCounter = 0
        self.previousInputtedCounter = 0
        self.OSCValue = 0
        self.lastGreyCodeValue = 0
        self.lastRotation = 0

        # TODO Make these functions eventually
        self.LEDBrightnessModes = [
            "NORMAL ROTORY STACK",
            "RGB ROTORY STACK",
            "CENTER NORMAL STACK",
            "CENTER RGB STACK",
            "COLOR SHIFT",
            "GRADIENT STACK"
        ]
        self.LEDHue = hue
        self.calculatedLEDBits = [0, 0, 0, 0]

    def updateEncoderCounter(self, setValue):
        self.currentInputtedCounter = setValue
        self.counter += self.currentInputtedCounter - self.previousInputtedCounter
        self.counter = max(min(self.counter, self.steps), 0)

        valueRange = self.maxValue - self.minValue
        normalizedCounter = self.counter / self.steps
        self.OSCValue = (normalizedCounter * valueRange) + self.minValue

        self.previousInputtedCounter = self.currentInputtedCounter

        client.send_message(self.OSCDirectory, self.OSCValue)

    def calculateLEDBits(self):
        stepsPerLED = self.steps / self.ledCount

        # All solid LEDs
        solidColorRGB = HSVtoRGB(self.LEDHue, 1.0, 1.0)
        solidLEDsCount = math.floor(self.counter / stepsPerLED)
        solidColorCalculatedBits = 0

        for i in range(3):
            solidColorCalculatedBits += int(
                solidColorRGB[2 - i] * self.bitMask) << (self.bitCount * i)

        for i in range(solidLEDsCount):
            self.calculatedLEDBits[i] = solidColorCalculatedBits

        # Single LED with variable brightness
        appendRGB = 0
        middleLEDBrightness = (self.counter % stepsPerLED) / stepsPerLED
        middleLEDColorValues = HSVtoRGB(self.LEDHue, 1.0, middleLEDBrightness)

        for i in range(3):
            appendRGB += int(
                middleLEDColorValues[2 - i] * self.bitMask) << (self.bitCount * i)

        # All completely dark LEDs
        for i in range(solidLEDsCount, self.ledCount):
            self.calculatedLEDBits[i] = appendRGB
            appendRGB = 0


class EncoderModule():
    def __init__(self, virtualEncoderSettings, ledCount=4, ledBitDepth=8):
        self.ledCount = ledCount
        self.ledBitDepth = ledBitDepth

        self.virtualEncoders = []
        for encoderArgs in virtualEncoderSettings:
            newEncoder = VirtualEncoder(
                *encoderArgs, ledCount=ledCount, ledBitDepth=ledBitDepth)
            self.virtualEncoders.append(newEncoder)

        self.currentEncoderIndex = 0
        self.currentVirtualEncoder: VirtualEncoder = self.virtualEncoders[0]

        self.buttonPressHistory = [1] + [0] * 5

    def updateCurrentEncoder(self, buttonPress, controllerEncoderCount):
        self.buttonPressHistory.pop(1)
        self.buttonPressHistory.append(int(buttonPress))
        if (numpy.prod(self.buttonPressHistory) != 0):
            self.currentEncoderIndex += 1
            self.buttonPressHistory[0] = 0
            self.currentEncoderIndex %= len(self.virtualEncoders)
            self.currentVirtualEncoder: VirtualEncoder = self.virtualEncoders[
                self.currentEncoderIndex]
            self.currentVirtualEncoder.previousInputtedCounter = int(
                controllerEncoderCount)
        elif sum(self.buttonPressHistory[1:]) == 0:
            self.buttonPressHistory[0] = 1

        self.currentVirtualEncoder.updateEncoderCounter(
            int(controllerEncoderCount))

    def calculateEncoderLEDValues(self):
        self.currentVirtualEncoder.calculateLEDBits()
        return self.currentVirtualEncoder.calculatedLEDBits


class ButtonModule():
    def __init__(self, encoderValues, OSCValue, function):
        self.OSCValue = OSCValue
        self.execution = function

    def detectButtonPress():
        # detect when button state changes

        # Send increment on the OSC value
        # Execute function
        pass

    def calculateLEDBits():
        # much simpler because you only have one LED
        pass


class MainRoutine(Thread):

    def __init__(self) -> None:
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        time.sleep(2)
        serialCommunication.reset_input_buffer()
        print("Serial OK")

        encoderModules = [
            EncoderModule([
                ["/param/a/filter/1/cutoff", 0.67],
                ["/param/a/filter/2/cutoff", 0],
                ["/param/a/filter/config", 0.125, 7, 7]
            ]),
            EncoderModule([
                ["/param/a/filter/1/resonance", 0.8],
                ["/param/a/filter/2/resonance", 0.1],
                ["/param/a/filter/1/type", 0.4, 33, 33]
            ])
        ]

        try:
            while True:
                # encoder.calculateLEDBits(encoder.OSCValue)
                serialDataToSend = ""
                for module in encoderModules:
                    for led in reversed(module.calculateEncoderLEDValues()):
                        serialDataToSend += str(led) + "."
                serialDataToSend = serialDataToSend[:-1]
                serialDataToSend += "\n"
                # For testing total load under worst scenario
                # serialCommunication.write("512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.".encode('utf-8'))
                serialCommunication.write(serialDataToSend.encode('utf-8'))

                while serialCommunication.in_waiting <= 0:
                    time.sleep(.01)

                encoderValues = [item.split('|') for item in serialCommunication.readline().decode(
                    'utf-8').rstrip().split(',')]

                for i, module in enumerate(encoderModules):
                    module.updateCurrentEncoder(*encoderValues[i])
                # print(
                #     f"{encoderValues[1]}, {encoderModule.currentVirtualEncoder.counter}, {encoderModule.currentVirtualEncoder.OSCValue}, {encoderModule.currentVirtualEncoder.calculatedLEDBits}, {encoderValues[0]}")

        except (KeyboardInterrupt):
            print("Close Serial Coms")
            serialCommunication.close()


def DefaultOSCHandler(type, *args):
    print(type, args)


if __name__ == "__main__":
    ip = "127.0.0.1"
    sendPort = 7000
    recievePort = 8000

    # send OSC messages
    client = udp_client.SimpleUDPClient(ip, sendPort)

    # recieve OSC messages
    dispatcher = dispatcher.Dispatcher()
    dispatcher.set_default_handler(DefaultOSCHandler)

    # setup main code stuff and OSC
    MainRoutine()
    # new EncoderModule listOfEncoderModules[[], [], []]

    # OSC start
    server = osc_server.ThreadingOSCUDPServer((ip, recievePort), dispatcher)
    print(f"Servering on {server.server_address}")
    server.serve_forever()

    # def calculateGreyCode(self):
    #     currentGreyCodeValue = int(self.inputtedValues[1:3], 2)

    #     if (currentGreyCodeValue < 2):
    #         currentGreyCodeValue += 1
    #         currentGreyCodeValue %= 2

    #     difference = currentGreyCodeValue - self.lastGreyCodeValue
    #     match (difference % 4):
    #         case 3:  # 2-3, 1-2, 0-1, or 3-0
    #             self.lastRotation = -1
    #         case 1:  # 3-2, 2-1, 1-0, or 0-3
    #             self.lastRotation = 1
    #         case 0:
    #             self.lastRotation = 0

    #     self.lastGreyCodeValue = currentGreyCodeValue
    #     return self.lastRotation
