from time import sleep
import time
from pynput.keyboard import Key, Listener
import random
import math

import os
import pygame as pg
import pygame.midi
import pygame.mixer
pygame.mixer.init()

import sys
sys.path.append("..")
from HapticVest.bhaptics import haptic_player

player = haptic_player.HapticPlayer()
sleep(3) # Needs a few seconds to boot up or something
print("Begin!")

isPiano = True # Whether using piano keyboard or computer keyboard
mode = 3 
# 0 is just learning the notes
# 1 is testing with random individual notes
# 2 is doing a randomly generated melody
# 3 is doing prerecorded melody

# For melody, first number is note (low C = 0), second number is duration (1, 2, or 4)
melody = [[0,2], [2, 2], [4,2], [5,2], [4,2], [2,2], [0,4]]
melodyIndex = 0
beginMelody = False
lastNoteTime = 0

isOldRange = True # Whether the range goes to each point or just the 3 points (left, centre, right)

correctNote = 0 # MIDI number of correct note, if mode != 0
isGuessed = True # Whether the correct note has been guessed yet

# Setup
pins = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
accidentalPins = [0,2,4,10,12,14]
rangePins = [0,1,2,3]

rangeUpdateTime = 10 # range vibration updates every 10 ms
rangeTime = 100 # time to move to next note
sweepTime = 75 # milliseconds
accidentalTime = 200 # milliseconds
durations = [75, 575, 1075] # Quarter note, half note, whole note

maxRangeIntensity = 40
sweepIntensity = [80, 100] # Cardinal notes, diagonal notes

keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']','\\']
sweepDirections = [0,0,1,2,2,3,3,4,4,5,6,6]
accidentals = [-1,1,-1,0,-1,-1,1,-1,1,-1,0,-1] # -1 none, 0 flat, 1 sharp
noteNames = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]

oldDirections = [
  [[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]], # down
  [[4],[3,8],[2,7,12],[1,6,11,16],[5,10,15],[9,14],[13]], # down-left
  [[4,8,12,16],[3,7,11,15],[2,6,10,14],[1,5,9,13]], # left
  [[16],[12,15],[8,11,14],[4,7,10,13],[3,6,9],[2,5],[1]], # up-left
  [[13,14,15,16],[9,10,11,12],[5,6,7,8],[1,2,3,4]], # up
  [[13],[9,14],[5,10,15],[1,6,11,16],[2,7,12],[3,8],[4]], # up-right
  [[1,5,9,13],[2,6,10,14],[3,7,11,15],[4,8,12,16]] # right
]

directions = [
  [[2,3],[6,7],[10,11],[14,15]], # down
  [[4],[7],[10],[13]], # down-left
  [[8,12],[7,11],[6,10],[5,9]], # left
  [[16],[11],[6],[1]], # up-left
  [[14,15],[10,11],[6,7],[2,3]], # up
  [[13],[10],[7],[4]], # up-right
  [[5,9],[6,10],[7,11],[8,12]] # right
]

keyNum = 0 # Between 0 and 24
pointOfVibration = 1.5 # 0 to 3

def doRandomNote():
  global correctNote
  keyNum = random.randint(0,24)
  correctNote = 60 + keyNum
  runVibrations(keyNum)
  sleep(1)
  print(noteNames[keyNum%12], (math.floor(keyNum/12)+1))


##############
# Main Logic #
##############

def runVibrations(keyNum, durationNum = 1):
  global pointOfVibration
  newPOV = keyNum/8 if isOldRange else (0 if keyNum < 12 else (3 if keyNum > 12 else 1.5))
  moveRange(pointOfVibration, newPOV)
  sweep(sweepDirections[keyNum%12], durationNum)
  vibrateAccidental(accidentals[keyNum%12])
  sleep((durations[durationNum]-sweepTime)/1000)

def moveRange(oldPOV, newPOV):
  global pointOfVibration
  for i in range(int(rangeTime/rangeUpdateTime)): # Time between each update
    pointOfVibration = oldPOV + (newPOV - oldPOV)*((1+i)/(rangeTime/rangeUpdateTime))
    for index, rangeInfo in enumerate(getRangeInfo(pointOfVibration)):
      player.submit_dot("range" + str(index), "VestFront", [{"index": rangePins[int(rangeInfo[0])], "intensity": int(rangeInfo[1])}], 10000)
    sleep(rangeUpdateTime/1000)

def resetRange():
    player.submit_dot("range0", "VestFront", [{"index": 90, "intensity": 0}], 1)
    player.submit_dot("range1", "VestFront", [{"index": 91, "intensity": 0}], 1)

def sweep(direction, durationNum):
  # direction: see 3d array
  # duration: time to hold the last vibration
  # phase: 4 phases for cardinal directions, 7 for diagonal directions
  numPhases = len(directions[direction])
  for phase in range(numPhases):
    phaseTime = int(durations[durationNum] if phase == numPhases-1 else sweepTime)
    for index, i in enumerate(directions[direction][phase]):
      isLastPhase = phase == numPhases-1
      player.submit_dot(i-1, "VestBack", [{"index": pins[i-1], "intensity": sweepIntensity[direction%2]}], phaseTime)
    sleep(sweepTime/1000)

