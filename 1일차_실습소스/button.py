from machine import Pin
from time import sleep

btn_a = Pin(36, Pin.IN)
btn_b = Pin(39, Pin.IN)
while True:
    print(btn_a.value(),
          btn_b.value())
    sleep(0.2)


