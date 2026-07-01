# ============================================================
#  ai_gripper_ble.py
#  손가락(핀치) 모양으로 집게(그리퍼)를 움직이는 AI 제어 - 포니봇(보드) 측
#
#  [동작]  웹앱(MediaPipe Hands)이 손가락 벌어진 정도를 0~90 각도로 보내면
#          BLE(Nordic UART)로 수신해 S4 서보(집게)를 그 각도로 움직입니다.
#
#  [준비]  보드에 ble_library, ai_ponybot 패키지가 올라가 있어야 합니다.
#          로봇팔이 조립되어 S4 단자에 집게 서보가 연결돼 있어야 합니다.
#  [교재]  집게(S4) 각도 범위 0~90 / servo.set_angle(채널, 각도)
# ============================================================
from time import sleep
import ble_library
import bluetooth
from ai_ponybot import i2c, PonyMotor, PonyServo, PonyOLED
from machine import Pin
from neopixel import NeoPixel

# ---- 장치 초기화 ----
motor = PonyMotor(i2c)
servo = PonyServo(motor.pwm)      # 서보는 모터와 PWM 공유
oled  = PonyOLED(i2c)

# ---- BLE 주변장치(Peripheral) ----
# ※ 이 이름('ESP-ARM')을 웹앱 연결 화면에서 똑같이 골라야 합니다.
ble = bluetooth.BLE()
p   = ble_library.BLESimplePeripheral(ble, 'ESP-KJI')

# ---- 포니봇 본체 LED(4구, Pin 4) : 상태 표시용 ----
pony = NeoPixel(Pin(4), 4)
def set_pony(r, g, b):
    for i in range(4):
        pony[i] = (r, g, b)
    pony.write()

# ---- 집게(그리퍼) 설정 ----
GRIP_CH  = 4        # S4 = 집게
GRIP_MIN = 0        # 닫힘 각도
GRIP_MAX = 90       # 열림 각도 (교재: 집게는 0~90)
angle    = 45       # 시작 각도(반쯤 열림)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

servo.set_angle(GRIP_CH, angle)   # 시작 위치로

# ---- OLED 출력 헬퍼 (교재와 동일한 방식) ----
def oled_show(line1, line2=""):
    for i in range(1, len(oled.buffer)):
        oled.buffer[i] = 0
    oled.draw_text(0, 0, line1)
    oled.draw_text(0, 16, line2)
    oled.show()

# ---- BLE 데이터 수신 콜백 ----
# 받는 형식(셋 다 허용):
#   "45"      : 각도 숫자
#   "G:45"    : 접두어 G:
#   "OPEN" / "CLOSE" : 완전 열기 / 닫기
def on_rx(v):
    global angle
    data = v.strip()
    try:
        if data == "OPEN":
            angle = GRIP_MAX
        elif data == "CLOSE":
            angle = GRIP_MIN
        else:
            if data.startswith("G:"):
                data = data[2:]
            angle = clamp(int(float(data)), GRIP_MIN, GRIP_MAX)

        servo.set_angle(GRIP_CH, angle)               # 집게 이동

        # 열린 정도를 색으로: 닫힘=빨강 → 열림=초록
        g = int(50 * (angle - GRIP_MIN) / (GRIP_MAX - GRIP_MIN))
        set_pony(50 - g, g, 0)
        oled_show("GRIPPER", "angle: %d" % angle)
        print("gripper ->", angle)
    except Exception as e:
        print("parse err:", repr(data), e)

p.on_write(on_rx)

# ---- 시작 화면 ----
oled_show("BLE: WAITING...", "name: ESP-KJI")
set_pony(50, 0, 0)
print("BLE 대기 중... 웹앱에서 'ESP-KJI' 으로 연결하세요.")

# ---- 메인 루프: 연결 상태 표시 ----
while True:
    if p.is_connected():
        oled_show("BLE: CONNECTED", "angle: %d" % angle)
    else:
        set_pony(50, 0, 0)
        oled_show("BLE: WAITING...", "name: ESP-KJI")
    sleep(0.5)
