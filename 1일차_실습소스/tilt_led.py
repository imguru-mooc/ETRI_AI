from machine import I2C, Pin
import mpu6050
from neopixel import NeoPixel
from time import sleep

i2c=I2C(0,scl=Pin(21),sda=Pin(22)); imu=mpu6050.accel(i2c,0x69)
np=NeoPixel(Pin(13,Pin.OUT),25)
clamp=lambda v: max(0, min(4, v))
while True:
    a=imu.get_values()
    col=clamp(2 - a['AcY']//6000)   # 기울기→열
    row=clamp(2 + a['AcX']//6000)   # 기울기→행
    for i in range(25): np[i]=(0,0,0)
    np[row*5+col]=(0,0,12)
    np.write(); sleep(0.05)
