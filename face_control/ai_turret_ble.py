# ai_turret_ble.py  ----  얼굴 추적 카메라 터렛 (서보 2축 pan/tilt) 수신 펌웨어
#   웹앱이 보내는 형식: "P:90,T:60"  (P=수평/pan, T=수직/tilt)  또는 "CENTER"
#   서보: S1=pan(수평), S2=tilt(수직)  (연결 단자에 맞게 채널 수정)
from time import sleep
import ble_library
import bluetooth
from ai_ponybot import i2c, PonyMotor, PonyServo, PonyOLED

motor = PonyMotor(i2c)
servo = PonyServo(motor.pwm)      # 서보는 모터와 PWM 공유
oled  = PonyOLED(i2c)

ble = bluetooth.BLE()
p = ble_library.BLESimplePeripheral(ble, 'ESP-000')   # 웹앱 namePrefix 'ESP'와 일치

# ---- 서보 채널·안전 범위 ----
PAN_CH,  TILT_CH  = 1, 2          # S1=수평, S2=수직
PAN_MIN, PAN_MAX  = 10, 170
TILT_MIN, TILT_MAX = 40, 150
pan, tilt = 90, 90                # 시작(정면)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def apply():
    servo.set_angle(PAN_CH, pan)
    servo.set_angle(TILT_CH, tilt)

apply()

def oled_show(a, b=""):
    for i in range(1, len(oled.buffer)):
        oled.buffer[i] = 0
    oled.draw_text(0, 0, a)
    oled.draw_text(0, 16, b)
    oled.show()

def on_rx(v):
    global pan, tilt
    data = v.strip().upper()
    if not data:
        return
    try:
        if data in ('CENTER', 'HOME'):
            pan, tilt = 90, 90
        else:
            for part in data.split(','):          # "P:90,T:60"
                if ':' not in part:
                    continue
                k, val = part.split(':')
                k = k.strip()
                if   k == 'P': pan  = clamp(int(float(val)), PAN_MIN,  PAN_MAX)
                elif k == 'T': tilt = clamp(int(float(val)), TILT_MIN, TILT_MAX)
        apply()
        oled_show("TURRET", "P%-3d T%-3d" % (pan, tilt))
    except Exception as e:
        print("parse err:", data, e)

p.on_write(on_rx)
oled_show("BLE WAITING", "name ESP-000")
print("얼굴 추적 터렛 대기 중... (기기명 ESP-000)")

while True:
    if not p.is_connected():
        oled_show("BLE WAITING", "name ESP-000")
    sleep(0.3)
