from time import sleep
import time
from datetime import datetime
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

# For melody, first number is note (low C = 0), second number is duration (quarter, half)
# All melodies have 22 notes and 3 octave indications (used to be 5 sweeps but I made it easier)
melodies = [
  [[0,0], [4,0], [9,0], [7,0], [5,1], [7,0], [4,0], [2,1], [11,0], [7,0], [12,1], [12,1], [9,0], [7,0], [7,0], [5,0], [4,1], [12,1], [14,0], [17,0], [9,0], [11,0], [12,1]],
  # Real ones:
  [[0,1], [4,0], [5,0], [7,1], [9,0], [7,0], [16,1], [14,0], [16,0], [12,1], [7,1], [9,0], [5,0], [9,0], [12,0], [11,1], [7,1], [12,0], [12,0], [14,0], [11,0], [12,1]], #123
  [[0,0], [2,0], [4,0], [7,0], [12,1], [7,1], [9,0], [12,0], [14,0], [12,0], [16,1], [12,1], [17,0], [19,0], [21,0], [17,0], [16,1], [16,0], [17,0], [19,1], [11,1], [12,1]], #123
  [[12,0], [11,0], [12,0], [7,0], [9,1], [7,1], [4,0], [2,0], [4,0], [7,0], [12,1], [16,1], [17,0], [19,0], [17,1], [16,0], [21,0], [19,1], [14,1], [9,0], [11,0], [12,1]], #123
  [[4,0], [7,0], [12,1], [9,0], [5,0], [17,0], [19,0], [14,1], [19,1], [16,0], [14,0], [12,1], [21,0], [21,0], [17,0], [14,0], [16,1], [12,1], [11,0], [12,0], [14,1], [12,1]], #123
  [[9,0], [4,0], [12,0], [11,0], [9,1], [16,1], [14,0], [16,0], [17,1], [16,0], [14,0], [12,1], [11,0], [9,0], [11,0], [4,0], [5,1], [14,1], [16,0], [17,0], [16,1], [21,1]], #123
  [[9,0], [4,0], [11,0], [4,0], [12,1], [16,0], [21,0], [17,1], [14,0], [19,0], [16,1], [9,1], [11,1], [4,0], [4,0], [12,1], [17,0], [14,0], [19,1], [14,0], [16,0], [12,1]] #123    
]
melodyIndex = 1
melodyChunk = 0
# 0 full
# 1 first  2 bars
# 2 second 2 bars
# 3 third  2 bars
# 4 fourth 2 bars
# 5 first  4 bars
# 6 second 4 bars

secondsPerBar = 4
mode = 0
# 0 is just learning the notes
# 1 is testing with random individual notes
# 2 is testing with a randomly generated melody
# 3 is testing with a prerecorded melody
# 4 is playback of prerecorded melody without haptics
# 5 is playback of prerecorded melody with haptics
# 6 is just logging the data (for initial test)
# 7 is evaluating with a precorded melody but no haptics! It just waits for you to play
# 8 is testing with a prerecorded melody without haptics, with audio (if people have trouble finding the notes)

isPiano = True # Whether using piano keyboard or computer keyboard
writeToFile = True

beatLegend = [1,2,4]

def makeMelody():
  if melodyChunk == 0:
    return melodies[melodyIndex]
  startBeats = [-1, 0, 8,  16, 24, 0,  16]
  endBeats =   [-1, 8, 16, 24, 32, 16, 32]
  beatNumber = 0
  startIndex = 0
  endIndex = 0
  for i in range(len(melodies[melodyIndex])):
    if beatNumber == startBeats[melodyChunk]:
      startIndex = i
    beatNumber = beatNumber + beatLegend[melodies[melodyIndex][i][1]]
    if beatNumber == endBeats[melodyChunk]:
      endIndex = i+1
  if endIndex == 0:
    endIndex = len(melodies[melodyIndex])
  return melodies[melodyIndex][startIndex:endIndex]
melody = makeMelody()

totalNotes = len(melody)
totalBeats = sum(beatLegend[melody[i][1]] for i in range(totalNotes))
validNotes = [0,2,4,5,7,9,11,12,14,16,17,19,21,23] # not 24 at the end, just for mode 1 and 2

