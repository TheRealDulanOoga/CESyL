import math
import time
import numpy
import UsefulFunctions
import Settings

# A virtual object that represents a singular setting that one encoder will change
# There will be multiple of these assigned to a single encoder "module" (one rotory encoder / purple PCB)
class VirtualEncoder():
    # Virtual Encoder Constructor Function
    def __init__(self, knobFunction : callable, knobFunctionArgs : list, hue: float = 0,  steps=32, maxValue=1.0, minValue=0.0, ledBehavior = "Rotory Stack", ledBitDepth=Settings.PWMSTEPS, ledCount=Settings.LEDCOUNT):

        #Functions
        self.knobFunction = knobFunction
        self.knobFunctionArgs = knobFunctionArgs

        # LED Information
        self.ledBehavior = ledBehavior
        self.steps = steps * 4
        self.maxValue = maxValue
        self.minValue = minValue

        # PWM Information
        self.bitDepth = ledBitDepth
        self.bitMask = ledBitDepth - 1
        self.bitCount = int(math.log2(ledBitDepth))
        self.ledCount = ledCount

        # Knob Counter Information
        self.counter = 0
        self.currentInputtedCounter = 0
        self.previousInputtedCounter = 0
        self.clampedCounter = 0
        self.lastGreyCodeValue = 0
        self.lastRotation = 0

        # LED Functionality
        self.LEDHue = hue
        self.calculatedLEDBits = [0, 0, 0, 0]
        # TODO Make these functions eventually
        self.LEDBheaviorModes = [
            "NORMAL ROTORY STACK",
            "RGB ROTORY STACK",
            "CENTER NORMAL STACK",
            "CENTER RGB STACK",
            "COLOR SHIFT",
            "GRADIENT STACK"
        ]

    # Update the value associated with the rotory encoder using data from Serial
    def updateEncoderCounter(self, setValue):
        self.currentInputtedCounter = setValue
        difference = self.currentInputtedCounter - self.previousInputtedCounter
        self.counter += difference
        self.counter = max(min(self.counter, self.steps), 0)

        valueRange = self.maxValue - self.minValue
        normalizedCounter = self.counter / self.steps
        self.clampedCounter = (normalizedCounter * valueRange) + self.minValue

        self.previousInputtedCounter = self.currentInputtedCounter

        return difference

    def assignChangedCounter(self, clampedValue):
        valueRange = self.maxValue - self.minValue
        normalizedCounter = (clampedValue - self.minValue) / valueRange
        self.counter = normalizedCounter * self.steps
    
        # Grabs the value(s) of encoder(s) from surge and assigns those values when one of them is updated
   
    def recieveOSCAssignments(self, isNewEncoder):
        reviewHistoryLength = len(Settings.OSCRECIEVEHISTORY) - 1
        noHistory = reviewHistoryLength <= 0
        historyOverflow = reviewHistoryLength > Settings.ENCODERSCOUNT + Settings.BUTTONSCOUNT
        if noHistory and not isNewEncoder or historyOverflow:
            Settings.OSCRECIEVEHISTORY = [[]]
            return
        
        # Create OSC address to be used for the query
        extendedMessage = "/q" + self.knobFunctionArgs[0]
        isExtendedValue = "+" in extendedMessage
        message = extendedMessage[:extendedMessage.rindex("/")] if isExtendedValue else extendedMessage

        isPatchUpdate = False
        if not noHistory:
            isPatchUpdate = "/patch" in Settings.OSCRECIEVEHISTORY[0][0][0]
            isMatchingParam = message in "/q" + Settings.OSCRECIEVEHISTORY[0][0][0]
            if (not (isPatchUpdate or isMatchingParam)):
                return
            
        # Send the message, await response, and update the current encoder accordingly
        print("\nUpdating Encoder Values . . .", reviewHistoryLength)
        Settings.OSCCLIENT.send_message(message, 0)
        while Settings.OSCRECIEVEHISTORY[reviewHistoryLength] == []:
            time.sleep(0.001)

        itemIndex = 0
        # If it is a special OSC value with extended capabilities then it needs special treatment (take the base value and then find it from that query instead)
        if isExtendedValue:
            for item in Settings.OSCRECIEVEHISTORY[reviewHistoryLength]:
                if extendedMessage in "/q" + item[0]:
                    break
                itemIndex += 1

        print(message)
        self.assignChangedCounter(Settings.OSCRECIEVEHISTORY[reviewHistoryLength][itemIndex][1])
        print(Settings.OSCRECIEVEHISTORY[reviewHistoryLength][0])
        print(self.counter)

        if isNewEncoder or not isPatchUpdate:
            Settings.HISTORYSIZE = 0
            Settings.OSCRECIEVEHISTORY = [[]]

        # reviewHistoryLength = len(Settings.OSCRECIEVEHISTORY) - 1
        # repeatValue = reviewHistoryLength > 1 and Settings.OSCRECIEVEHISTORY[1][0][0] == self.knobFunctionArgs[0]
        # if repeatValue or Settings.HISTORYSIZE > Settings.ENCODERSCOUNT + 6:
        #     Settings.HISTORYSIZE = 0
        #     Settings.OSCRECIEVEHISTORY = [[]]
        #     return
        
        # Settings.HISTORYSIZE += 1

        # # Create OSC address to be used for the query
        # extendedMessage = "/q" + self.knobFunctionArgs[0]
        # isExtendedValue = "+" in extendedMessage
        # message = extendedMessage[:extendedMessage.rindex("/")] if isExtendedValue else extendedMessage

        # if reviewHistoryLength > 0:
        #     isParam = "/param" in Settings.OSCRECIEVEHISTORY[0][0][0]
        #     isMatchingParam = message in "/q" + Settings.OSCRECIEVEHISTORY[0][0][0]
        #     if (isParam and not isMatchingParam):
        #         return

        # # Send the message, await response, and update the current encoder accordingly
        # print("\nUpdating Encoder Values . . .")
        # Settings.OSCCLIENT.send_message(message, 0)
        # time.sleep(0.02)

        # # If it is a special OSC value with extended capabilities then it needs special treatment (take the base value and then find it from that query instead)
        # if isExtendedValue:
        #     for item in Settings.OSCRECIEVEHISTORY[reviewHistoryLength:]:
        #         if extendedMessage in "/q" + item[0]:
        #             break
        #         reviewHistoryLength += 1
    
        # print(message)
        # self.assignChangedCounter(Settings.OSCRECIEVEHISTORY[reviewHistoryLength][1][0])
        # print(Settings.OSCRECIEVEHISTORY[reviewHistoryLength])
        # print(self.counter)

        # if isNewEncoder or isParam: 
        #     Settings.HISTORYSIZE = 0
        #     Settings.OSCRECIEVEHISTORY = [[]]

    # Executes the assigned function for when the knob turns
    def doKnobAction(self):
        UsefulFunctions.FUNCS[self.knobFunction](self)



