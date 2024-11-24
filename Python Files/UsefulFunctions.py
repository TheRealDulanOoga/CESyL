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
    valueBeingChanged = Settings.globalIndecies[self.knobFunctionArgs[0]][self.knobFunctionArgs[1]]
    location = Settings.globalIndecies["Global"]["Scene"]["Current Value"] if self.knobFunctionArgs[0] == "Scene-dependant" else "Index"
    valueBeingChanged[location] = int(self.clampedCounter)

    if (self.knobFunctionArgs[0] == "Global"):
        valueBeingChanged["Current Value"] = list(valueBeingChanged.values())[1][valueBeingChanged["Index"]]
        # print("global")
    
    Settings.globalIndecies[self.knobFunctionArgs[0]][self.knobFunctionArgs[1]] = valueBeingChanged
    print(valueBeingChanged)

def DummyFunction(*args):
    pass

FUNCS = {
    "OSC Send": SendOSCMessage,
    "Increment Encoder Cycle": IncrementEncoderCycle,
    "OSC Increment": IncrementOSCValue,
    "Button Index Change": ButtonChangeGlobalIndex,
    "Knob Index Change": KnobChangeGlobalIndex,
    "Mute Cycle": MixerMuteCycle,
    "None": DummyFunction
}

# Calculate the bits associated with each LED on this encoder (12 LEDs total; 4 * RGB)
def calculateLEDBits(self):
    CVE = self.currentVirtualEncoder
    stepsPerLED = CVE.steps / CVE.ledCount

    # All solid LEDs
    solidColorRGB = HSVtoRGB(CVE.LEDHue, 1.0, 1.0)
    solidLEDsCount = math.floor(CVE.counter / stepsPerLED)
    solidColorCalculatedBits = 0

    for i in range(3):
        solidColorCalculatedBits += int(
            solidColorRGB[2 - i] * CVE.bitMask) << (CVE.bitCount * i)

    for i in range(solidLEDsCount):
        CVE.calculatedLEDBits[i] = solidColorCalculatedBits

    # Single LED with variable brightness
    appendRGB = 0
    middleLEDBrightness = (CVE.counter % stepsPerLED) / stepsPerLED
    middleLEDColorValues = HSVtoRGB(CVE.LEDHue, 1.0, middleLEDBrightness)

    for i in range(3):
        appendRGB += int(
            middleLEDColorValues[2 - i] * CVE.bitMask) << (CVE.bitCount * i)

    # All completely dark LEDs
    for i in range(solidLEDsCount, CVE.ledCount):
        CVE.calculatedLEDBits[i] = appendRGB
        appendRGB = 0
    
    self.currentVirtualEncoder = CVE

LEDMODES = {
    "Follow Knob": calculateLEDBits,
    # "NORMAL ROTORY STACK",
    # "RGB ROTORY STACK",
    # "CENTER NORMAL STACK",
    # "CENTER RGB STACK",
    # "COLOR SHIFT",
    # "GRADIENT STACK"
}