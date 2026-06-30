# joystick_drive.py  ----  조이스틱 메카넘 주행 (A=시작 / B=대기)
from machine import ADC, Pin
from time import sleep
from ai_ponybot import i2c, PonyMotor

motor = PonyMotor(i2c)

# ── 조이스틱 1 (P0=X=Pin26, P1=Y=Pin32) ──
joy_x = ADC(Pin(26)); joy_x.atten(ADC.ATTN_11DB); joy_x.width(ADC.WIDTH_10BIT)
joy_y = ADC(Pin(32)); joy_y.atten(ADC.ATTN_11DB); joy_y.width(ADC.WIDTH_10BIT)

# ── 버튼 A(시작) / B(대기) : 누르면 value()==0 ──
btn_a = Pin(36, Pin.IN)
btn_b = Pin(39, Pin.IN)

CENTER = 512        # 10비트(0~1023) 중앙값
DEAD   = 150        # 중앙 근처 무시 구간
MAXOFF = 480        # 속도 환산 기준 거리

INV_X = False       # 좌우 반전 (반대로 가면 True)
INV_Y = True        # 전후 반전 (앞뒤·대각선 앞뒤 뒤바뀜 보정)

# 키패드 코드: 7 8 9 / 4 5 6 / 1 2 3  (8=전진,2=후진,4=좌횡,6=우횡,5=정지)
NAME = {8:'FWD', 2:'BACK', 4:'LEFT', 6:'RIGHT',
        9:'F-R', 7:'F-L', 3:'B-R', 1:'B-L', 5:'STOP'}

def read_offsets():
    dx = joy_x.read() - CENTER
    dy = joy_y.read() - CENTER
    if INV_X: dx = -dx
    if INV_Y: dy = -dy
    return dx, dy

def joy_to_code(dx, dy):
    fx = 1 if dx > DEAD else (-1 if dx < -DEAD else 0)
    fy = 1 if dy > DEAD else (-1 if dy < -DEAD else 0)
    table = {(0, 0): 5,
             (0, 1): 8, (0, -1): 2, (1, 0): 6, (-1, 0): 4,
             (1, 1): 9, (-1, 1): 7, (1, -1): 3, (-1, -1): 1}
    return table[(fx, fy)]

def joy_to_speed(dx, dy):
    mag = max(abs(dx), abs(dy))
    spd = 40 + (mag - DEAD) * 60 // (MAXOFF - DEAD)
    return max(40, min(100, spd))

state = 'IDLE'      # 'IDLE'(대기) / 'RUN'(주행)
last  = None
print("대기 중... A=시작 / B=대기")

while True:
    # ── A 버튼: 주행 시작 ──
    if state == 'IDLE' and btn_a.value() == 0:
        state = 'RUN'; last = None
        print(">> RUN: 조이스틱 입력 시작")
        sleep(0.3)                       # 버튼 디바운스

    # ── B 버튼: 대기로 복귀 ──
    if state == 'RUN' and btn_b.value() == 0:
        state = 'IDLE'
        motor.mecanum(5)                 # 즉시 정지
        print(">> IDLE: 대기 상태")
        sleep(0.3)

    # ── 상태별 동작 ──
    if state == 'RUN':
        dx, dy = read_offsets()
        code = joy_to_code(dx, dy)
        if code == 5:
            motor.mecanum(5)
        else:
            motor.mecanum(code, joy_to_speed(dx, dy))
        if code != last:
            print("DIR:%-5s  X:%5d Y:%5d" % (NAME[code], dx, dy))
            last = code
    else:
        motor.mecanum(5)                 # 대기 중엔 항상 정지(조이스틱 무시)

    sleep(0.05)
