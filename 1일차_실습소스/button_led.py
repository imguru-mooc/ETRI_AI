from neopixel import NeoPixel
from machine import Pin
from time import sleep

np = NeoPixel(Pin(13, Pin.OUT), 25)
btn_a = Pin(36, Pin.IN)   # 켜기
btn_b = Pin(39, Pin.IN)   # 끄기

while True:
    if btn_a.value() == 0:
        for i in range(25): np[i] = (0, 12, 0)
    elif btn_b.value() == 0:
        for i in range(25): np[i] = (0, 0, 0)
    np.write()
    sleep(0.05)