pins = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19]

# backPointPins = [[0], [8], [16,17], [9,10], [3], [11], [18,19]] # Backwards N
# backPointPins = [[0], [8], [16,17], [9,10], [18,19], [11], [3]] # Edwin's W
backPointPins = [[16,17], [8], [0], [9,10], [18,19], [11], [3]] # Forwards N

isBrailleOctaves = True
octavePins =  [[4,8,12],[7,11,15]] # [[4],[7]] # just one for karen
octaveIntensity = 60 # normally 60 but changed to 40 for karen
rangePins = [8,9,10,11] # [12,13,14,15] # [0,1,2,3] # [16,17,18,19] # For old octave sweep system

octaveTime = 600 if isBrailleOctaves else 700 # time to complete octave sweep, or to vibrate which octave it is
durations =  [int(i * secondsPerBar) for i in [250, 500, 1000]] # Quarter note, half note, whole note

# backPointIntensity = [40, 40] # 1 motor, 2 motors
backPointIntensity = [50, 40, 30, 40, 50, 40, 30] # cc, d, e, ff, gg, a, b

keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']','\\']
playbackKeys = ['z', 'x', 'c', 'v', 'b']
convertToWhiteNote = [0,0,1,2,2,3,3,4,4,5,6,6,7,7,8,9,9,10,10,11,12,12,13,13]
noteNames = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]


####################
# Global Variables #
####################

GVARS = {
  'sound': None,
  'isRunning': True, # For computer keyboard input

  'randomMelodyNote': [7,1],
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

  'keyNum': None, # Number of note to be vibrated, between 0 and 23
  'previousKeyNum': None, # Key num of the previous note, used for beeping during mode 5
  'durationNum': 0, # See `durations` array
  'whiteNote': None, # 0-6, refers to which "white note" the note is (E.g. for C#, it's C)
  'vibrationStartTime':  0,
  'moveRangePhase': 0, # Phases within moving through the range
  'newOctave': 0, # 1 if moved up an octave, -1 if moved down an octave
  'hasStartedVibration': 0, # Whether the back point has started vibrating yet
}


##############
# Main Logic #
##############

def doRandomNote():
  startVibrations(random.choice(validNotes[0:7] if GVARS['keyNum'] == None else validNotes)) # Start off in the lower octave
  
def playAudio(midiNote):
  if GVARS['sound']:
    GVARS['sound'].stop()
  sampleRate = 44100
  freq = int(2**((midiNote-69)/12)*440)
  arr = numpy.array([4096 * numpy.sin(2.0 * numpy.pi * freq * x / sampleRate) for x in range(0, sampleRate)]).astype(numpy.int16)
  arr2 = numpy.c_[arr,arr]
  GVARS['sound'] = pygame.sndarray.make_sound(arr2)
  GVARS['sound'].play(-1)
  f.write(f"Audio {midiNote} at {time.time_ns()}, index {GVARS['melodyIndex']}\n")

def startVibrations(keyNum, durationNum = 0):
  resetVibrations()
  GVARS['durationNum'] = durationNum
  GVARS['whiteNote'] = convertToWhiteNote[keyNum%12]
  if GVARS['keyNum'] == None:
    GVARS['newOctave'] = int(keyNum/12) # 0 for low octave, 1 for high octave
  if GVARS['keyNum'] != None and (GVARS['isGuessed'] or mode == 4 or mode == 5):
    if isBrailleOctaves:
      interval = abs(convertToWhiteNote[int(GVARS['keyNum'])]-convertToWhiteNote[int(keyNum)])
      if interval > 4: # 6th and more
        GVARS['newOctave'] = int(keyNum/12) # 0 for low octave, 1 for high octave 
      elif interval in [3,4]: # 4th or 5th
        if int(int(GVARS['keyNum'])/12) != int(keyNum/12):
          GVARS['newOctave'] = int(keyNum/12) # 0 for low octave, 1 for high octave
        else:
          GVARS['newOctave'] = None
      else:
        GVARS['newOctave'] = None
    else:
      if int(int(GVARS['keyNum'])/12) > int(keyNum/12):
        GVARS['newOctave'] = -1
      elif int(int(GVARS['keyNum'])/12) < int(keyNum/12):
        GVARS['newOctave'] = 1 
      else:
        GVARS['newOctave'] = None
  GVARS['previousKeyNum'] = GVARS['keyNum']
  GVARS['keyNum'] = keyNum
  GVARS['moveRangePhase'] = 0
  GVARS['hasStartedVibration'] = 0
  GVARS['vibrationStartTime'] = time.time_ns()
  if writeToFile:
    f.write(f"Vibrate {keyNum},{durationNum} at {GVARS['vibrationStartTime']}, index {GVARS['melodyIndex']}\n")
  print(f"Vibrate {noteNames[keyNum%12]}: {keyNum},{durationNum}")

