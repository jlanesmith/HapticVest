import random

melodyLength = 20
beatNum = 0
note = 12
beatLegend = [1,2,4]
melody = "["

for i in range(melodyLength):
    note = note + random.randint(-4, 4)
    note = max(min(note,24),0)
    duration = None
    if beatNum == 0:
      duration = random.choice([0,1,2])
    elif beatNum == 1 or beatNum == 2:
      duration = random.choice([0,1])
    else:
      duration = 0
    beatNum = (beatNum + beatLegend[duration]) % 4
    melody = melody + "[" + str(note) + "," + str(duration) + "]"
    if i != melodyLength - 1:
        melody = melody + ", "

melody = melody + "]"

print(melody)

