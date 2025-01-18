import math
import time
import numpy
import UsefulFunctions
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder
import Settings

# A virtual object that represents a singular setting that one encoder will change
# There will be multiple of these assigned to a single encoder "module" (one rotory encoder / purple PCB)
class VirtualEncoder():
    # Virtual Encoder Constructor Function
    def __init__(self, knobFunction : callable, knobFunctionArgs : list, hue: str = "Color1",  steps=32, maxValue=1.0, minValue=0.0, ledBehavior="Left Stack", ledBitDepth=Settings.PWMSTEPS, ledCount=Settings.LEDCOUNT):

        if len(knobFunctionArgs) > 1 and "pitch" in knobFunctionArgs[0]:
            print(knobFunctionArgs, hue, steps, maxValue, minValue, ledBehavior)
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
        self.LEDHue = Settings.COLORLUT[hue]
        self.calculatedLEDBits = [0, 0, 0, 0]

        self.isModulatable = len(self.knobFunctionArgs) > 3 and self.knobFunctionArgs[4] == "YM"
        if self.isModulatable:
            self.modClampedCounter = 0
            self.modulationSources = {
                "LFO": {"a": [], "b": []},
                "Misc Mod": {"a": [], "b": []},
                "Macro": {"a": []}
            }
            for _ in range(Settings.LFOMODSOURCES):
                self.modulationSources["LFO"]["a"].append(0)
                self.modulationSources["LFO"]["b"].append(0)
            for _ in range(Settings.OTHERMODSOURCES):
                self.modulationSources["Misc Mod"]["a"].append(0)
                self.modulationSources["Misc Mod"]["b"].append(0)
            for _ in range(Settings.MACROMODSOURCES):
                self.modulationSources["Macro"]["a"].append(0)

            # print(self.modulationSources)

    # Update the value associated with the rotory encoder using data from Serial
    def updateEncoderCounter(self, setValue):
        self.currentInputtedCounter = setValue
        difference = self.currentInputtedCounter - self.previousInputtedCounter

        modInfo = Settings.globalIndecies["Global"]["Modulation"]["Current Value"]
        if self.isModulatable:
            type, scene, index = modInfo[1:]

            counter = self.modulationSources[type][scene][index]
            counter += difference / self.steps
            counter = max(min(counter, 1), -1)

            self.modClampedCounter = self.modulationSources[type][scene][index] = counter
        else:
            self.counter += difference
            self.counter = max(min(self.counter, self.steps), 0)

            valueRange = self.maxValue - self.minValue
            normalizedCounter = self.counter / self.steps
            self.clampedCounter = (normalizedCounter * valueRange) + self.minValue

        self.previousInputtedCounter = self.currentInputtedCounter

        return difference

    # Update the new counter based on a clamped value
    def assignChangedCounter(self, clampedValue):
        valueRange = self.maxValue - self.minValue
        normalizedCounter = (clampedValue - self.minValue) / valueRange
        return normalizedCounter * self.steps

    # Grabs the value(s) of encoder(s) from surge and assigns those values when one of them is updated
    def updateAllKnobValues(self, actions):
        paramUpdateData = []
        modUpdateData = []
        singleParamFound = False
        singleModFound = False
        itemIndex = 0
        print("\n- - - - - - - - - - - - - -\n")

        # Check for changes in param values
        if "Patch" in actions: # if the patch was recently updated, update all parameters
            print("Patch", Settings.OSCRECIEVEHISTORY["Patch"][0])
            paramUpdateData, itemIndex = self.fetchSurgeParamValues()
            Settings.OSCRECIEVEHISTORY["Patch"][0] += 1
        elif "Param" in actions: # update one param
            print("Param")
            for item in Settings.OSCRECIEVEHISTORY["Param"]:
                if self.knobFunctionArgs[0] in item[0][0]:
                    paramUpdateData = item
                    singleParamFound = True
                    break
        elif "Knob" in actions: # request one param
            print("Knob")
            paramUpdateData, itemIndex = self.fetchSurgeParamValues()


        # Update the value itself if there is one to update
        if paramUpdateData != []:
            finalTermInAddress = self.knobFunctionArgs[0].rindex("/")
            if "param" in self.knobFunctionArgs[0][finalTermInAddress:] and "/doc" in paramUpdateData[-1][0]:
                docReference = paramUpdateData[-1]
                if docReference[2] == "float":
                    self.minValue = 0
                    self.maxValue = 1
                    self.steps = 32 * 4
                    self.knobFunctionArgs[4] = "YM"
                elif docReference[2] == "int":
                    self.minValue = int(docReference[3])
                    self.maxValue = int(docReference[4])
                    self.steps = (self.maxValue - self.minValue) * 4
                    self.knobFunctionArgs[4] = "NM"

            if "/doc" not in paramUpdateData[itemIndex][0]:
                self.counter = self.assignChangedCounter(paramUpdateData[itemIndex][1])
            print(paramUpdateData[itemIndex])
            print(self.counter)

            Settings.OSCRECIEVEHISTORY["Param"].append([])
            
        # Check for changes in mod values
        if "ModSource" in actions: # request one mod value after mod source is updated
            print("ModSource")
            modUpdateData = self.fetchSurgeModValues()
            Settings.OSCRECIEVEHISTORY["ModSource"][0] += 1
        elif "ModValue" in actions: # update one mod value
            print("ModValue")
            for item in Settings.OSCRECIEVEHISTORY["Mod"]:
                print(item[0][1], self.knobFunctionArgs[0])
                if self.knobFunctionArgs[0] in item[0][1]:
                    modUpdateData = item
                    singleModFound = True
                    break
        
        # Assign new mod data to the counter
        if modUpdateData != []:
            modInfo = Settings.globalIndecies["Global"]["Modulation"]["Current Value"]
            type, scene, index = modInfo[1:]

            self.modulationSources[type][scene][index] = modUpdateData[0][2]
            print("MOD", modUpdateData[0], self.modulationSources[type][scene][index])
            print(self.modClampedCounter)
        
            Settings.OSCRECIEVEHISTORY["Mod"].append([])


        # Reset any values if needed
        if Settings.OSCRECIEVEHISTORY["Patch"][0] >= Settings.ENCODERSCOUNT:
            Settings.OSCRECIEVEHISTORY["Patch"][0] = -1
            Settings.OSCRECIEVEHISTORY["Patch"][1] -= 1
            Settings.OSCRECIEVEHISTORY["Param"] = [[]]
        elif singleParamFound or ("Knob" in actions and Settings.OSCRECIEVEHISTORY["Patch"][0] == -1):
            Settings.OSCRECIEVEHISTORY["Param"] = [[]]

        if Settings.OSCRECIEVEHISTORY["ModSource"][0] >= Settings.ENCODERSCOUNT:
            Settings.OSCRECIEVEHISTORY["ModSource"][0] = -1
            Settings.OSCRECIEVEHISTORY["ModSource"][1] -= 1
            Settings.OSCRECIEVEHISTORY["Mod"] = [[]]
        elif singleModFound or ("ModValue" in actions and Settings.OSCRECIEVEHISTORY["ModSource"][0] == -1):
            Settings.OSCRECIEVEHISTORY["Mod"] = [[]]
        
        if Settings.OSCRECIEVEHISTORY["Patch"][0] == -1 and Settings.OSCRECIEVEHISTORY["Patch"][1] > 0:
            Settings.OSCRECIEVEHISTORY["Patch"][0] = 0
        if Settings.OSCRECIEVEHISTORY["ModSource"][0] == -1 and Settings.OSCRECIEVEHISTORY["ModSource"][1] > 0:
            Settings.OSCRECIEVEHISTORY["ModSource"][0] = 0

        print("Patch", Settings.OSCRECIEVEHISTORY["Patch"])
        print("Mod", Settings.OSCRECIEVEHISTORY["ModSource"])

    def fetchSurgeParamValues(self):
        # Create OSC address to be used for the query
        queryMessage = "/q" + self.knobFunctionArgs[0]
        isExtendedValue = "+" in queryMessage
        message = queryMessage[:queryMessage.rindex("/")] if isExtendedValue else queryMessage

        sleepTime = 0.01
        oldTime = time.time()
        print("\nUpdating Param Values . . .", message)
        Settings.OSCCLIENT.send_message(message, 0)
        while len(Settings.OSCRECIEVEHISTORY["Param"][-1]) <= 0 and time.time() - oldTime < sleepTime: pass
            # print(int(100 - (time.time() - oldTime) * (100 / sleepTime)))
        
        time.sleep(0.0001)
  
        if len(Settings.OSCRECIEVEHISTORY["Param"][-1]) <= 0: return [], 0

        paramData = Settings.OSCRECIEVEHISTORY["Param"][-1]
        
        # If it is a special OSC value with extended capabilities then it needs special treatment (take the base value and then find it from that query instead)
        itemIndex = 0
        if isExtendedValue:
            for item in paramData:
                if queryMessage in "/q" + item[0]:
                    break
                itemIndex += 1

        return paramData, itemIndex
    
    def fetchSurgeModValues(self):
        modInfo = Settings.globalIndecies["Global"]["Modulation"]["Current Value"]
        type, scene, index = (modInfo[1:])
        modSourcePaths = Settings.ALLMODULATIONPATHS[type]

        match type:
            case "Misc Mod": modPath = modSourcePaths[index].replace("<s>", scene)
            case "Macro": modPath = modSourcePaths.replace("<n>", str(index + 1))
            case "LFO": modPath = modSourcePaths[int(index / 6)].replace("<n>", str(index % 6 + 1)).replace("<s>", scene) + "/0"
            case _: return

        # Create OSC address to be used for the query
        modPath = "/q" + modPath
        paramPath = self.knobFunctionArgs[0]

        # Send the message, await response, and update the current encoder accordingly
        sleepTime = 0.001
        print("\nUpdating Mod Values . . .", modPath, paramPath)
        oldTime = time.time()
        Settings.OSCCLIENT.send_message(modPath, paramPath)
        while len(Settings.OSCRECIEVEHISTORY["Mod"][-1]) <= 0 and time.time() - oldTime < sleepTime : pass

        modData = Settings.OSCRECIEVEHISTORY["Mod"][-1]
        return modData

    # Executes the assigned function for when the knob turns
    def doKnobAction(self):
        modInfo = Settings.globalIndecies["Global"]["Modulation"]["Current Value"]
        isModSource = len(self.knobFunctionArgs) > 0 and ("/macro" in self.knobFunctionArgs[0] or self.knobFunctionArgs[-1] == "LFO" or self.knobFunctionArgs[-1] == "Misc Mod")
        isModulatable = self.isModulatable

        if isModSource or not isModulatable:
            UsefulFunctions.FUNCS[self.knobFunction](self)
        elif isModulatable:
            type, scene, index = (modInfo[1:])
            modSourcePaths = Settings.ALLMODULATIONPATHS[type]

            match type:
                case "Misc Mod": modPath = modSourcePaths[index].replace("<s>", scene)
                case "Macro": modPath = modSourcePaths.replace("<n>", str(index + 1))
                case "LFO": modPath = modSourcePaths[int(index / 6)].replace("<n>", str(index % 6 + 1)).replace("<s>", scene)
                case _: return

            # print(message, self.knobFunctionArgs[0], self.clampedCounter * 1.0)
            bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
            message = osc_message_builder.OscMessageBuilder(address=modPath)
            message.add_arg(self.knobFunctionArgs[0])
            message.add_arg(self.modClampedCounter * 1.0)

            bundle.add_content(message.build())
            bundle = bundle.build()

            Settings.OSCCLIENT.send(bundle)



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

            for knobSettingsList in virtualEncoderSettings:
                knobSettingsList = list(knobSettingsList)
                knobFunctionArgs = knobSettingsList[1]

                sceneValue = knobFunctionArgs[1] if self.sceneStatus == 2 else "a"
                encoderGroupIndex = knobFunctionArgs[2]
                encoderSubIndex = knobFunctionArgs[3]

                ledBehavior = "Left Stack"
                if isinstance(knobSettingsList[-1], str) and any([item in knobSettingsList[-1] for item in UsefulFunctions.LEDMODES.keys()]):
                    ledBehavior = knobSettingsList[-1]
                    del knobSettingsList[-1]

                knobFunctionArgs[0] = knobFunctionArgs[0].replace("<s>", str(sceneValue)).replace("<n>", str(encoderSubIndex + 1))
                
                newEncoder = VirtualEncoder(*knobSettingsList, ledBehavior=ledBehavior, ledCount=ledCount, ledBitDepth=ledBitDepth)

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

        activateButton = buttonToggleOn or buttonWhilePressed or buttonToggledBi
        modInfo = Settings.globalIndecies["Global"]["Modulation"]["Current Value"]
        knobArgs = self.currentVirtualEncoder.knobFunctionArgs

        isModSource = len(knobArgs) > 0 and ("/macro" in knobArgs[0] or knobArgs[-1] == "LFO" or knobArgs[-1] == "Misc Mod")
        isModulatable = self.currentVirtualEncoder.isModulatable

        if activateButton and (not isModulatable or isModSource):
            UsefulFunctions.FUNCS[self.buttonFunction](self)
        elif activateButton and isModulatable:
            type, scene, index = (modInfo[1:])
            self.currentVirtualEncoder.modClampedCounter = 0
            self.currentVirtualEncoder.modulationSources[type][scene][index] = 0

            modSourcePaths = Settings.ALLMODULATIONPATHS[type]

            match type:
                case "Misc Mod": modPath = modSourcePaths[index].replace("<s>", scene)
                case "Macro": modPath = modSourcePaths.replace("<n>", str(index + 1))
                case "LFO": modPath = modSourcePaths[int(index / 6)].replace("<n>", str(index % 6 + 1)).replace("<s>", scene)
                case _: return

            # print(message, self.knobFunctionArgs[0], self.clampedCounter * 1.0)
            bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
            message = osc_message_builder.OscMessageBuilder(address=modPath)
            message.add_arg(self.currentVirtualEncoder.knobFunctionArgs[0])
            message.add_arg(self.currentVirtualEncoder.modClampedCounter * 1.0)

            bundle.add_content(message.build())
            bundle = bundle.build()

            Settings.OSCCLIENT.send(bundle)

    # Handles all updates to the status of the current virtual encoder and the encoder module
    def updateCurrentEncoder(self, buttonPress, rawEncoderCounter):
        # Set up a few preliminary variables
        self.rawEncoderCounter = rawEncoderCounter

        scene = Settings.globalIndecies["Global"]["Scene"]["Current Value"] if self.sceneStatus == 2 else "a"

        if self.groupType in ["Filter", "Mixer", "EG", "LFO", "Misc Mod", "VCO"]:
            self.currentEncoderIndecies[scene][0] = Settings.globalIndecies["Scene-dependant"][self.groupType][scene]
        elif self.groupType in ["FX"]:
            self.currentEncoderIndecies[scene][0] = Settings.globalIndecies["Global"]["FX"]["Index"]
        else: 
            self.currentEncoderIndecies[scene][0] = 0

        # Knob Function Stuff
        knobArgs = self.currentVirtualEncoder.knobFunctionArgs

        isModulationGroup = Settings.MODSTATUSCHANGE[1] == self.groupType
        isCorrectMacroIndex = len(knobArgs) > 0 and Settings.MODSTATUSCHANGE[2] + 1 == knobArgs[0][-1]
        if isModulationGroup and (isCorrectMacroIndex or self.groupType != "Macro"):
            Settings.MODSTATUSCHANGE = [False, 0, 0]

        self.determineModulatability()
        difference = self.currentVirtualEncoder.updateEncoderCounter(int(rawEncoderCounter))
        if (difference != 0): self.currentVirtualEncoder.doKnobAction()

        # setting indecies and sub indecies
        if self.groupType == "EG":
            self.currentEncoderIndecies[scene][0] = Settings.globalIndecies["Scene-dependant"]["LFO"][scene]
            self.currentEncoderIndecies[scene][1] = Settings.globalIndecies["Scene-dependant"]["EG"][scene]
        self.currentEncoderIndex = self.currentEncoderIndecies[scene][0] # MODULO THIS THING there is an error when it goes past the index of the third one (I don't know what this means TwT)
        self.currentEncoderSubIndex = self.currentEncoderIndecies[scene][1]

        # self.determineModulatability()
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

        # Check if it is a contextual parameter that should be updated
        knobArgs = self.currentVirtualEncoder.knobFunctionArgs
        isOscillator = isFX = isTypeModifier = isContextualParam = False

        if len(knobArgs) > 0:
            isOscillator = "/osc" in knobArgs[0]
            isFX = "/fx" in knobArgs[0]
            isTypeModifier = "/type" in knobArgs[0]

            if isOscillator and isTypeModifier:
                Settings.VCOCONTEXTUAL = self.currentVirtualEncoder.clampedCounter != Settings.LASTOSCILLATORTYPE
                Settings.LASTOSCILLATORTYPE = self.currentVirtualEncoder.clampedCounter
            if isFX and isTypeModifier:
                Settings.FXCONTEXTUAL = self.currentVirtualEncoder.clampedCounter != Settings.LASTFXTYPE
                Settings.LASTFXTYPE = self.currentVirtualEncoder.clampedCounter
            if "/param" in knobArgs[0]:
                finalTermInAddress = knobArgs[0].rindex("/")
                isContextualParam = "param" in knobArgs[0][finalTermInAddress:]

        # Check if the knob itself needs to be updated
        # self.determineModulatability()
        valueHasUpdated = Settings.OSCRECIEVEHISTORY["Param"][-1] != []
        valueHasUpdated = valueHasUpdated and len(knobArgs) > 0 and knobArgs[0] in Settings.OSCRECIEVEHISTORY["Param"][-1][0][0]
        isContextualEncoder = (Settings.VCOCONTEXTUAL and isContextualParam and isOscillator) or (Settings.FXCONTEXTUAL and isContextualParam and isFX)

        modValueHasUpdated = Settings.OSCRECIEVEHISTORY["Mod"][-1] != []
        modValueHasUpdated = modValueHasUpdated and len(knobArgs) > 0 and knobArgs[0] in Settings.OSCRECIEVEHISTORY["Mod"][-1][0][1]
        modValueHasUpdated = modValueHasUpdated and Settings.globalIndecies["Global"]["Modulation"]["Current Value"][0] == True

        newPatch = Settings.OSCRECIEVEHISTORY["Patch"][0] >= 0
        newModSource = Settings.OSCRECIEVEHISTORY["ModSource"][0] >= 0 and self.currentVirtualEncoder.isModulatable

        # Curate which events to trigger for differrent parts of the code to fetch surge values
        actions = []
        if newPatch:
            actions.append("Patch")
        if valueHasUpdated:
            actions.append("Param")
        if isNewEncoder or isContextualEncoder:
            actions.append("Knob")
        if newModSource:
            actions.append("ModSource")
        if modValueHasUpdated and False:
            actions.append("ModValue")

        if self.currentVirtualEncoder.knobFunction == "OSC Send" and actions != []:
            self.currentVirtualEncoder.updateAllKnobValues(actions)

    def determineModulatability(self):
        modInfo = Settings.globalIndecies["Global"]["Modulation"]["Current Value"]
        knobArgs = self.currentVirtualEncoder.knobFunctionArgs

        if modInfo[0] == False or len(knobArgs) < 4:
            self.currentVirtualEncoder.isModulatable = False
            return
    
        type, scene, index = (modInfo[1:])

        isModulatable = knobArgs[4] == "YM"
        isLFOModSource = type == "LFO"
        isVLFOModSource = isLFOModSource and index < 6
        isSLFOModSource = isLFOModSource and index >= 6
        isEGSource = type == "Misc Mod" and index > 10
        isLimitedMiscSource = type == "Misc Mod" and any(index == i for i in [0, 1, 2, 9, 10])

        vlfoSource = str(scene) + "/vlfo/" + str(index + 1)
        slfoSource = str(scene) + "/slfo/" + str(index - 5)

        scopeConflict = (isLimitedMiscSource or isEGSource or isVLFOModSource) and any(name in knobArgs[0][5:] for name in ["/fx/", "/highpass", "/send", "/vel_to_gain"])
        EGScopeConflict = isEGSource and any(name in knobArgs[0] for name in ["/feg/", "/aeg/", "/vel_to_gain"])
        LFOSelfSetting = (isVLFOModSource and vlfoSource in knobArgs[0]) or (isSLFOModSource and slfoSource in knobArgs[0])
        sceneDisagreement = type != "Macro" and "/" + scene + "/" not in knobArgs[0]

        self.currentVirtualEncoder.isModulatable = isModulatable and not (scopeConflict or EGScopeConflict or LFOSelfSetting or sceneDisagreement)

    # Calculates the LED values for the current virtual encoder
    def calculateEncoderLEDValues(self):
        CVE = self.currentVirtualEncoder
        knobArgs = CVE.knobFunctionArgs
        modValues = Settings.globalIndecies["Global"]["Modulation"]["Current Value"]
        inModMode, type, __Scene__, index = modValues if modValues[0] == True else [False, "None", "a", 0]

        if len(knobArgs) < 1: return CVE.calculatedLEDBits

        changeInModSource = Settings.OSCRECIEVEHISTORY["ModSource"][0] >= 0
        modKnob = len(knobArgs) > 5
        modTypeMatch = modKnob and type == knobArgs[5]
        if modTypeMatch and type == "Macro":
            macroIndexMatch = self.buttonFunctionArgs[1] == index
        else:
            macroIndexMatch = True

        now = time.time()
        timeRange = 75
        timer = math.floor(now * 100) % (timeRange * 2)
        if timer > timeRange:
            timerCounter = (timeRange * 2 - timer) / timeRange
        else:
            timerCounter = timer / timeRange

        mode = CVE.ledBehavior
        counter = CVE.counter
        hue = CVE.LEDHue
        lightness = 1.0
        dimness = 0.1

        if changeInModSource: return CVE.calculatedLEDBits
        elif mode == "Center Stack":
            extremeValue = (CVE.maxValue - CVE.minValue) / 2
            counter = CVE.clampedCounter
            if CVE.minValue >= 0: counter -= extremeValue
            counter *=  CVE.steps / extremeValue
        elif CVE.isModulatable:
            mode = "Center Stack"
            counter = CVE.modClampedCounter * CVE.steps
            hue = 0.35
            lightness = timerCounter

        if inModMode and modTypeMatch and macroIndexMatch:
            lightness = timerCounter
            dimness = timerCounter * 0.2 + 0.05
            
        
        UsefulFunctions.LEDMODES[mode](self, counter, hue, 1.0, lightness, dimness)

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
            hue, saturation, lightness = list(settingsForCurrentIndex.values())
            solidColorRGB = UsefulFunctions.HSVtoRGB(Settings.COLORLUT[hue], saturation, lightness)
    

        solidColorCalculatedBits = 0
        for i in range(3):
            solidColorCalculatedBits += int(
                solidColorRGB[2 - i] * self.bitMask) << (self.bitCount * i)

        return solidColorCalculatedBits
