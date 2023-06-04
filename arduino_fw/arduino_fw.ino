String current_arg = "";
String serial_line = "";

void setup(){
  Serial.begin(115200);
}

void loop() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    if(c == '\n'){
      processCommand();
      cleanUp();
    }
    else{
      serial_line += c;
    }
  }
}

void getSlice(){
  int pos = serial_line.indexOf(":");
  if(pos == -1){
    current_arg = serial_line;
    serial_line = "";
  }
  else{
    // Current arg is the bit upto the colon;
    current_arg = serial_line.substring(0, pos);
    // serial line becomes the remaining bit;
    serial_line = serial_line.substring(pos + 1);
  }
}

void cleanUp(){
  serial_line = "";
}

void processCommand(){
  getSlice();

  if(current_arg.equals("*IDN?")){
    Serial.print("Student Robotics:Arduino:X:2.0\n");
    return;
  }

  else if(current_arg.equals("*STATUS?")){
    Serial.print("Yes\n");
    return;
  }

  else if(current_arg.equals("*RESET?")){
    Serial.print("NACK:Reset not supported\n");
    return;
  }

  else if(current_arg.equals("PIN")){
    getSlice();
    int pin = current_arg.toInt();
    getSlice();

    if(current_arg.equals("MODE")){
      getSlice();
      if(current_arg.equals("GET?")){
        int mode = getPinMode(pin);
        if(mode == INPUT){
          Serial.print("INPUT\n");
          return;
        }
        else if(mode == INPUT_PULLUP){
          Serial.print("INPUT_PULLUP\n");
          return;
        }
        else if(mode == OUTPUT){
          Serial.print("OUTPUT\n");
          return;
        }
      }
      else if(current_arg.equals("SET")){
        getSlice();
        if(current_arg.equals("INPUT")){
          pinMode(pin, INPUT);
          Serial.print("ACK\n");
          return;
        }
        else if(current_arg.equals("INPUT_PULLUP")){
          pinMode(pin, INPUT_PULLUP);
          Serial.print("ACK\n");
          return;
        }
        else if(current_arg.equals("OUTPUT")){
          pinMode(pin, OUTPUT);
          Serial.print("ACK\n");
          return;
        }
        else if(current_arg.equals("INPUT_ANALOG")){
          pinMode(pin, INPUT);
          Serial.print("ACK\n");
          return;
        }
      }

    }

    else if(current_arg.equals("DIGITAL")){
      getSlice();
      if(current_arg.equals("GET?")){
        if(digitalRead(pin)){
          Serial.print("1\n");
          return;
        }
        else{
          Serial.print("0\n");
          return;
        }
      }
      else if(current_arg.equals("SET")){
        getSlice();
        if(current_arg.equals("1")){
          digitalWrite(pin, HIGH);
          Serial.print("ACK\n");
          return;
        }
        else{
          digitalWrite(pin, LOW);
          Serial.print("ACK\n");
          return;
        }
      }
    }

    else if(current_arg.equals("ANALOG")){
      getSlice();
      if(current_arg.equals("GET?")){
        Serial.print(analogRead(pin));
        Serial.print("\n");
        return;
      }
    }
  }

  else if(current_arg.equals("ULTRASOUND")){
    getSlice();
    int pulse = current_arg.toInt();
    getSlice();
    int echo = current_arg.toInt();
    getSlice();
    if(current_arg.equals("MEASURE?")){
      pinMode(pulse, OUTPUT);
      pinMode(echo, INPUT);
      
      digitalWrite(pulse, LOW);
      delayMicroseconds(2);
      digitalWrite(pulse, HIGH);
      delayMicroseconds(5);
      digitalWrite(pulse, LOW);

      int duration = pulseIn(echo, HIGH, 60000);
      Serial.print(microsecondsToMm(duration));
      Serial.print("\n");
      return;
    }
  }

  Serial.print("NACK:Invalid command\n");
}

long microsecondsToMm(long microseconds) {
  // The speed of sound is 340 m/s or 29 microseconds per centimeter.
  // The ping travels out and back, so to find the distance we need half
  // 10 x (us / 29 / 2)
  return (5 * microseconds / 29);
}

int getPinMode(uint8_t pin){
  uint8_t bit = digitalPinToBitMask(pin);
  uint8_t port = digitalPinToPort(pin);

  volatile uint8_t *reg = portModeRegister(port);
  if (*reg & bit) return (OUTPUT);

  volatile uint8_t *out = portOutputRegister(port);
  return ((*out & bit) ? INPUT_PULLUP : INPUT);
}
