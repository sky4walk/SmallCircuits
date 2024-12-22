int PWM_Pin = 3;
int pwm_value = 0;

void setup() {


  Serial.begin(9600);

    pinMode(PWM_Pin, OUTPUT);
    pinMode(pwm_value, INPUT);
}

void loop() {
  
  int Potiwert = analogRead(pwm_value);
  Serial.println(Potiwert);
  analogWrite(PWM_Pin,Potiwert/4);
  delay(500);
  
}