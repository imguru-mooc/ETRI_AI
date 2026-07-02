from ai_ponybot import i2c, PonyMotor, PonyServo
from time import sleep

motor = PonyMotor(i2c)
servo = PonyServo(motor.pwm)

def servo_move(servo_num, pre_angle, after_angle, delay=0.005):
    if pre_angle > after_angle:
        for i in range(pre_angle, after_angle- 1, -1):
            servo.set_angle(servo_num, i)
            sleep(delay)
    else:
        for i in range(pre_angle, after_angle + 1):
            servo.set_angle(servo_num, i)
            sleep(delay)

servo_move(4,   90,  0)   # S4 집게: 벌리기 → 집기
