from machine import Pin
from neopixel import NeoPixel
from time import sleep, ticks_ms, ticks_diff
import random

np = NeoPixel(Pin(13, Pin.OUT), 25)
btn = Pin(36, Pin.IN)
while True:
    for i in range(25): np[i]=(0,0,0)
    np.write()
    sleep(random.uniform(1, 3))      # 무작위 대기
    for i in range(25): np[i]=(0,12,0)  # 초록 = 지금!
    np.write()
    t0 = ticks_ms()
    while btn.value()==1: pass        # 누를 때까지
    print('반응:', ticks_diff(ticks_ms(), t0), 'ms')
    sleep(1)

