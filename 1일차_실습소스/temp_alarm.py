from machine import I2C, Pin
import mpu6050              # mpu6050.py 업로드 필요
from time import sleep
from neopixel import NeoPixel

i2c = I2C(0, scl=Pin(21), sda=Pin(22))
imu = mpu6050.accel(i2c, 0x69)
np = NeoPixel(Pin(13, Pin.OUT), 25)
while True:
    v = imu.get_values()
    t = v['Tmp']
    color = (12,0,0) if t >= 30 else (0,10,0)  # 40↑ 빨강
    for i in range(25): np[i] = color
    np.write(); print(t); sleep(0.5)
