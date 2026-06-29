from neopixel import NeoPixel
from machine import Pin
from time import sleep

np = NeoPixel(Pin(13, Pin.OUT), 25)

while True:
    for v in range(0, 60, 2):      # 점점 밝게
        for i in range(25): np[i] = (v, 0, 0)
        np.write(); sleep(0.03)
    for v in range(60, -1, -2):    # 점점 어둡게
        for i in range(25): np[i] = (v, 0, 0)
        np.write(); sleep(0.03)




