from neopixel import NeoPixel
from machine import Pin
from time import sleep

np = NeoPixel(Pin(13, Pin.OUT), 25)  # 내장 5x5

while True:
    for i in range(25):       # 하나씩 켜기
        np[i] = (10, 0, 0)     # 빨강(약하게)
        np.write()
        sleep(0.05)
    for i in range(25):       # 하나씩 끄기
        np[i] = (0, 0, 0)
        np.write()
        sleep(0.05)
