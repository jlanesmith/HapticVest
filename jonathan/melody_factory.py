import random

# Constants
includeAccidentals = False
beatLength = 24
beatLegend = [1,2,4]
validNotes = [0,2,4,5,7,9,11,12,14,16,17,19,21,23,24]

# Variables
beatNum = 0
note = 12 if includeAccidentals else 7 # start at note 12
melody = "["

while beatNum < beatLength:
  if includeAccidentals:
    note = note + random.randint(-4, 4)
    note = max(min(note,24),0)
  else:
    note = note + random.randint(-3, 3)
    note = max(min(note,len(validNotes)-1),0)
  duration = None
  if beatNum%4 == 0:
    duration = random.choice([0,1]) # Don't do [0,1,2] cause 2s are too long
  elif beatNum%4 == 1 or beatNum%4 == 2:
    duration = random.choice([0,1])
  else:
    duration = 0
  beatNum = beatNum + beatLegend[duration]
  melody = melody + "[" + str(note if includeAccidentals else validNotes[note]) + "," + str(duration) + "]"
  if beatNum < beatLength:
    melody = melody + ", "

melody = melody + "]"

print(melody)

