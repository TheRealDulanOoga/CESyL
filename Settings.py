global globalIndecies
global sceneSpecificIndecies

global PWMSTEPS
global LEDCOUNT

global OSCCLIENT

PWMSTEPS = pow(2, 5)
LEDCOUNT = 4

globalIndecies = {
    "Global": {
        "Scene": {"Index": 0, "Values": ["a", "b"], "Current Value": "a"}
    },
    "Scene-dependant": {
        "Filter": {"a": 0, "b": 0}
    }
}