def updateVibrations():
  if GVARS['whiteNote'] != None:
    if isBrailleOctaves:
      vibrateFrontPoint()
    else:
      moveRange()
    vibrateBackPoint()

# For old way of indicating octaves
def moveRange():
  if (GVARS['newOctave'] != None and GVARS['moveRangePhase'] != 4 and time.time_ns() - GVARS['vibrationStartTime'] >= octaveTime/4*GVARS['moveRangePhase'] * 1000000):
    pinIndex = rangePins[int(GVARS['moveRangePhase'])] if GVARS['newOctave'] == 1 else rangePins[3 - int(GVARS['moveRangePhase'])]
    player.submit_dot("range" + str(GVARS['moveRangePhase']), "VestFront", [{"index": pinIndex, "intensity": 100}], int(octaveTime/4))
    if (GVARS['moveRangePhase'] == 0):
      f.write(f"Sweep {'Right' if GVARS['newOctave'] == 1 else 'Left'} at {time.time_ns()}\n")
    GVARS['moveRangePhase'] = GVARS['moveRangePhase'] + 1

# For Braille octave notation
def vibrateFrontPoint():
  numPhase = len(octavePins[0])
  if (GVARS['newOctave'] != None and GVARS['moveRangePhase'] != numPhase and time.time_ns() - GVARS['vibrationStartTime'] >= octaveTime/numPhase*GVARS['moveRangePhase'] * 1000000):
    if (GVARS['newOctave'] == None or GVARS['moveRangePhase'] == None):
      print(f"Hit the bug, octave: {GVARS['newOctave']}, moveRangePhase: {GVARS['moveRangePhase']}")
      f.write(f"Hit the bug, octave: {GVARS['newOctave']}, moveRangePhase: {GVARS['moveRangePhase']} at {time.time_ns()}\n")
      return
    pinIndex = octavePins[int(GVARS['newOctave'])][int(GVARS['moveRangePhase'])]
    player.submit_dot("octave" + str(GVARS['moveRangePhase']), "VestFront", [{"index": pinIndex, "intensity": octaveIntensity}], int(octaveTime/numPhase))
    if (GVARS['moveRangePhase'] == 0):
      print(f"Octave {'Top' if GVARS['newOctave'] == 1 else 'Bottom'}")
      f.write(f"Octave {'Top' if GVARS['newOctave'] == 1 else 'Bottom'} at {time.time_ns()}\n")
    GVARS['moveRangePhase'] = GVARS['moveRangePhase'] + 1

def vibrateBackPoint():
  timeToWait = octaveTime if (GVARS['newOctave'] != None or mode != 0) else 0 # Go immediately if mode == 0 and no sweep for the range
  if (GVARS['hasStartedVibration'] == 0 and time.time_ns() - GVARS['vibrationStartTime'] >= timeToWait * 1000000):
    for i in backPointPins[GVARS['whiteNote']]:
      # player.submit_dot(i, "VestBack", [{"index": i, "intensity": backPointIntensity[len(backPointPins[GVARS['whiteNote']]) > 1]}], durations[GVARS['durationNum']])
      player.submit_dot(i, "VestBack", [{"index": i, "intensity": backPointIntensity[GVARS['whiteNote']]}], durations[GVARS['durationNum']])
    GVARS['hasStartedVibration'] = 1

