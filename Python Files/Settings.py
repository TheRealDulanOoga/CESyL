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

global LFOMODSOURCES
global OTHERMODSOURCES
global MACROMODSOURCES
global MODSTATUSCHANGE

global ALLMODULATIONPATHS


PWMSTEPS = pow(2, 5)
LEDCOUNT = 4
ENCODERSCOUNT = 0
BUTTONSCOUNT = 0
OSCRECIEVEHISTORY = {"Patch": [-1, 0], "Param": [[]], "ModSource": [-1, 0], "Mod": [[]]}
HISTORYSIZE = 0

LASTOSCILLATORTYPE = 0
LASTFXTYPE = 0
VCOCONTEXTUAL = False
FXCONTEXTUAL = False

LFOMODSOURCES = 12
OTHERMODSOURCES = 13
MACROMODSOURCES = 1
MODSTATUSCHANGE = [False, 0, 0]

ALLMODULATIONPATHS = {
    "Macro": "/mod/macro_<n>",
    "Misc Mod": ["/mod/vel", 
                 "/mod/rel_vel", 
                 "/mod/keytrk", 
                 "/mod/<s>/lowest_key", 
                 "/mod/<s>/highest_key", 
                 "/mod/<s>/latest_key", 
                 "/mod/mw", 
                 "/mod/sus",
                 "/mod/pb",
                 "/mod/alt_bi",
                 "/mod/alt_uni",
                 "/mod/<s>/feg",
                 "/mod/<s>/aeg"
                 ],
    "LFO": ["/mod/<s>/vlfo_<n>", "/mod/<s>/slfo_<n>"]
}

globalIndecies = {
    "Global": {
        "Scene":      {"Index": 0, "Values": ["a", "b"], "Current Value": "a",     "Type": "str"},
        "FX":         {"Index": 0,                                                 "Type": "int"},
        "Modulation": {"Index": 0, "Values": [[False]],  "Current Value": [False], "Type": "bool"}
    },
    "Scene-dependant": {
        "Filter":            {"a": 0,                                    "b": 0},
        "EG":                {"a": 0,                                    "b": 0},
        "Mixer":             {"a": 0,                                    "b": 0},
        "LFO":               {"a": 0,                                    "b": 0},
        "Misc Mod":          {"a": 0,                                    "b": 0},
        "VCO":               {"a": 0,                                    "b": 0},
        "Mixer Mute & Solo": {"a": [0, 0, 0, 0, 0, 0],                   "b": [0, 0, 0, 0, 0, 0]},
        #TODO make code for the following ones
        "VCO KT & RT":       {"a": [0, 0, 0],                            "b": [0, 0, 0]},
        "LFO Polarity":      {"a": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "b": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
        "EG Settings":       {"a": [0, 0, 0, 0, 0],                      "b": [0, 0, 0, 0, 0]}
    }
}