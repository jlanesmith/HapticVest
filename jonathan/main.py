from time import sleep

import sys
sys.path.append("..")
from HapticVest.bhaptics import haptic_player


player = haptic_player.HapticPlayer()
sleep(0.4)

interval = 0.5
durationMillis = 1000

for i in range(1):
    print(i, "back")
    player.submit_dot("backFrame", "VestBack", [{"index": i, "intensity": 100}], durationMillis)
    # sleep(interval)

    print(i, "front")
    player.submit_dot("frontFrame", "VestFront", [{"index": i, "intensity": 100}], durationMillis)
    # sleep(interval)

sleep(2)
