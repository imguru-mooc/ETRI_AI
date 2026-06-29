from machine import I2C, Pin

i2c = I2C(0, scl=Pin(21),
          sda=Pin(22))
print(i2c.scan())






