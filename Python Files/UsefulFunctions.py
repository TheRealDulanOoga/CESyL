import Settings
import math

scalar = float


# Converts an HSV value to an RGB value
def HSVtoRGB(hue: scalar, saturation: scalar, value: scalar) -> tuple:
    if saturation:
        hue %= 1.0
        HUESECTOR = int(hue * 6.0) # This variable represents which sector of the HSV color wheel the hue falls into.
        FRACTIONALHUE = hue * 6.0 - HUESECTOR # This is the fractional part of the hue's position within its sector. It indicates how far the hue is between the two colors in the current sector.

        SHADE = value * (1.0 - saturation) # This value represents the RGB component that corresponds to the minimum value of the RGB triplet when saturation is applied
        IC1 = value * (1.0 - saturation * FRACTIONALHUE) # This is the RGB component that is on the edge of the color corresponding to the current hue.
        IC2 = value * (1.0 - saturation * (1.0 - FRACTIONALHUE)) # This value represents the other edge of the color component, It serves a similar purpose to Q, but for the other side of the transition between two colors in the current sector.

        match HUESECTOR:
            case 0: return (value, IC2, SHADE)
            case 1: return (IC1, value, SHADE)
            case 2: return (SHADE, value, IC2)
            case 3: return (SHADE, IC1, value)
            case 4: return (IC2, SHADE, value)
            case 5: return (value, SHADE, IC1)
            case _: return (value, value, value)
    return (value, value, value)

def IncrementValue(value, max):
    value += 1
    value %= max + 1
    return value

def IncrementButtonFunctionValue(self):
    self.currentButtonFunctionValue = IncrementValue(self.currentButtonFunctionValue, self.buttonFunctionMaxValue)
    return self.currentButtonFunctionValue

def SendOSCMessage(self):
    OSCDirectory = self.knobFunctionArgs[0]
    Settings.OSCCLIENT.send_message(OSCDirectory, self.clampedCounter * 1.0)
    
def IncrementEncoderCycle(self):
    scene = Settings.globalIndecies["Global"]["Scene"]["Current Value"] if self.sceneStatus == 2 else "a"

    newValue = IncrementValue(self.currentEncoderIndecies[scene][1], self.buttonFunctionMaxValue)
    # print(scene, self.currentEncoderSubIndex, self.currentEncoderIndex, self.currentEncoderIndecies)

    self.currentEncoderIndecies[scene][1] = newValue

def IncrementOSCValue(self):
    OSCDirectory = self.buttonFunctionArgs[1][0]
    IncrementButtonFunctionValue(self)
    # print(OSCDirectory, self.currentButtonFunctionValue)
    Settings.OSCCLIENT.send_message(OSCDirectory, self.currentButtonFunctionValue * 1.0)

def MixerMuteCycle(self):
    scene = Settings.globalIndecies["Global"]["Scene"]["Current Value"]
    currentMixerIndex = Settings.globalIndecies["Scene-dependant"]["Mixer"][scene]
    valueBeingChanged = Settings.globalIndecies["Scene-dependant"]["Mixer Mute & Solo"][scene][currentMixerIndex]
    valueBeingChanged = self.clampedCounter
    Settings.globalIndecies["Scene-dependant"]["Mixer Mute & Solo"][scene][currentMixerIndex] = valueBeingChanged

    OSCDirectory = self.knobFunctionArgs[0]
    match valueBeingChanged:
        case 0: 
            Settings.OSCCLIENT.send_message(OSCDirectory + "mute", 0.0)
            Settings.OSCCLIENT.send_message(OSCDirectory + "solo", 0.0)
            self.LEDHue = 0.97
        case 1: 
            Settings.OSCCLIENT.send_message(OSCDirectory + "mute", 1.0)
            Settings.OSCCLIENT.send_message(OSCDirectory + "solo", 0.0)
            self.LEDHue = 0.60
        case 2: 
            Settings.OSCCLIENT.send_message(OSCDirectory + "mute", 0.0)
            Settings.OSCCLIENT.send_message(OSCDirectory + "solo", 1.0)
            self.LEDHue = 0.05

def ButtonChangeGlobalIndex(self):
    valueBeingChanged = Settings.globalIndecies[self.buttonFunctionArgs[1]][self.buttonFunctionArgs[2]]
    location = Settings.globalIndecies["Global"]["Scene"]["Current Value"] if self.buttonFunctionArgs[1] == "Scene-dependant" else "Index"
    valueBeingChanged[location] = IncrementButtonFunctionValue(self)

    if (self.buttonFunctionArgs[1] == "Global"):
        valueBeingChanged["Current Value"] = list(valueBeingChanged.values())[1][valueBeingChanged["Index"]]
        # print("global")
    
    Settings.globalIndecies[self.buttonFunctionArgs[1]][self.buttonFunctionArgs[2]] = valueBeingChanged
    print(valueBeingChanged)

