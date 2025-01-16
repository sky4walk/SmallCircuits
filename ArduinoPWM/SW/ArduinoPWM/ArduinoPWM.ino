// PWM Pins R3, UNO: 3, 5, 6, 9, 10, 11
int PWM_Pin = 3;
int analogPin  = A0;

void setup() {
  Serial.begin(9600);
  pinMode(PWM_Pin, OUTPUT);
  pinMode(analogPin, INPUT);
  analogWriteResolution(8);
}

void loop() {
  int Potiwert = analogRead(analogPin);
  Serial.println(Potiwert);
  // analogRead values go from 0 to 1023, analogWrite values from 0 to 255
  analogWrite(PWM_Pin,Potiwert/4);
  delay(500);
}