def vibrateAccidental(isSharp):
  if (isSharp == 0 or isSharp == 1):
    for i in range(len(accidentalPins)):
      player.submit_dot("accidental" + str(i), "Right" if isSharp else "Left", [{"index": accidentalPins[i], "intensity": 100}], accidentalTime)
    sleep(accidentalTime/1000/2) # only wait half of the accidentalTime before moving on to next note

def getRangeInfo(POV): # point of vibration
  justOneActuator = [0,1,2,3]
  if POV in justOneActuator:
    return [[POV, maxRangeIntensity]]
  elif POV > 0 and POV < 1:
    return [[0, (1-POV)*maxRangeIntensity], [1, (POV-0)*maxRangeIntensity]]
  elif POV > 1 and POV < 2:
    return [[1, (2-POV)*maxRangeIntensity], [2, (POV-1)*maxRangeIntensity]]
  elif POV > 2 and POV < 3:
    return [[2, (3-POV)*maxRangeIntensity], [3, (POV-2)*maxRangeIntensity]]


###########################
# Computer Keyboard Input #
###########################

def on_press(key):
  print('{0} pressed'.format(
      key))
  if key == Key.esc:
    # Stop listener
    resetRange()
    return False
  if key == Key.space:
    doRandomNote()
  if hasattr(key, 'char') and key.char in keys:
    keyNum = keys.index(key.char)
    runVibrations(keyNum)


#######################
# MIDI Keyboard Input #
#######################

def print_midi_device_info():
  pygame.midi.init()
  _print_midi_device_info()
  pygame.midi.quit()


def _print_midi_device_info():
  for i in range(pygame.midi.get_count()):
    r = pygame.midi.get_device_info(i)
    (interf, name, input, output, opened) = r

    in_out = ""
    if input:
      in_out = "(input)"
    if output:
      in_out = "(output)"

    print(
      "%2i: interface :%s:, name :%s:, opened :%s:  %s"
      % (i, interf, name, opened, in_out)
    )

def midi_input_main(device_id=None):
  global isGuessed
  global beginMelody
  global correctNote
  global lastNoteTime
  global melodyIndex
  pg.init()
  pg.fastevent.init()
  event_get = pg.fastevent.get
  event_post = pg.fastevent.post

  pygame.midi.init()

  # _print_midi_device_info()

  if device_id is None:
    input_id = pygame.midi.get_default_input_id()
  else:
    input_id = device_id

  # print("using input_id :%s:" % input_id)
  i = pygame.midi.Input(input_id)

  pg.display.set_mode((1, 1))

  going = True
  while going:

    if (beginMelody and isGuessed and time.time_ns() - lastNoteTime >= melody[melodyIndex][1]*500000000):
      if lastNoteTime > 0: # If it's not the first note
        melodyIndex = melodyIndex + 1
        if melodyIndex == len(melody):
          resetRange()
          going = False
          break
      correctNote = 60 + melody[melodyIndex][0]
      runVibrations(correctNote - 60)
      lastNoteTime = time.time_ns()
      isGuessed = False

    events = event_get()
    for e in events:
      if e.type in [pg.QUIT]:
        going = False
      if e.type in [pg.KEYDOWN]:
        going = False
      if e.type in [pygame.midi.MIDIIN] and e.data1 == 108: # C8
        resetRange()
        going = False
      elif e.type in [pygame.midi.MIDIIN] and e.status == 144 and e.data1 == 48: # C3
        if mode == 2 or mode == 3: # Melody
          if not beginMelody:
            beginMelody = True
          if not isGuessed:
            runVibrations(correctNote - 60)
        elif mode == 1:
          if isGuessed:
            doRandomNote()
            isGuessed = False
          else:
            runVibrations(correctNote - 60)
      elif e.type in [pygame.midi.MIDIIN] and e.status == 144 and e.data1 >= 60 and e.data1 <= 84: # C4 to C6
        if mode == 0:
          runVibrations(e.data1 - 60)
        elif mode == 1:
          if correctNote != 0:
            if e.data1 == correctNote:
              pygame.mixer.music.load("jonathan/correct.wav")
              isGuessed = True
            else:
              pygame.mixer.music.load("jonathan/wrong.mp3")
            pygame.mixer.music.play()
        elif mode == 2 or mode == 3:
          if correctNote != 0:
            if e.data1 == correctNote:
              isGuessed = True
            else:
              pygame.mixer.music.load("jonathan/wrong.mp3")
              pygame.mixer.music.play()
    if i.poll():
      midi_events = i.read(10)
      # convert them into pygame events.
      midi_evs = pygame.midi.midis2events(midi_events, i.device_id)

      for m_e in midi_evs:
        event_post(m_e)
  del i
  pygame.midi.quit()


if isPiano:
  midi_input_main(1)
else:
  with Listener(on_press=on_press) as listener:
    listener.join()