# A class that holds the higher level data that goes with the whole Purple PCB
# One of these for each PCB
# Instantiates new virtual encoders for every different combination of settings given
class EncoderModule():
    # Encoder Module Constructor Function
    def __init__(self, type: str, buttonSettings: list, LEDSettings: list, virtualEncoderInfo: list, virtualEncoderSettings: list, ledBitDepth=Settings.PWMSTEPS, ledCount=Settings.LEDCOUNT):
        # Knob info
        self.groupType = type
        
        # Variables from constructor
        self.ledCount = ledCount
        self.ledBitDepth = ledBitDepth

        # List of virtual encoders associated with this module
        self.virtualEncoders = {"a": []}
        self.currentEncoderIndecies = {"a": [0, 0]}
        self.currentEncoderIndex = 0
        self.currentEncoderSubIndex = 0
        self.sceneStatus = 0

        if buttonSettings == "None":
            self.virtualEncoders = {"a": [[VirtualEncoder("None", [], ledCount=ledCount, ledBitDepth=ledBitDepth)]]}
        
        else:
            self.sceneStatus = virtualEncoderInfo["Scenes"]
            if self.sceneStatus == 2:
                self.virtualEncoders = {"a": [], "b": []}
                self.currentEncoderIndecies = {"a": [0, 0], "b": [0, 0]}

            for _ in range(virtualEncoderInfo["StepsPerCycle"]):
                for scene in self.virtualEncoders:
                    self.virtualEncoders[scene].append([])

            for encoderArgList in virtualEncoderSettings:
                encoderArgList = list(encoderArgList)
                encoderFunctionArgs = encoderArgList[1]

                sceneValue = encoderFunctionArgs[1] if "<s>" in encoderFunctionArgs[0] else "a"
                encoderGroupIndex = encoderFunctionArgs[2]
                encoderSubIndex = encoderFunctionArgs[3]

                encoderFunctionArgs[0] = encoderFunctionArgs[0].replace("<s>", str(sceneValue)).replace("<n>", str(encoderSubIndex + 1))
                
                newEncoder = VirtualEncoder(*encoderArgList, ledCount=ledCount, ledBitDepth=ledBitDepth)

                self.virtualEncoders[sceneValue][encoderGroupIndex].append(newEncoder)

            # for scene in ["a", "b"]:
            #     print("--------------")
            #     for i in range(len(self.virtualEncoders[scene])):
            #         for j in range(len(self.virtualEncoders[scene][i])):
            #             print(scene, i, j, self.virtualEncoders[scene][i][j].knobFunctionArgs[0])
            #         print("\n")



        # Variables associated with the encoders list
        self.rawEncoderCounter = 0
        self.currentVirtualEncoder: VirtualEncoder =  self.virtualEncoders[Settings.globalIndecies["Global"]["Scene"]["Current Value"]][0][0]

        # Button presses function
        self.buttonBehavior = buttonSettings[0]
        self.buttonFunction = buttonSettings[1]
        self.buttonFunctionArgs = buttonSettings[2]

        self.currentButtonFunctionValue = 0
        self.buttonFunctionMaxValue = self.buttonFunctionArgs[0]

        # Button presses data
        self.buttonPressHistory = [1] + [0] * 5
        self.buttonIsPressed = False
        self.buttonStatusHasChanged = False

    # Detects if the button has been pressed and if it has changed states
    def detectButtonPress(self, buttonPress):
        self.buttonPressHistory.pop(1)
        self.buttonPressHistory.append(int(buttonPress))
        self.buttonStatusHasChanged = True

        # The instant that button press history is switching all on
        if (numpy.prod(self.buttonPressHistory) != 0):
            self.buttonPressHistory[0] = 0
            self.buttonIsPressed = True
        # The instant that button press history is switching off
        elif sum(self.buttonPressHistory) == 0:
            self.buttonPressHistory[0] = 1
            self.buttonIsPressed = False
        # If button press history is in a steady state
        else:
            self.buttonStatusHasChanged = False

    # Handles the button functions
    def doButtonAction(self):
        buttonToggleOn = self.buttonIsPressed and self.buttonStatusHasChanged and self.buttonBehavior == "Toggled On"
        buttonWhilePressed = self.buttonIsPressed and self.buttonBehavior == "While On"
        buttonToggledBi = self.buttonStatusHasChanged and self.buttonBehavior == "Toggled Bi"

        if (buttonToggleOn or buttonWhilePressed or buttonToggledBi):
            UsefulFunctions.FUNCS[self.buttonFunction](self)

    # Handles all updates to the status of the current virtual encoder and the encoder module
    def updateCurrentEncoder(self, buttonPress, rawEncoderCounter):
        # Set up a few preliminary variables
        self.rawEncoderCounter = rawEncoderCounter

        scene = Settings.globalIndecies["Global"]["Scene"]["Current Value"] if self.sceneStatus == 2 else "a"
        self.currentEncoderIndecies[scene][0] = Settings.globalIndecies["Scene-dependant"][self.groupType][scene] if self.groupType in ["Filter", "Mixer", "EG", "LFO", "Misc Mod"] else 0

        # Knob Function Stuff
        difference = self.currentVirtualEncoder.updateEncoderCounter(int(rawEncoderCounter))
        if (difference != 0): self.currentVirtualEncoder.doKnobAction()

        # setting indecies and sub indecies
        if self.groupType == "EG":
            self.currentEncoderIndecies[scene][0] = Settings.globalIndecies["Scene-dependant"]["LFO"][scene]
            self.currentEncoderIndecies[scene][1] = Settings.globalIndecies["Scene-dependant"]["EG"][scene]
        self.currentEncoderIndex = self.currentEncoderIndecies[scene][0] # MODULO THIS THING there is an error when it goes past the index of the third one (I don't know what this means TwT)
        self.currentEncoderSubIndex = self.currentEncoderIndecies[scene][1]
        

        # Button Function stuff
        self.detectButtonPress(buttonPress)
        self.doButtonAction()

        # Assign new encoder only if it was changed
        length = len(self.virtualEncoders[scene][self.currentEncoderSubIndex])
        newEncoder = self.virtualEncoders[scene][self.currentEncoderSubIndex][self.currentEncoderIndex % length]
        isNewEncoder = self.currentVirtualEncoder != newEncoder
        if (isNewEncoder):
            self.currentVirtualEncoder = newEncoder
            self.currentVirtualEncoder.previousInputtedCounter = int(self.rawEncoderCounter)

        # Assign the value from surge to the new encoder only if the knob is set up to send OSC messages
        valueHasUpdated = Settings.OSCRECIEVEHISTORY != []
        encoderHasUpdated = isNewEncoder or valueHasUpdated
        if (encoderHasUpdated and self.currentVirtualEncoder.knobFunction == "OSC Send"):
            self.currentVirtualEncoder.recieveOSCAssignments(isNewEncoder)

        # print(Settings.globalIndecies["Scene"]["Current Value"], self.currentButtonFunctionValue, self.currentEncoderIndex)

    # Calculates the LED values for the current virtual encoder
    def calculateEncoderLEDValues(self):
        UsefulFunctions.calculateLEDBits(self)
        return self.currentVirtualEncoder.calculatedLEDBits


