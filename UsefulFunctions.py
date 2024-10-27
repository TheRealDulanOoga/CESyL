import Settings

scalar = float


# Converts an HSV value to an RGB value
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
    return (v, v, v)

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
    print(scene, self.currentEncoderSubIndex, self.currentEncoderIndex, self.currentEncoderIndecies)

    self.currentEncoderIndecies[scene][1] = newValue


def IncrementOSCValue(self):
    OSCDirectory = self.buttonFunctionArgs[1][0]
    IncrementButtonFunctionValue(self)
    # print(OSCDirectory, self.currentButtonFunctionValue)
    Settings.OSCCLIENT.send_message(OSCDirectory, self.currentButtonFunctionValue * 1.0)

def ChangeGlobalIndex(self):
    valueBeingChanged = Settings.globalIndecies[self.buttonFunctionArgs[1]][self.buttonFunctionArgs[2]]
    location = Settings.globalIndecies["Global"]["Scene"]["Current Value"] if self.buttonFunctionArgs[1] == "Scene-dependant" else "Index"
    valueBeingChanged[location] = IncrementButtonFunctionValue(self)

    if (self.buttonFunctionArgs[1] == "Global"):
        valueBeingChanged["Current Value"] = list(valueBeingChanged.values())[1][valueBeingChanged["Index"]]
        print("global")
    
    Settings.globalIndecies[self.buttonFunctionArgs[1]][self.buttonFunctionArgs[2]] = valueBeingChanged

def DummyFunction(*args):
    pass

FUNCS = {
    "OSC Send": SendOSCMessage,
    "Increment Encoder Cycle": IncrementEncoderCycle,
    "OSC Increment": IncrementOSCValue,
    "Index Change": ChangeGlobalIndex,
    "None": DummyFunction
}