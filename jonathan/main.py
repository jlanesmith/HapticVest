from time import sleep
import time
from pynput.keyboard import Key, Listener
import random
import math
import numpy

import os
import pygame as pg
import pygame.midi
import pygame.mixer

import sys
sys.path.append("..")
from HapticVest.bhaptics import haptic_player


#############
# Constants #
#############

player = haptic_player.HapticPlayer()

isPiano = False # Whether using piano keyboard or computer keyboard
mode = 5
# 0 is just learning the notes
# 1 is testing with random individual notes
# 2 is testing with a randomly generated melody
# 3 is testing with a prerecorded melody
# 4 is playback of prerecorded melody without haptics
# 5 is playback of prerecorded melody with haptics

# For melody, first number is note (low C = 0), second number is duration (quarter, half, whole)
# melody = [[0,1], [2, 1], [4,2], [0,1], [2, 1], [4,2], [0,1], [2, 1], [4,2], [0,1], [2, 1], [0,2]]
melody =[[9,1], [11,0], [8,0], [8,0], [5,1], [4,0], [6,2], [6,1], [8,0], [6,0], [6,0], [6,1], [6,0], [6,1], [9,1], [5,1], [5,0], [1,0], [5,1], [9,1]]
beatLegend = [1,2,4]
totalNotes = len(melody)
totalBeats = sum(beatLegend[melody[i][1]] for i in range(totalNotes))
isOldRange = True # Whether the range goes to each point or just the 3 points (left, centre, right)

pins = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
accidentalPins = [0,2,4,10,12,14]
rangePins = [0,1,2,3]

numSweepPhases = 4
directions = [
  [[2,3],[6,7],[10,11],[14,15]], # down
  [[4],[7],[10],[13]], # down-left
  [[8,12],[7,11],[6,10],[5,9]], # left
  [[16],[11],[6],[1]], # up-left
  [[14,15],[10,11],[6,7],[2,3]], # up
  [[13],[10],[7],[4]], # up-right
  [[5,9],[6,10],[7,11],[8,12]] # right
]

secondsPerBar = 2
rangeUpdateTime = 10 # range vibration updates every 10 ms
rangeTime = 100 # time to move to next note
sweepTime = 75 # milliseconds
accidentalTime = 200 # milliseconds
durations =  [i * secondsPerBar - sweepTime*(numSweepPhases-1) for i in [250, 500, 1000]] # Quarter note, half note, whole note

maxRangeIntensity = 40
sweepIntensity = [80, 100] # Cardinal notes, diagonal notes

keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']','\\']
playbackKeys = ['z', 'x', 'c', 'v', 'b']
sweepDirections = [0,0,1,2,2,3,3,4,4,5,6,6]
accidentals = [-1,1,-1,0,-1,-1,1,-1,1,-1,0,-1] # -1 none, 0 flat, 1 sharp
noteNames = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]


####################
# Global Variables #
####################

GVARS = {
  'sound': None,
  'isRunning': True, # For computer keyboard input

  'randomMelodyNote': [12,1],
  'playbackCommand': 0,
    # 0 is no command
    # 1 is skip to beginning
    # 2 is skip to previous bar
    # 3 is skip to previous note (to repeat note)
    # 4 is to play
    # 5 is to pause

  'melodyIndex': 0, # which note of the melody we're on
  'beatIndex': 0, # which beat of the melody we're on
  'beginMelody': False,
  'lastNoteTime': 0, # time since last melody note was played
  'isGuessed': True, # Whether the correct note has been guessed yet

  'keyNum': None, # Number of note to be vibrated, between 0 and 24
  'durationNum': 0,
  'pointOfVibration': 1.5, # 0 to 3
  'oldPOV': None,
  'newPOV': None,
  'direction': None,
  'isSharp': False,
  'vibrationStartTime':  0,
  'moveRangePhase': 0, # Phases within moving through the range
  'sweepPhase': 0, # Phases within sweeping
}


