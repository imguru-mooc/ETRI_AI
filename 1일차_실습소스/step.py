from machine import I2C, Pin
import mpu6050, math
from time import sleep, ticks_ms, ticks_diff

i2c = I2C(0, scl=Pin(21), sda=Pin(22))
imu = mpu6050.accel(i2c, 0x69)
count, last = 0, 0
while True:
    a = imu.get_values()
    m = math.sqrt(a['AcX']**2+a['AcY']**2+a['AcZ']**2)
    now = ticks_ms()
    if m > 24000 and ticks_diff(now, last) > 300:
        count += 1; last = now
        print('걸음 수:', count)
    sleep(0.02)