def resetVibrations():
  player.submit_dot("range0", "VestFront", [{"index": 90, "intensity": 0}], 1)
  player.submit_dot("range1", "VestFront", [{"index": 91, "intensity": 0}], 1)
  for i in range(20):
    player.submit_dot(i, "VestBack", [{"index": pins[i], "intensity": 0}], 1)

def skipToPrevious():
  resetVibrations()
  GVARS['lastNoteTime'] = 0
  GVARS['isGuessed'] = True

def continuousLoop(): # Code that runs every loop
  updateVibrations()
  playbackCommand = GVARS['playbackCommand'] # To avoid situtations where it changes during use
  if playbackCommand == 1: # Skip to beginning
    GVARS['melodyIndex'] = 0
    GVARS['beatIndex'] = 0
    skipToPrevious()
  elif playbackCommand == 2: # Skip to previous bar
    while True:
      GVARS['melodyIndex'] = GVARS['melodyIndex'] - 1 if GVARS['melodyIndex'] != 0 else totalNotes - 1
      GVARS['beatIndex'] = GVARS['beatIndex'] - beatLegend[melody[GVARS['melodyIndex']][1]] \
        if GVARS['beatIndex'] >= beatLegend[melody[GVARS['melodyIndex']][1]] \
        else totalBeats - beatLegend[melody[GVARS['melodyIndex']][1]]
      if (GVARS['beatIndex'] % 4 == 0):
        skipToPrevious()
        break
  elif playbackCommand == 3: # Skip to previous note
    GVARS['melodyIndex'] = GVARS['melodyIndex'] - 1 if GVARS['melodyIndex'] != 0 else totalNotes - 1
    GVARS['beatIndex'] = GVARS['beatIndex'] - beatLegend[melody[GVARS['melodyIndex']][1]] \
      if GVARS['beatIndex'] >= beatLegend[melody[GVARS['melodyIndex']][1]] \
      else totalBeats - beatLegend[melody[GVARS['melodyIndex']][1]]
    skipToPrevious()
  elif playbackCommand == 4: # Play
    pressPlayNote()
  elif playbackCommand == 5: # Pause
    resetVibrations()
    GVARS['beginMelody'] = False
    if GVARS['sound']:
      GVARS['sound'].stop()    
    GVARS['lastNoteTime'] = 0
  if (GVARS['playbackCommand'] == playbackCommand): # If playbackCommand changed, don't get rid of it just yet
    GVARS['playbackCommand'] = 0

  noteDuration = beatLegend[melody[GVARS['melodyIndex']][1] if mode != 2 else GVARS['randomMelodyNote'][1]] * 250000000 * secondsPerBar
  # Note: for mode 8, the duration is half as much
  if GVARS['beginMelody'] and \
    ((mode == 2 or mode == 3 or mode == 8) and GVARS['isGuessed'] or mode == 4 or mode == 5) \
    and time.time_ns() - GVARS['lastNoteTime'] >= noteDuration * (0.5 if mode == 8 else 1) \
    or mode == 7 and GVARS['isGuessed']:

    newKeyNum =  GVARS['keyNum']
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
          if GVARS['sound']:
            GVARS['sound'].stop()
          return # This used to be continue
      newKeyNum = melody[GVARS['melodyIndex']][0]
    else: # mode == 2
      while True:
        newNoteIndex = validNotes.index(GVARS['randomMelodyNote'][0]) + random.randint(-3, 3)
        if newNoteIndex < 14 and newNoteIndex >= 0:
          break
      GVARS['randomMelodyNote'] = [validNotes[newNoteIndex], random.choice([0,1])]
      newKeyNum = GVARS['randomMelodyNote'][0]
    if mode == 4 or mode == 8:
      playAudio(newKeyNum + 60)
    GVARS['lastNoteTime'] = time.time_ns()
    if mode != 4 and mode != 7 and mode != 8:
      startVibrations(newKeyNum, melody[GVARS['melodyIndex']][1] if mode != 2 else GVARS['randomMelodyNote'][1])
    else:
      GVARS['keyNum'] = newKeyNum  
    GVARS['isGuessed'] = False