##############
# Main Logic #
##############

def doRandomNote():
  startVibrations(random.randint(0,24))
  print(noteNames[GVARS['keyNum']%12], (math.floor(GVARS['keyNum']/12)+1))
  
def playAudio(midiNote):
  if GVARS['sound']:
    GVARS['sound'].stop()
  sampleRate = 44100
  freq = int(2**((midiNote-69)/12)*440)
  arr = numpy.array([4096 * numpy.sin(2.0 * numpy.pi * freq * x / sampleRate) for x in range(0, sampleRate)]).astype(numpy.int16)
  arr2 = numpy.c_[arr,arr]
  GVARS['sound'] = pygame.sndarray.make_sound(arr2)
  GVARS['sound'].play(-1)

def startVibrations(keyNum, durationNum = 0):
  GVARS['durationNum'] = durationNum
  GVARS['newPOV'] = keyNum/8 if isOldRange else (0 if keyNum < 12 else (3 if keyNum > 12 else 1.5))
  GVARS['oldPOV'] = GVARS['pointOfVibration']
  GVARS['direction'] = sweepDirections[keyNum%12]
  GVARS['isSharp'] = accidentals[keyNum%12]
  GVARS['keyNum'] = keyNum
  GVARS['moveRangePhase'] = 0
  GVARS['sweepPhase'] = 0
  GVARS['accidentalPhase'] = 0
  GVARS['vibrationStartTime'] = time.time_ns()

def updateVibrations():
  if GVARS['oldPOV'] != None:
    moveRange()
    sweep()
    vibrateAccidental()

def moveRange():
  if (GVARS['moveRangePhase'] < int(rangeTime/rangeUpdateTime) and \
  time.time_ns() - GVARS['vibrationStartTime'] >= rangeUpdateTime*GVARS['moveRangePhase'] * 1000000):
    GVARS['moveRangePhase'] = GVARS['moveRangePhase'] + 1
    GVARS['pointOfVibration'] = GVARS['oldPOV'] + (GVARS['newPOV'] - GVARS['oldPOV'])*(GVARS['moveRangePhase']/(rangeTime/rangeUpdateTime))
    for index, rangeInfo in enumerate(getRangeInfo(GVARS['pointOfVibration'])):
      player.submit_dot("range" + str(index), "VestFront", [{"index": rangePins[int(rangeInfo[0])], "intensity": int(rangeInfo[1])}], 10000)

def sweep():
  # direction: see 3d array
  # duration: time to hold the last vibration
  nextUpdateTime = sweepTime*GVARS['sweepPhase'] if GVARS['sweepPhase'] < 4 else \
    sweepTime*(numSweepPhases-1) + durations[GVARS['durationNum']]
  if (GVARS['sweepPhase'] < numSweepPhases and time.time_ns() - GVARS['vibrationStartTime'] >= nextUpdateTime * 1000000):
    phaseTime = int(durations[GVARS['durationNum']] if GVARS['sweepPhase'] == numSweepPhases-1 else sweepTime)
    for index, i in enumerate(directions[GVARS['direction']][GVARS['sweepPhase']]):
      player.submit_dot(i-1, "VestBack", [{"index": pins[i-1], "intensity": sweepIntensity[GVARS['direction']%2]}], phaseTime)
    GVARS['sweepPhase'] = GVARS['sweepPhase'] + 1

def vibrateAccidental():
  if (GVARS['accidentalPhase'] == 0 and time.time_ns() - GVARS['vibrationStartTime'] >= (sweepTime*numSweepPhases) * 1000000):
    GVARS['accidentalPhase'] = 1
    if (GVARS['isSharp'] == 0 or GVARS['isSharp'] == 1):
      for i in range(len(accidentalPins)):
        player.submit_dot("accidental" + str(i), "Right" if GVARS['isSharp'] else "Left", \
          [{"index": accidentalPins[i], "intensity": 100}], accidentalTime)

