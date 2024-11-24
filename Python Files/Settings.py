global globalIndecies
global sceneSpecificIndecies

global PWMSTEPS
global LEDCOUNT
global ENCODERSCOUNT
global BUTTONSCOUNT

global OSCRECIEVEHISTORY
global HISTORYSIZE

global OSCCLIENT

global LASTOSCILLATORTYPE
global LASTFXTYPE
global VCOCONTEXTUAL
global FXCONTEXTUAL

PWMSTEPS = pow(2, 5)
LEDCOUNT = 4
ENCODERSCOUNT = 0
BUTTONSCOUNT = 0
OSCRECIEVEHISTORY = [[]]
HISTORYSIZE = 0

LASTOSCILLATORTYPE = 0
LASTFXTYPE = 0
VCOCONTEXTUAL = False
FXCONTEXTUAL = False

globalIndecies = {
    "Global": {
        "Scene": {"Index": 0, "Values": ["a", "b"], "Current Value": "a", "Type": "str"},
        "FX":    {"Index": 0,                                             "Type": "int"}
    },
    "Scene-dependant": {
        "Filter":            {"a": 0,                  "b": 0},
        "EG":                {"a": 0,                  "b": 0},
        "Mixer":             {"a": 0,                  "b": 0},
        "LFO":               {"a": 0,                  "b": 0},
        "Misc Mod":          {"a": 0,                  "b": 0},
        "VCO":               {"a": 0,                  "b": 0},
        "Mixer Mute & Solo": {"a": [0, 0, 0, 0, 0, 0], "b": [0, 0, 0, 0, 0, 0]},
    }
}