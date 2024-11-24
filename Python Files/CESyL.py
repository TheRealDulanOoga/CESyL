from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
from threading import Thread

import InputHandlers
import Settings
import serial
import time
import json
import os

#set up global variables
serialCommunication = serial.Serial('COM4', 115200, timeout=1.0)
scalar = float
encoderModules = []
buttonModules = []

def DefaultOSCHandler(type, *args):
    isParam = "/param" in type
    isPatchUpdate = "/patch" in type
    isDocParam = "/doc" in type

    if isDocParam:
        Settings.OSCRECIEVEHISTORY.append([]) if "/ext" not in type else False
        return
    
    if (not (isParam or isPatchUpdate)):
        return
    
    Settings.OSCRECIEVEHISTORY[-1].append([type, *args])
    Settings.OSCRECIEVEHISTORY.append([]) if isPatchUpdate else False

    print(type, args)

def SetupInputModules():
    #Setup all of the encoder and button modules from the json file
    with open("encoder-data.json", "r") as f:
        data = json.load(f)

    #encoders
    i = 0
    for encoder in data["Encoders"]:
        print(i)
        i+=1
        if (encoder["Type"] == ""):
            encoderModules.append(InputHandlers.EncoderModule("", "None", "", [], []))
        else:
            buttonSettings = [setting for setting in encoder["ButtonSettings"].values()]
            LEDSettings = (dictionary.values() for dictionary in encoder["LEDSettings"])
            virtualEncoderSettings = (dictionary.values() for dictionary in encoder["KnobSettings"])

            encoderModules.append(InputHandlers.EncoderModule(encoder["Type"], buttonSettings, LEDSettings, encoder["VirtualEncoderInfo"], virtualEncoderSettings))
            Settings.ENCODERSCOUNT += 1

    #buttons
    for button in data["Buttons"]:
        if (button["Type"] == ""):
            buttonModules.append(InputHandlers.ButtonModule("", "None", "None"))
        else:
            buttonSettings = [setting for setting in button["ButtonSettings"].values()]
            LEDSettings = [dictionary for dictionary in button["LEDSettings"]]
            buttonModules.append(InputHandlers.ButtonModule(button["Type"], buttonSettings, LEDSettings))
            Settings.BUTTONSCOUNT += 1

    Settings.OSCCLIENT.send_message("/q/patch", 0)

def MainLoop():
    # encoder.calculateLEDBits(encoder.OSCValue)
    serialDataToSend = ""

    #Calculate the encoder module output message for LEDS
    for module in encoderModules:
        for led in module.calculateEncoderLEDValues():
            serialDataToSend += str(led) + "."
        serialDataToSend = serialDataToSend[:-1] + "|"
    serialDataToSend = serialDataToSend[:-1] + "\n"

    #Calculate the button module output message for LEDS
    for module in buttonModules:
        serialDataToSend += str(module.calculateButtonLEDValues()) + "|"
    serialDataToSend = serialDataToSend[:-1] + "\n"

    # Send outgoing Serial communication to the Teensy
    serialCommunication.write(serialDataToSend.encode('utf-8'))
        
    while serialCommunication.in_waiting <= 0:
        time.sleep(.01)

    # taking in the encoder and button values from Serial
    incomingSerialData = [item.split(".") for item in serialCommunication.readline().decode(
        'utf-8').rstrip().split("|")]

    for i, module in enumerate(encoderModules):
        module.updateCurrentEncoder(*incomingSerialData[i])
    for i, module in enumerate(buttonModules):
        module.updateButton(incomingSerialData[i + 55][0])

#Main Function
class MainRoutine(Thread):
    def __init__(self) -> None:
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        # time.sleep(2)
        serialCommunication.reset_input_buffer()
        print("Serial OK")

        #this needs to be changed for raspi
        os.chdir("CESyL")
        SetupInputModules()

        # Main loop
        while True:
            MainLoop()
                
# For testing total load under worst scenario
# serialCommunication.write("512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.512.".encode('utf-8'))
# print(serialDataToSend[:-1])

# for module in encoderModules:
#     module.virtualEncoders[0].LEDHue += 0.001
#     module.virtualEncoders[0].LEDHue %= 1
    
# assigning encoder and button values to their respective objects
# print(incomingSerialData[55:])
# print(
#     f"{encoderValues[1]}, {encoderModule.currentVirtualEncoder.counter}, {encoderModule.currentVirtualEncoder.OSCValue}, {encoderModule.currentVirtualEncoder.calculatedLEDBits}, {encoderValues[0]}")



if __name__ == "__main__":
    try:
        ip = "127.0.0.1"
        sendPort = 7000
        recievePort = 8000

        # send OSC messages
        client = Settings.OSCCLIENT = udp_client.SimpleUDPClient(ip, sendPort)

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

    except KeyboardInterrupt:
        print("Closing serial comms and halting the program")
        serialCommunication.close()