def resetVibrations():
  player.submit_dot("range0", "VestFront", [{"index": 90, "intensity": 0}], 1)
  player.submit_dot("range1", "VestFront", [{"index": 91, "intensity": 0}], 1)
  for i in range(16):
    player.submit_dot(i, "VestBack", [{"index": pins[i], "intensity": 0}], 1)
  for i in range(len(accidentalPins)):
    player.submit_dot("accidental" + str(i), "Left", [{"index": accidentalPins[i], "intensity": 0}], 1)
    player.submit_dot("accidental" + str(i), "Right", [{"index": accidentalPins[i], "intensity": 0}], 1)

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

def continuousLoop(): # Code that runs every loop
  updateVibrations()
  playbackCommand = GVARS['playbackCommand'] # To avoid situtations where it changes during use
  if playbackCommand == 1: # Skip to beginning
    resetVibrations()
    GVARS['melodyIndex'] = 0
    GVARS['beatIndex'] = 0
    GVARS['lastNoteTime'] = 0
  elif playbackCommand == 2: # Skip to previous bar
    resetVibrations()
    while True:
      GVARS['melodyIndex'] = GVARS['melodyIndex'] - 1 if GVARS['melodyIndex'] != 0 else totalNotes - 1
      GVARS['beatIndex'] = GVARS['beatIndex'] - beatLegend[melody[GVARS['melodyIndex']][1]] \
        if GVARS['beatIndex'] >= beatLegend[melody[GVARS['melodyIndex']][1]] \
        else totalBeats - beatLegend[melody[GVARS['melodyIndex']][1]]
      if (GVARS['beatIndex'] % 4 == 0):
        GVARS['lastNoteTime'] = 0
        break
  elif playbackCommand == 3: # Skip to previous note
    GVARS['melodyIndex'] = GVARS['melodyIndex'] - 1 if GVARS['melodyIndex'] != 0 else totalNotes - 1
    GVARS['beatIndex'] = GVARS['beatIndex'] - beatLegend[melody[GVARS['melodyIndex']][1]] \
      if GVARS['beatIndex'] >= beatLegend[melody[GVARS['melodyIndex']][1]] \
      else totalBeats - beatLegend[melody[GVARS['melodyIndex']][1]]
  elif playbackCommand == 4: # Play
    GVARS['beginMelody'] = True
  elif playbackCommand == 5: # Pause
    resetVibrations()
    GVARS['beginMelody'] = False
    GVARS['sound'].stop()
  if (GVARS['playbackCommand'] == playbackCommand): # If playbackCommand changed, don't get rid of it just yet
    GVARS['playbackCommand'] = 0

  noteDuration = beatLegend[melody[GVARS['melodyIndex']][1] if mode != 2 else GVARS['randomMelodyNote'][1]] * 250000000 * secondsPerBar
  if GVARS['beginMelody'] and (((mode == 2 or mode == 3) and GVARS['isGuessed']) or (mode == 4 or mode == 5)) \
    and (time.time_ns() - GVARS['lastNoteTime'] >= noteDuration):
    if mode != 2:
      if GVARS['lastNoteTime'] > 0: # If it's not the first note
        GVARS['beatIndex'] = GVARS['beatIndex'] + beatLegend[melody[GVARS['melodyIndex']][1]]
        GVARS['melodyIndex'] = GVARS['melodyIndex'] + 1
        if GVARS['melodyIndex'] == len(melody):
          resetVibrations()
          GVARS['beginMelody'] = False
          GVARS['melodyIndex'] = 0
          GVARS['beatIndex'] = 0
          GVARS['lastNoteTime'] = 0
          GVARS['sound'].stop()
          return # This used to be continue
      GVARS['keyNum'] = melody[GVARS['melodyIndex']][0]
    else:
      newNote = GVARS['randomMelodyNote'][0] + random.randint(-4, 4)
      GVARS['randomMelodyNote'] = [max(min(newNote,24),0), random.choice([0,1,2])]
      GVARS['keyNum'] = GVARS['randomMelodyNote'][0]
    if mode == 4 or mode == 5:
      playAudio(GVARS['keyNum'] + 60)
    GVARS['lastNoteTime'] = time.time_ns()
    if mode != 4:
      startVibrations(GVARS['keyNum'], melody[GVARS['melodyIndex']][1] if mode != 2 else GVARS['randomMelodyNote'][1])
    GVARS['isGuessed'] = False

