from machine import Pin, ADC
from time import sleep

mic = ADC(Pin(35))           # 내장 마이크
mic.atten(ADC.ATTN_11DB)     # 0~3.3V

while True:
    s = [mic.read() for _ in range(100)]
    level = max(s) - min(s)   # 소리 크기
    print('소리 크기:', level)
    sleep(0.1)





