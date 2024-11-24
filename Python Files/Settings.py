global globalIndecies
global sceneSpecificIndecies

global PWMSTEPS
global LEDCOUNT
global ENCODERSCOUNT
global BUTTONSCOUNT

global OSCRECIEVEHISTORY
global HISTORYSIZE

global OSCCLIENT

PWMSTEPS = pow(2, 5)
LEDCOUNT = 4
ENCODERSCOUNT = 0
BUTTONSCOUNT = 0
OSCRECIEVEHISTORY = [[]]
HISTORYSIZE = 0

globalIndecies = {
    "Global": {
        "Scene": {"Index": 0, "Values": ["a", "b"], "Current Value": "a"}
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