# A class that holds the higher level data that goes with one button
# Currently no need for a virtual button module because each button will only have one functionality
class ButtonModule():
    # Button Module Constructor Function
    def __init__(self, type: str, buttonSettings: list, LEDSettings: list, ledBitDepth=Settings.PWMSTEPS):
        
        self.groupType = type
        
        #LED data
        self.LEDSettings = LEDSettings
        self.bitDepth = ledBitDepth
        self.bitMask = ledBitDepth - 1
        self.bitCount = int(math.log2(ledBitDepth))

        # Button press function
        self.buttonBehavior = buttonSettings[0]
        self.buttonFunction = buttonSettings[1]
        self.buttonFunctionArgs = buttonSettings[2]

        self.currentButtonFunctionValue = 0
        self.buttonFunctionMaxValue = self.buttonFunctionArgs[0]

        # Button press data
        self.buttonPressHistory = [1] + [0] * 5
        self.buttonIsPressed = False
        self.buttonStatusHasChanged = False

    # Detects when the button is pressed and assigns the respective variable values
    def detectButtonPress(self, buttonPress):
        self.buttonPressHistory.pop(1)
        self.buttonPressHistory.append(int(buttonPress))
        self.buttonStatusHasChanged = True

        # The instant that button press history is switching all on
        if (numpy.prod(self.buttonPressHistory) != 0):
            self.buttonPressHistory[0] = 0
            self.buttonIsPressed = True
        # The instant that button press history is switching off
        elif sum(self.buttonPressHistory) == 0:
            self.buttonPressHistory[0] = 1
            self.buttonIsPressed = False
        # If button press history is in a steady state
        else:
            self.buttonStatusHasChanged = False

    # Handles the button functions
    def doButtonAction(self):
        buttonToggleOn = self.buttonIsPressed and self.buttonStatusHasChanged and self.buttonBehavior == "Toggled On"
        buttonWhilePressed = self.buttonIsPressed and self.buttonBehavior == "While On"
        buttonToggledBi = self.buttonStatusHasChanged and self.buttonBehavior == "Toggled Bi"

        if (buttonToggleOn or buttonWhilePressed or buttonToggledBi):
            UsefulFunctions.FUNCS[self.buttonFunction](self)

    # Handles all updates to the current button module
    def updateButton(self, buttonPress):
        self.detectButtonPress(buttonPress)
        self.doButtonAction()



    # Calculates the LED values for the single RGB LED assigned to the button
    def calculateButtonLEDValues(self):
        solidColorRGB = UsefulFunctions.HSVtoRGB(0.0, 0.0, 0.0)

        if self.groupType != "":
            scene = Settings.globalIndecies["Global"]["Scene"]["Current Value"] if self.buttonFunctionArgs[1] == "Scene-dependant" else "Index"
            currentIndex = Settings.globalIndecies[self.buttonFunctionArgs[1]][self.buttonFunctionArgs[2]][scene]
            settingsForCurrentIndex = self.LEDSettings[currentIndex]
            solidColorRGB = UsefulFunctions.HSVtoRGB(*list(settingsForCurrentIndex.values()))
    

        solidColorCalculatedBits = 0
        for i in range(3):
            solidColorCalculatedBits += int(
                solidColorRGB[2 - i] * self.bitMask) << (self.bitCount * i)

        return solidColorCalculatedBits
