# 실습 — 얼굴 추적 카메라 터렛 (MediaPipe Face Detection) 🎯

> **멀티모달 인지 기반 피지컬 AI 로봇 시스템 구현 과정**
> 카메라로 **얼굴 위치**를 인식해, 그 좌표(x·y)를 **서보 2축(수평 pan / 수직 tilt)** 각도로 바꿉니다.
> 얼굴이 움직이면 포니봇 머리가 따라 돌아 **항상 얼굴 쪽을 바라봅니다.**
> 핵심 학습: **화면 좌표(0~1) → 서보 각도(도) 매핑.**

---

## 0. 전체 그림

```
 [폰 카메라 = 눈]                              [포니봇 = 머리]
 얼굴 x,y (0~1)  ─ 좌표→각도 매핑 ─▶  P:90,T:60  ──BLE──▶  S1(수평)·S2(수직) 서보
 MediaPipe Face Detection            Web Bluetooth        얼굴을 향해 회전
```

- 폰이 얼굴을 보고, **얼굴이 화면 어디에 있는지**를 각도로 바꿔 터렛을 돌립니다.
- 명령 형식은 방향 주행과 달리 **각도 2개**: `P:<수평>,T:<수직>` (예: `P:120,T:70`), 그리고 `CENTER`(정면 복귀).

---

## 1. 하드웨어 준비

- 서보 2개로 만든 **pan/tilt(팬틸트) 브래킷**에 포니봇 서보 단자 연결
  - **S1 = 수평(pan)**, **S2 = 수직(tilt)**  ← 펌웨어 채널과 일치시키기
- 조립 시 두 서보를 **90°(정면·수평)** 상태로 맞춰 두면 추적이 자연스럽습니다.

| 파일 | 역할 |
|------|------|
| `ble_library.py` | BLE(Nordic UART) 라이브러리 — 보드 루트(`/`)에 업로드 |
| `ai_ponybot` 패키지 | `PonyServo`(서보), `PonyOLED` |
| `ai_turret_ble.py` | 터렛 수신 펌웨어(부록) |
| `face_turret.html` | 얼굴 추적 웹앱 |

---

## 2. STEP 1 — 서보 영점 맞추기 (조립 후 1회)

REPL에서 두 서보를 90°로 두고 브래킷을 정면·수평으로 정렬합니다.

```python
from ai_ponybot import i2c, PonyMotor, PonyServo
motor = PonyMotor(i2c); servo = PonyServo(motor.pwm)
servo.set_angle(1, 90)   # 수평
servo.set_angle(2, 90)   # 수직
```

---

## 3. STEP 2 — 펌웨어 실행

1. `ble_library.py`와 `ai_turret_ble.py`를 보드에 업로드
2. `ai_turret_ble.py` 실행 → OLED `BLE WAITING / name ESP-000`, 셸에 `얼굴 추적 터렛 대기 중...`

---

## 4. STEP 3 — 웹앱 연결 & 추적

1. `face_turret.html`을 **HTTPS 주소**로 엽니다(배포는 6장).
2. **① 포니봇 연결** → 목록에서 **ESP-000** 선택
3. **② 카메라 시작** → 카메라 허용
4. 얼굴을 화면에 보이면:
   - 얼굴에 **보라색 박스**와 중심점, 화면 **중앙 십자선**이 표시됩니다
   - **수평/수직 게이지**와 각도 숫자가 얼굴 위치에 따라 실시간으로 변합니다
   - 터렛이 얼굴을 따라 회전합니다
5. 머리가 **반대로** 돌면 **수평 반전 / 수직 반전** 체크박스로 방향을 맞춥니다.
6. 흐트러지면 **중앙** 버튼으로 정면(90,90) 복귀.

---

## 5. 코드 핵심 — 좌표를 각도로

### 웹앱: 얼굴 중심 → 서보 각도
```javascript
const bb = detections[0].boundingBox;     // xCenter,yCenter (0~1)
const tPan  = mapClamp(bb.xCenter, 0.15, 0.85, 10, 170, invPan);   // 좌우 → 수평
const tTilt = mapClamp(bb.yCenter, 0.15, 0.85, 40, 150, !invTilt); // 상하 → 수직
```
- `0.15~0.85`: 화면 가장자리를 잘라 흔들림을 줄입니다.
- **EMA 평활**로 서보가 부드럽게 움직입니다: `cur += (target - cur) * 0.30`
- 변화가 있고 70ms가 지났을 때만 `P:..,T:..`를 전송(BLE 혼잡 방지).