def pressPlayNote(): # C3 on piano, space on computer
  if mode == 2 or mode == 3 or mode == 4 or mode == 5: # Melody
    if not GVARS['beginMelody']:
      GVARS['beginMelody'] = True
    if not GVARS['isGuessed'] and (mode == 2 or mode == 3):
      startVibrations(GVARS['keyNum'], melody[GVARS['melodyIndex']][1] if mode == 3 else GVARS['randomMelodyNote'][1])
  elif mode == 1: # No melody, just random notes
    if GVARS['isGuessed']: # This currently won't work for computer keyboard input, only for piano input
      doRandomNote()
      GVARS['isGuessed'] = False
    else:
      startVibrations(GVARS['keyNum'])

###########################
# Computer Keyboard Input #
###########################

def on_press(key):
  print('{0} pressed'.format(
      key))
  if key == Key.esc:
    # Stop listener
    resetVibrations()
    GVARS['isRunning'] = False
  if key == Key.space:
    pressPlayNote()
  if mode == 0 and hasattr(key, 'char') and key.char in keys:
    startVibrations(keys.index(key.char))
  if (mode == 4 or mode == 5) and hasattr(key, 'char') and key.char in playbackKeys:
    GVARS['playbackCommand'] = playbackKeys.index(key.char) + 1


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

    continuousLoop()

    # Code for when a piano key is pressed
    events = event_get()
    for e in events:
      if e.type in [pg.QUIT]:
        going = False
      if e.type in [pg.KEYDOWN]:
        going = False
      if e.type in [pygame.midi.MIDIIN] and e.data1 == 108: # C8
        resetVibrations()
        going = False
      elif e.type in [pygame.midi.MIDIIN] and e.status == 144 and e.data1 == 48: # C3
        pressPlayNote()
      elif e.type in [pygame.midi.MIDIIN] and e.status == 144 and e.data1 >= 60 and e.data1 <= 84: # C4 to C6
        if mode == 0:
          startVibrations(e.data1 - 60)
        elif mode == 1:
          if GVARS['keyNum'] != None:
            if e.data1 == GVARS['keyNum']:
              pygame.mixer.music.load("jonathan/correct.wav")
              GVARS['isGuessed'] = True
            else:
              pygame.mixer.music.load("jonathan/wrong.mp3")
            pygame.mixer.music.play()
        elif mode == 2 or mode == 3:
          if GVARS['keyNum'] != None:
            if e.data1 == GVARS['keyNum']:
              GVARS['isGuessed'] = True
            else:
              pygame.mixer.music.load("jonathan/wrong.mp3")
              pygame.mixer.music.play()
      elif e.type in [pygame.midi.MIDIIN] and e.status == 144 and e.data1 in [36, 38, 40, 41, 43]: # C2 to G2
        if mode == 4 or mode == 5:
            GVARS['playbackCommand'] = [36, 38, 40, 41, 43].index(e.data1) + 1
    if i.poll():
      midi_events = i.read(10)
      # convert them into pygame events.
      midi_evs = pygame.midi.midis2events(midi_events, i.device_id)

      for m_e in midi_evs:
        event_post(m_e)
  del i
  pygame.midi.quit()


##########
# Start #
##########

pygame.mixer.init(44100,-16,2,512)
sleep(3) # Needs a few seconds to boot up or something
print("Begin!")
if isPiano:
  midi_input_main(1)
else:
  listener = Listener(
    on_press=on_press)
  listener.start()
  while GVARS['isRunning']:
    continuousLoop()
