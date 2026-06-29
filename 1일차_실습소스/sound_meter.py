from machine import Pin, ADC
from neopixel import NeoPixel
from time import sleep

mic = ADC(Pin(35)); mic.atten(ADC.ATTN_11DB)
np = NeoPixel(Pin(13, Pin.OUT), 25)
while True:
    s = [mic.read() for _ in range(100)]
    level = max(s) - min(s)
    n = min(level // 80, 25)         # 켤 개수
    for i in range(25):
        np[i] = (8,0,0) if i < n else (0,0,0)
    np.write(); sleep(0.05)
