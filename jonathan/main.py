from time import sleep
from pynput.keyboard import Key, Listener

import sys
sys.path.append("..")
from HapticVest.bhaptics import haptic_player

player = haptic_player.HapticPlayer()
sleep(3) # Needs a few seconds to boot up or something

# Setup
frameNames = ["main1", "main2", "main3", "main4", "top1", "top2", "accidental"]
pins = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]

rangeTime = 500 # milliseconds
sweepTime = [105, 60] # 4:7 ratio, 420 milliseconds overall
accidentalTime = 500 # milliseconds

keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']']

sweepDirections = [0,0,1,2,2,3,3,4,4,5,6,6]
accidentals = [-1,1,-1,0,-1,-1,1,-1,1,-1,0,-1] # -1 none, 0 flat, 1 sharp

directions = [
  [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]], # down
  [[4],[3,8],[2,7,12],[1,6,11,16],[5,10,15],[9,14],[13]], # down-left
  [[4,8,12,16],[3,7,11,15],[2,6,10,14],[1,5,9,13]], # left
  [[16],[12,15],[8,11,14],[4,7,10,13],[3,6,9],[2,5],[1]], # up-left
  [[13,14,15,16],[9,10,11,12],[5,6,7,8],[1,2,3,4]], # up
  [[13],[9,14],[5,10,15],[1,6,11,16],[2,7,12],[3,8],[4]], # up-right
  [[1,5,9,13],[2,6,10,14],[3,7,11,15],[4,8,12,16]] # right
]

keyNum = 0 # Between 0 and 24

def on_press(key):
  print(key)
  print(keys)
  print('{0} pressed'.format(
      key))
  if key == Key.esc:
    # Stop listener
    return False
  if hasattr(key, 'char') and key.char in keys:
    print(key)
    keyNum = keys.index(key.char)%12
    sweep(sweepDirections[keyNum])


def sweep(direction):
  # direction: see 3d array
  # phase: 4 phases for cardinal directions, 7 for diagonal directions
  numPhases = len(directions[direction])
  print(sweepTime[direction%2])
  for phase in range(numPhases):
    for index, i in enumerate(directions[direction][phase]):
      player.submit_dot(i-1, "VestBack", [{"index": pins[i-1], "intensity": 50}], int(sweepTime[direction%2]*1.0))
    sleep(sweepTime[direction%2]/1000)

with Listener(
    on_press=on_press) as listener:
  listener.join()