def pressPlayNote(): # F2 on piano, \ on computer
  if mode in [2,3,4,5,8]: # Melody
    GVARS['beginMelody'] = True
    if not GVARS['isGuessed'] and (mode == 2 or mode == 3):
      startVibrations(GVARS['keyNum'], melody[GVARS['melodyIndex']][1] if mode == 3 else GVARS['randomMelodyNote'][1])
    if not GVARS['isGuessed'] and mode == 8:
      playAudio(GVARS['keyNum'] + 60)
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
  if writeToFile and (key == Key.esc or hasattr(key, 'char') and (key.char.isnumeric() and mode == 6 or key.char == '\\')):
    f.write(f"Computer {key} at {time.time_ns()}\n")
    print(f"Computer {key}")

  if key == Key.esc:
    resetVibrations()
    GVARS['isRunning'] = False
  if hasattr(key, 'char') and key.char == '\\':
    pressPlayNote()
  if not isPiano:
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

  if device_id is None:
    input_id = pygame.midi.get_default_input_id()
  else:
    input_id = device_id

  i = pygame.midi.Input(input_id)

  pg.display.set_mode((1, 1))

  going = True
  while going and GVARS["isRunning"]:

    continuousLoop()

    # Code for when a piano key is pressed
    events = event_get()
    for e in events:
      if e.type in [pygame.midi.MIDIIN] and e.status == 144 and e.data2 == 0: # Note being raised up
        continue
      if writeToFile and e.type in [pygame.midi.MIDIIN] and e.status == 144:
        f.write(f"MIDI {e.data1} at {time.time_ns()}\n")

      if e.type in [pg.QUIT]:
        going = False
      if e.type in [pygame.midi.MIDIIN] and e.data1 == 108: # C8
        resetVibrations()
        going = False
      elif e.type in [pygame.midi.MIDIIN] and e.status == 144 and e.data1 >= 60 and e.data1 < 84: # C4 to C6
        if mode == 0:
          startVibrations(e.data1 - 60)
        elif mode == 1:
          if GVARS['keyNum'] != None:
            if e.data1 - 60 == GVARS['keyNum']:
              pygame.mixer.music.load("jonathan/correct.wav")
              f.write(f"Audio correct at {time.time_ns()}\n")
              GVARS['isGuessed'] = True
            else:
              pygame.mixer.music.load("jonathan/wrong.mp3")
              f.write(f"Audio wrong at {time.time_ns()}\n")
            pygame.mixer.music.play()
        elif mode in [2,3,5,7,8]:
          if GVARS['keyNum'] != None:
            if e.data1 - 60 == GVARS['keyNum'] or (mode == 5 and GVARS['previousKeyNum'] != None and e.data1 - 60 == GVARS['previousKeyNum']):
              GVARS['isGuessed'] = True
              if mode == 8:
                GVARS['lastNoteTime'] = time.time_ns() # So that it doesn't immediately go to the next note
            elif mode != 8:
              pygame.mixer.music.load("jonathan/wrong.mp3")
              f.write(f"Audio wrong at {time.time_ns()}\n")
              pygame.mixer.music.play()
      elif e.type in [pygame.midi.MIDIIN] and e.status == 144 and e.data1 in [36, 38, 40, 41, 43]: # C2 to G2
        if mode in [1,2] and e.data1 == 41:
          pressPlayNote()
        elif mode in [4,5,3,7,8]:
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
if writeToFile:
  now = datetime.now()
  dt_string = now.strftime("%Y%m%d,%H%M%S")
  f = open(f"{dt_string}_{mode}", "w")
  f.write(f"Mode {mode}\n")
  f.write(f"Melody {melodyIndex}: {melodies[melodyIndex]}\n")
  f.write(f"Chunk {melodyChunk}: {melody}\n")
  f.write(f"Speed {secondsPerBar}\n")
print("Begin!")

listener = Listener(
  on_press=on_press)
listener.start()
if isPiano:
  midi_input_main(1)
else:
  while GVARS['isRunning']:
    continuousLoop()
if writeToFile:
  f.close()
