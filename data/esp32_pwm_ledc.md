\# ESP32 PWM（LEDC）社内標準



\## 基本方針

\- ESP32では `analogWrite()` は使用しない

\- PWMは \*\*LEDC（LED Control）API\*\* を使用する

\- Arduino互換APIに依存しない



\## LEDCの基本構成

\- チャンネル数：最大16

\- 同一チャンネルを複数GPIOに割り当て可能

\- 周波数・分解能はチャンネル単位で共通



\## 基本サンプル（単一チャンネル・複数GPIO）



```cpp

const int pwmChannel = 0;

const int pwmFreq = 5000;

const int pwmResolution = 8;



const int pinA = 18;

const int pinB = 19;



void setup() {

&nbsp; ledcSetup(pwmChannel, pwmFreq, pwmResolution);

&nbsp; ledcAttachPin(pinA, pwmChannel);

&nbsp; ledcAttachPin(pinB, pwmChannel);



&nbsp; ledcWrite(pwmChannel, 128);

}



void loop() {

}



