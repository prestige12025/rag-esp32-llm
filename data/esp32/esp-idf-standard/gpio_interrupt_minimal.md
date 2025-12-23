\# ESP-IDF GPIO Interrupt Basic Example



\## 対象

\- ESP32 / ESP32-S3

\- ESP-IDF v4.x / v5.x



\## 概要

ESP-IDFでGPIO割り込みを使用する最小構成例。



\## サンプルコード



```c

\#include "freertos/FreeRTOS.h"

\#include "freertos/task.h"

\#include "driver/gpio.h"

\#include "esp\_log.h"



\#define GPIO\_INPUT\_IO 25

\#define GPIO\_INPUT\_PIN\_SEL (1ULL << GPIO\_INPUT\_IO)



static const char \*TAG = "GPIO\_ISR";



static void IRAM\_ATTR gpio\_isr\_handler(void \*arg)

{

&nbsp;   int gpio\_num = (int)arg;

&nbsp;   // ISR内ではログやmallocは禁止

&nbsp;   ets\_printf("GPIO %d interrupt\\n", gpio\_num);

}



void app\_main(void)

{

&nbsp;   gpio\_config\_t io\_conf = {

&nbsp;       .intr\_type = GPIO\_INTR\_POSEDGE,

&nbsp;       .mode = GPIO\_MODE\_INPUT,

&nbsp;       .pin\_bit\_mask = GPIO\_INPUT\_PIN\_SEL,

&nbsp;       .pull\_down\_en = GPIO\_PULLDOWN\_DISABLE,

&nbsp;       .pull\_up\_en = GPIO\_PULLUP\_ENABLE,

&nbsp;   };



&nbsp;   gpio\_config(\&io\_conf);



&nbsp;   gpio\_install\_isr\_service(0);

&nbsp;   gpio\_isr\_handler\_add(GPIO\_INPUT\_IO, gpio\_isr\_handler, (void \*)GPIO\_INPUT\_IO);



&nbsp;   ESP\_LOGI(TAG, "GPIO interrupt initialized");

}



