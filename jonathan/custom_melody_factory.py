from pynput.keyboard import Key, Listener

# Space = finish melody, Esc = finish melody and quit
keys = ['1', '2', '3', '4', '5', '6', '7', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i']
makeLongerKey = 'l'
validNotes = [0,2,4,5,7,9,11,12,14,16,17,19,21,23,24]

melody = "["

def finishMelody():
  global melody
  melody = melody + "]"
  print(melody)
  melody = "["

def on_press(key):
  global melody
  print('{0} pressed'.format(
      key))
  if key == Key.esc:
    # Stop listener
    finishMelody()
    return False
  elif key == Key.space:
    finishMelody()
  elif hasattr(key, 'char') and key.char == makeLongerKey:
    if melody[-2] == "0":
      melody = melody[:-2] + "1]"
  elif hasattr(key, 'char') and key.char in keys:
    if melody[-1] != '[':
      melody = melody + ", "
    melody = melody + "[" + str(validNotes[keys.index(key.char)]) + "," + "0]"
  

with Listener(on_press=on_press) as listener:
  listener.join()