### 펌웨어: 각도 파싱 → 서보 구동
```python
for part in data.split(','):          # "P:120,T:70"
    k, val = part.split(':')
    if   k == 'P': pan  = clamp(int(float(val)), PAN_MIN,  PAN_MAX)
    elif k == 'T': tilt = clamp(int(float(val)), TILT_MIN, TILT_MAX)
servo.set_angle(PAN_CH, pan); servo.set_angle(TILT_CH, tilt)
```
- 관절별 **안전 범위로 clamp** 후 `set_angle` 호출.

---

## 6. GitHub로 배포 (HTTPS)

카메라·블루투스는 **HTTPS에서만** 동작합니다(`file://`·`content://`·`blob` ❌).

1. 공개 저장소에 `face_turret.html` 업로드
2. **Settings → Pages → Branch `main` / `/(root)` → Save**
3. 1~2분 뒤 `live at ...` 주소 확인 → 폰 Chrome:
   ```
   https://<아이디>.github.io/<저장소>/face_turret.html
   ```
   또는 즉시:
   ```
   https://cdn.jsdelivr.net/gh/<아이디>/<저장소>@main/face_turret.html
   ```

폰: **블루투스 ON · 위치 ON · Chrome(인앱 브라우저 ❌) · 카메라 허용 · 안드로이드**.

---

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 머리가 반대로 돎 | 서보 장착 방향 | **수평/수직 반전** 체크박스 |
| 서보가 덜덜 떨림 | 평활 부족·전원 | `SMOOTH` 낮추기, 서보 전원 4.8V↑ |
| 너무 크게 홱홱 움직임 | 반응이 급함 | `SMOOTH` 낮추기(예: 0.2), 가장자리 컷 넓히기 |
| 얼굴 인식 안 됨 | 조명·정면 아님 | 밝은 곳에서 얼굴 정면, 거리 조절 |
| 각도가 한쪽으로 치우침 | 서보 영점 어긋남 | STEP 1로 90° 재정렬, 범위(PAN/TILT) 조정 |
| 장치 안 보임 | 위치 OFF/다른 연결 | 위치 ON, 다른 BLE 해제, 보드 Ctrl+D |
| github.io 404 | Pages 미활성화 | Settings→Pages에서 켜고 접속 |

---

## 8. 도전과제 🎯

> **8-A. 데드존(dead-zone)** — 얼굴이 중앙 근처(예: 0.45~0.55)면 서보를 안 움직이게 해, 미세 떨림을 없애 보세요.

> **8-B. 속도 제한(slew rate)** — 한 번에 각도가 3° 이상 안 바뀌게 제한해 부드럽게 만들어 보세요.

> **8-C. 미소/눈 인식 반응** — Face Detection의 눈·코 랜드마크를 이용해, 얼굴이 가까우면(박스 크게) LED를 켜는 등 반응을 추가해 보세요.

> **8-D. 여러 얼굴 중 가장 큰 얼굴** — 여러 명이 보이면 **가장 가까운(박스가 큰) 얼굴**만 추적하도록 바꿔 보세요.

> **8-E. 폐루프 개념 실험** — 폰을 터렛 위에 올려 카메라가 함께 돌 때, 얼굴을 **화면 중앙으로 되돌리는** 방식(오차 기반 보정)으로 바꿔 보세요. (실전 카메라 터렛 원리)

---

## 부록 — `ai_turret_ble.py` (수신 펌웨어)

```python
# ai_turret_ble.py  ----  얼굴 추적 터렛 (서보 2축)
from time import sleep
import ble_library
import bluetooth
from ai_ponybot import i2c, PonyMotor, PonyServo, PonyOLED

motor = PonyMotor(i2c)
servo = PonyServo(motor.pwm)
oled  = PonyOLED(i2c)

ble = bluetooth.BLE()
p = ble_library.BLESimplePeripheral(ble, 'ESP-000')

PAN_CH,  TILT_CH  = 1, 2            # S1=수평, S2=수직
PAN_MIN, PAN_MAX  = 10, 170
TILT_MIN, TILT_MAX = 40, 150
pan, tilt = 90, 90

def clamp(v, lo, hi): return max(lo, min(hi, v))
def apply():
    servo.set_angle(PAN_CH, pan); servo.set_angle(TILT_CH, tilt)
apply()

def oled_show(a, b=""):
    for i in range(1, len(oled.buffer)): oled.buffer[i] = 0
    oled.draw_text(0, 0, a); oled.draw_text(0, 16, b); oled.show()

def on_rx(v):
    global pan, tilt
    data = v.strip().upper()
    if not data: return
    try:
        if data in ('CENTER', 'HOME'):
            pan, tilt = 90, 90
        else:
            for part in data.split(','):
                if ':' not in part: continue
                k, val = part.split(':'); k = k.strip()
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
```

> 이 실습으로 **좌표→각도 매핑**과 **평활·전송 최적화**를 익히고,
> AI 인식 결과가 실제 액추에이터(서보)를 움직이는 과정을 체험합니다.
