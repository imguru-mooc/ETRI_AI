# ai_arm_ble.py  ----  로봇팔 4서보 수신 (B:베이스 S:어깨 E:팔꿈치 G:집게)
#   웹앱 형식: "B:120,S:80,E:90,G:30"  또는 "HOME"/"OPEN"/"CLOSE"
#   집게(G)=0~90, 나머지=0~180 (교재 기준)
from time import sleep
import ble_library
import bluetooth
from ai_ponybot import i2c, PonyMotor, PonyServo, PonyOLED

motor = PonyMotor(i2c)
servo = PonyServo(motor.pwm)
oled  = PonyOLED(i2c)

ble = bluetooth.BLE()
p = ble_library.BLESimplePeripheral(ble, 'ESP-000')   # 웹앱 namePrefix 'ESP'와 일치

CH    = {'B': 1, 'S': 2, 'E': 3, 'G': 4}              # 베이스/어깨/팔꿈치/집게
LIMIT = {'B': (0, 180), 'S': (0, 180), 'E': (0, 180), 'G': (0, 90)}
angle = {'B': 90, 'S': 90, 'E': 90, 'G': 45}

def clamp(v, lo, hi): return max(lo, min(hi, v))

def apply(j, val):
    lo, hi = LIMIT[j]
    angle[j] = clamp(int(val), lo, hi)
    servo.set_angle(CH[j], angle[j])

for j in CH:
    servo.set_angle(CH[j], angle[j])

def oled_show(a, b=""):
    for i in range(1, len(oled.buffer)): oled.buffer[i] = 0
    oled.draw_text(0, 0, a); oled.draw_text(0, 16, b); oled.show()

def on_rx(v):
    data = v.strip().upper()
    if not data: return
    try:
        if data == 'HOME':
            for j, d in (('B',90),('S',90),('E',90),('G',45)): apply(j, d)
        elif data == 'OPEN':  apply('G', LIMIT['G'][1])
        elif data == 'CLOSE': apply('G', LIMIT['G'][0])
        elif ':' in data:
            for part in data.split(','):
                if ':' not in part: continue
                j, val = part.split(':'); j = j.strip()
                if j in CH: apply(j, float(val))
        oled_show("B%-3d S%-3d" % (angle['B'], angle['S']),
                  "E%-3d G%-3d" % (angle['E'], angle['G']))
    except Exception as e:
        print("parse err:", data, e)

p.on_write(on_rx)
oled_show("BLE WAITING", "name ESP-000")
print("로봇팔 대기 중... (기기명 ESP-000)")

while True:
    if not p.is_connected():
        oled_show("BLE WAITING", "name ESP-000")
    sleep(0.3)
