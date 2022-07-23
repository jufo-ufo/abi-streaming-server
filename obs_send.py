# pip install obs-websocket-py
# pip install keyboard
# pip install PyATEMMax

import time
from obswebsocket import obsws, requests
import keyboard

import PyATEMMax

# Please configure your shortcut keys here:
map_obs1_scenes = {"1": 0, "2": 1, "3": 2}
map_obs1_trans = {"y": 0, "m": 0, "n": 1, "b": 2}
map_obs2_scenes = {}
map_obs2_trans = {}
map_atem_cut = {"y"}
map_atem_scenes = {"ü": 1, "+": 2, "ä": 3, "#": 4}
map_exit = {"q"}
# and adjust the network configurations here:
obs1 = obsws('192.168.178.45', 4444, "H3110 ")
obs1.connect()
obs2 = obsws('192.168.178.75', 4444, "H3110 ")
obs2.connect()

atem = PyATEMMax.ATEMMax()
atem.connect("192.168.113.00")
#atem.waitForConnection()

# OBS1 get scenes and transitions:
try:
    obs1_scenes = obs1.call(requests.GetSceneList())
    obs1_transitions = obs1.call(requests.GetTransitionList())
    obs1_sceneName = []
    for s in obs1_scenes.getScenes():
        obs1_sceneName.append(s['name'])
    print(obs1_sceneName)
    obs1_transitionName = []
    for s in obs1_transitions.getTransitions():
        obs1_transitionName.append(s['name'])
    print(obs1_transitionName)
except Exception:
    pass
# OBS2 get scenes and transitions:
try:
    obs2_scenes = obs1.call(requests.GetSceneList())
    obs2_transitions = obs1.call(requests.GetTransitionList())
    obs2_sceneName = []
    for s in obs2_scenes.getScenes():
        obs2_sceneName.append(s['name'])
    print(obs2_sceneName)
    obs2_transitionName = []
    for s in obs2_transitions.getTransitions():
        obs2_transitionName.append(s['name'])
    print(obs2_transitionName)
except Exception:
    pass

while True:
    try:
        key = keyboard.read_key()

        if(key in map_obs1_scenes):
          obs1.call(requests.SetPreviewScene(obs1_sceneName[map_obs1_scenes[key]]))

        if(key in map_obs1_trans):
            obs1.call(requests.SetCurrentTransition(obs1_transitionName[map_obs1_trans[key]]))
            obs1.call(requests.TransitionToProgram())

        if (key in map_obs2_scenes):
            obs2.call(requests.SetPreviewScene(obs1_sceneName[map_obs2_scenes[key]]))

        if (key in map_obs2_trans):
            obs2.call(requests.SetCurrentTransition(obs1_transitionName[map_obs2_trans[key]]))
            obs2.call(requests.TransitionToProgram())

        if (key in map_atem_cut):
            atem.execCutME()

        if (key in map_atem_scenes):
            atem.setPreviewInputVideoSource(0, map_atem_scenes[key])

        if (key in map_exit):
            print("Exiting: Disconnecting...")
            obs1.disconnect()
            obs2.disconnect()
            atem.disconnect()
            exit()
    except IndexError:
        pass
    time.sleep(0.01)
