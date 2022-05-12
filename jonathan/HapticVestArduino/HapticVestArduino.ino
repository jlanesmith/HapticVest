/*
 * This code is for a custom haptic vest I created using 16 ERM motors. 
 * However, it was later decided to use a bHaptics vest instead.
 */

// 9 main pins, 2 accidental pins, 5 ANALOG range pins
const int pins[16] = {52,50,45,48,42,43,46,51,44,53,49,9,10,11,13,12};

const int rangeTime = 500; // milliseconds
const int sweepTime[2] = {300, 180}; // milliseconds
const int accidentalTime = 500; // milliseconds

const char keys16[16] = {'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k'};
const char keys24[24] = {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']'};

const int sweepDirections[12] = {0,0,1,2,2,3,3,4,4,5,6,6};
const int accidentals[12] = {-1,1,-1,0,-1,-1,1,-1,1,-1,0,-1}; // -1 none, 0 flat, 1 sharp

const int directions[7][5][3] = {
  {{1,2,3},{4,5,6},{7,8,9},{0,0,0},{0,0,0}}, // down
  {{0,0,3},{0,2,6},{1,5,9},{0,4,8},{0,0,7}}, // down-left
  {{3,6,9},{2,5,8},{1,4,7},{0,0,0},{0,0,0}}, // left
  {{0,0,9},{0,8,6},{7,5,3},{0,4,2},{0,0,1}}, // up-left
  {{7,8,9},{4,5,6},{1,2,3},{0,0,0},{0,0,0}}, // up
  {{0,0,7},{0,4,8},{1,5,9},{0,2,6},{0,0,3}}, // up-right
  {{1,4,7},{2,5,8},{3,6,9},{0,0,0},{0,0,0}} // right
};


int state = 0; // 0 is nothing, 1 is range moving, 2 is sweep, 3 is accidental
unsigned long startTime = 0;

char inChar = '\0';
int keyNum = 0;
float currentRangePosition = 2; // 2 is in the middle (0 to 4)
float newRangePosition = 2; // 2 is in the middle (0 to 4)
int currentSweepPhase = 4; // 0 to 2 or 4 (total of 3 or 5)
bool accidentalOn = false; // Whether accidental is vibrating

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  for (auto pin : pins) {
    pinMode(pin, OUTPUT);
  }
}

void looptest() {
   // For testing
   if (Serial.available() > 0) {
    inChar = Serial.read();
    for (int i = 0; i < 16; i++) {
      if (inChar == keys16[i]) {
        Serial.print(i);
        digitalWrite(pins[i], HIGH);
        delay(accidentalTime);
        digitalWrite(pins[i], LOW);   
      }   
    }
   }
}

void loop() {

  // New note detected
  if(state == 0 && Serial.available() > 0) {
    inChar = Serial.read();
    for (int i = 0; i < 24; i++) {
      if (inChar == keys24[i]) {
        keyNum = i;//random(0,24);
        newRangePosition = (float(keyNum))/23.0*4.0; // Between 0 and 4
        state = 1;
        startTime = millis();
        break;
      }
    }

  // Perform range motion
  } else if (state == 1) {
    unsigned long curTime = millis();
    if (curTime - startTime < rangeTime) {
      float percDone = (float(curTime - startTime))/rangeTime;
      setPwmAnalogValues(currentRangePosition + (newRangePosition-currentRangePosition)*percDone);
    } else if (curTime - startTime >= rangeTime) {
      setPwmAnalogValues(newRangePosition);
      currentRangePosition = newRangePosition;
      state = 2;
      startTime = millis();
    }

  // Perform sweep
  } else if (state == 2) {
    int direc = sweepDirections[keyNum%12]; 
    int timing = sweepTime[direc%2]; // cardinal or not
    int newPhase = (millis()-startTime)/timing; // this will round down and go from 0 to 3 or 5
    if (newPhase != currentSweepPhase) {
      if (currentSweepPhase < (direc%2 ? 5 : 3)) {
        for (int i = 0; i < 3; i++) {
          if (directions[direc][currentSweepPhase][i] != 0) {
            digitalWrite(pins[directions[direc][currentSweepPhase][i]-1], LOW);
          }
        }
      }
      if (newPhase < (direc%2 ? 5 : 3)) {
        for (int i = 0; i < 3; i++) {
          if (directions[direc][newPhase][i] != 0) {
            digitalWrite(pins[directions[direc][newPhase][i]-1], HIGH);
          }
        }
      } else {
        state = 3;
        startTime = millis();
      }
      currentSweepPhase = newPhase;
    } 

  // Do accidental
  } else if (state == 3) {     
    if (accidentals[keyNum%12] != -1) {
      if ((millis() - startTime < accidentalTime) && !accidentalOn) {
        digitalWrite(pins[9 + accidentals[keyNum%12]], HIGH); 
        accidentalOn = true;
      } else if (millis() - startTime >= accidentalTime) {
        digitalWrite(pins[9 + accidentals[keyNum%12]], LOW);
        accidentalOn = false;
        state = 0;
      }
    } else {
      state = 0;
    }
  }
}

void setPwmAnalogValues(float num) {
  for (int i = 0; i < 5; i++) {
    if (num <= (i-1) || num >= (i+1)) {
      analogWrite(pins[11+i], 0);
    } else if (num > (i-1) && num <= i) {
      analogWrite(pins[11+i], int((num + 1 - i)*255));
    } else if (num < (i+1) && num > i) {
      analogWrite(pins[11+i], int((i + 1 - num)*255));
    }
  }
}