def KnobChangeGlobalIndex(self):
    valueBeingChanged = Settings.globalIndecies[self.knobFunctionArgs[0]][self.knobFunctionArgs[5]]
    location = Settings.globalIndecies["Global"]["Scene"]["Current Value"] if self.knobFunctionArgs[0] == "Scene-dependant" else "Index"
    valueBeingChanged[location] = int(self.clampedCounter)

    if (self.knobFunctionArgs[0] == "Global"):
        if (valueBeingChanged["Type"] == "str"):
            valueBeingChanged["Current Value"] = list(valueBeingChanged.values())[1][valueBeingChanged["Index"]]
        # print("global")

    if self.knobFunctionArgs[1] == Settings.globalIndecies["Global"]["Scene"]["Current Value"]:
        Settings.globalIndecies[self.knobFunctionArgs[0]][self.knobFunctionArgs[5]] = valueBeingChanged
        print(valueBeingChanged)

def Modulation(self):
    type = self.buttonFunctionArgs[0]
    scene = Settings.globalIndecies["Global"]["Scene"]["Current Value"]
    if type == "Macro":
        scene = "a"
        index = self.buttonFunctionArgs[1]
    else:
        index = Settings.globalIndecies["Scene-dependant"][type][scene]

    currentValue = Settings.globalIndecies["Global"]["Modulation"]["Current Value"]
    newValue = [True, type, scene, index]
    if set(currentValue) == set(newValue):
        newValue = [False]
    elif Settings.OSCRECIEVEHISTORY["ModSource"][1] < 2:
        Settings.OSCRECIEVEHISTORY["ModSource"][1] += 1
        Settings.OSCRECIEVEHISTORY["ModSource"][0] = 0
        Settings.OSCRECIEVEHISTORY["Mod"] = [[]]

    print(newValue)
    
    Settings.globalIndecies["Global"]["Modulation"]["Current Value"] = newValue
    Settings.MODSTATUSCHANGE = [True, type, index]  

def DummyFunction(*args):
    pass

FUNCS = {
    "OSC Send": SendOSCMessage,
    "Increment Encoder Cycle": IncrementEncoderCycle,
    "OSC Increment": IncrementOSCValue,
    "Button Index Change": ButtonChangeGlobalIndex,
    "Knob Index Change": KnobChangeGlobalIndex,
    "Mute Cycle": MixerMuteCycle,
    "Modulation": Modulation,
    "None": DummyFunction
}

# Calculate the bits associated with each LED on this encoder (12 LEDs total; 4 * RGB)
def LEDLeftStack(self, counter, hue, saturation, lightness, dimness):
    CVE = self.currentVirtualEncoder
    stepsPerLED = CVE.steps / CVE.ledCount

    brightestValue = ((1.0 - dimness) * lightness) + dimness
    middleBrightnessValue = ((counter % stepsPerLED) / stepsPerLED) * (brightestValue - dimness) + dimness

    solidColor = HSVtoRGB(hue, saturation, brightestValue)
    middleColor = HSVtoRGB(hue, saturation, middleBrightnessValue)
    dimColor = HSVtoRGB(hue, saturation, dimness)

    solidLEDsCount = math.floor(counter / stepsPerLED)
    solidColorCalculatedBits = 0
    middleColorCalculatedBits = 0
    dimColorCalculatedBits = 0
    appendCalculatedBits = 0

    for i in range(3):
        solidColorCalculatedBits += int(solidColor[2 - i] * CVE.bitMask) << (CVE.bitCount * i)
        middleColorCalculatedBits += int(middleColor[2 - i] * CVE.bitMask) << (CVE.bitCount * i)
        dimColorCalculatedBits += int(dimColor[2 - i] * CVE.bitMask) << (CVE.bitCount * i)

    for i in range(CVE.ledCount):
        appendCalculatedBits = solidColorCalculatedBits if (i < solidLEDsCount) else middleColorCalculatedBits if (i == solidLEDsCount) else dimColorCalculatedBits
        CVE.calculatedLEDBits[i] = appendCalculatedBits
    
    self.currentVirtualEncoder = CVE

def LEDCenterStack(self, counter, hue, saturation, lightness, dimness):
    CVE = self.currentVirtualEncoder
    stepsPerLED = CVE.steps / CVE.ledCount * 2

    if counter < 0: middleBrightnessValue = stepsPerLED - (counter - 1) % stepsPerLED
    else: middleBrightnessValue = counter % stepsPerLED
    brightestValue = ((1.0 - dimness) * lightness) + dimness
    middleBrightnessValue = (middleBrightnessValue / stepsPerLED) * (brightestValue - dimness) + dimness

    solidColor = HSVtoRGB(hue, saturation, brightestValue)
    middleColor = HSVtoRGB(hue, saturation, middleBrightnessValue)
    dimColor = HSVtoRGB(hue, saturation, dimness)

    solidLEDsCount = math.floor(abs(counter / stepsPerLED))
    solidColorCalculatedBits = 0
    middleColorCalculatedBits = 0
    dimColorCalculatedBits = 0
    appendCalculatedBits = 0

    for i in range(3):
        solidColorCalculatedBits += int(solidColor[2 - i] * CVE.bitMask) << (CVE.bitCount * i)
        middleColorCalculatedBits += int(middleColor[2 - i] * CVE.bitMask) << (CVE.bitCount * i)
        dimColorCalculatedBits += int(dimColor[2 - i] * CVE.bitMask) << (CVE.bitCount * i)

    for i in range(CVE.ledCount):
        index = i
        if counter > 0 and i >= 2:
            appendCalculatedBits = solidColorCalculatedBits if (i - 2 < solidLEDsCount) else middleColorCalculatedBits if (i - 2 == solidLEDsCount) else dimColorCalculatedBits
        elif counter < 0 and i < 2:
            index = 1 - i
            appendCalculatedBits = solidColorCalculatedBits if (i < solidLEDsCount) else middleColorCalculatedBits if (i == solidLEDsCount) else dimColorCalculatedBits
        else:
            appendCalculatedBits = dimColorCalculatedBits
        CVE.calculatedLEDBits[index] = appendCalculatedBits
    
    self.currentVirtualEncoder = CVE

def LEDSolidColor(self, storeValue, hue, saturation, lightness, *args):
    CVE = self.currentVirtualEncoder
    solidColor = HSVtoRGB(hue, saturation, lightness)
    calculatedBits = 0

    for i in range(3): calculatedBits += int(solidColor[2 - i] * CVE.bitMask) << (CVE.bitCount * i)
    for i in range(CVE.ledCount): CVE.calculatedLEDBits[i] = calculatedBits

    if storeValue: self.currentVirtualEncoder = CVE

    return CVE.calculatedLEDBits

def LEDBinaryCount(self, counter, hue, saturation, lightness, dimness):
    CVE = self.currentVirtualEncoder

    maxCount = 16
    counter /= CVE.ledCount
    hue -= 0.1 * int(counter / maxCount)
    counter = int(counter % maxCount)

    brightestValue = ((1.0 - dimness) * lightness) + dimness
    solidColor = HSVtoRGB(hue, saturation, brightestValue)
    dimColor = HSVtoRGB(hue, saturation, dimness)

    solidColorCalculatedBits = 0
    dimColorCalculatedBits = 0
    mask = 0

    for i in range(3):
        solidColorCalculatedBits += int(solidColor[2 - i] * CVE.bitMask) << (CVE.bitCount * i)
        dimColorCalculatedBits += int(dimColor[2 - i] * CVE.bitMask) << (CVE.bitCount * i)
    
    maskLUT = [
        0b1000, #0
        0b0100,
        0b0010,
        0b0001,
        0b1001,
        0b1010, #5
        0b1100,
        0b0110,
        0b0101,
        0b0011,
        0b0111, #10
        0b1011,
        0b1101,
        0b1110,
        0b1111,
        0b0000 #15
    ]

    mask = maskLUT[counter]

    for i in range(4):
        CVE.calculatedLEDBits[3 - i] = solidColorCalculatedBits if ((mask >> i) & 1 == 1) else dimColorCalculatedBits
    
    self.currentVirtualEncoder = CVE    


LEDMODES = {
    "Left Stack": LEDLeftStack,
    "Center Stack": LEDCenterStack,
    "Solid": LEDSolidColor,
    "Binary": LEDBinaryCount
    # "NORMAL ROTORY STACK",
    # "RGB ROTORY STACK",
    # "CENTER NORMAL STACK",
    # "CENTER RGB STACK",
    # "COLOR SHIFT",
    # "GRADIENT STACK"
}