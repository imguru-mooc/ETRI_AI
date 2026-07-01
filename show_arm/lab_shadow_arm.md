# 실습 — 팔의 그림자 로봇 (MediaPipe Holistic) 🦾

> **멀티모달 인지 기반 피지컬 AI 로봇 시스템 구현 과정**
> 카메라로 **내 어깨·팔꿈치 각도**를 계산해 로봇팔 서보에 그대로 복사하고,
> **엄지·검지 손끝 거리(핀치)** 로 집게를 여닫습니다. "내 팔을 따라 하는 로봇".
> 핵심 학습: **관절 좌표 → 각도 계산 → 서보 매핑** (★★★)

---

## 0. 전체 그림

```
 [폰 카메라]  MediaPipe Holistic (포즈 + 양손)
   어깨·팔꿈치·손목 좌표 ─▶ 각도 계산 ─┐
   엄지·검지 손끝 거리   ─▶ 핀치       ├─▶ B:..,S:..,E:..,G:.. ─BLE─▶ 로봇팔 4서보
                                       ┘   Web Bluetooth
```

- **Holistic** 하나로 상체 포즈 33점 + 손 21점을 함께 얻어, 팔 각도와 손가락 핀치를 동시에 처리합니다.
- 명령 형식은 로봇팔 실습과 동일: `B:<베이스>,S:<어깨>,E:<팔꿈치>,G:<집게>` → **같은 펌웨어 `ai_arm_ble.py`** 사용.

### 손 동작 ↔ 로봇팔 관절

| 내 동작 | 계산 | 로봇 관절 |
|---------|------|-----------|
| 팔을 좌우로 스윙 | 위팔의 수평 성분(E.x − S.x) | **B 베이스(회전)** |
| 팔을 들어올림 | 위팔이 '아래'와 이루는 각(0~180) | **S 어깨(상하)** |
| 팔꿈치 굽힘 | 어깨-팔꿈치-손목 **내각** | **E 팔꿈치** |
| 엄지·검지 손끝 | 두 손끝 거리 ÷ 손 크기 | **G 집게(0~90)** |

---

## 1. 준비물 & 파일

- 조립된 **로봇팔**(서보 S1~S4), 서보 영점 90°
- 보드에 `ble_library.py` + `ai_ponybot`

| 파일 | 역할 |
|------|------|
| `ble_library.py` | BLE(Nordic UART) 라이브러리 |
| `ai_arm_ble.py` | 로봇팔 4서보 수신 펌웨어(부록) |
| `shadow_arm.html` | 포즈+손 인식 웹앱 |

> 채널: **B=S1, S=S2, E=S3, G=S4**. 실제 연결과 다르면 `ai_arm_ble.py`의 `CH`만 수정.

---

## 2. STEP 1 — 서보 영점 & 펌웨어

1. REPL에서 4서보를 90°로 정렬(집게는 반쯤):
   ```python
   from ai_ponybot import i2c, PonyMotor, PonyServo
   motor=PonyMotor(i2c); servo=PonyServo(motor.pwm)
   for ch in (1,2,3): servo.set_angle(ch,90)
   servo.set_angle(4,45)
   ```
2. `ble_library.py` + `ai_arm_ble.py` 업로드 → `ai_arm_ble.py` 실행 → OLED `BLE WAITING`.

---

## 3. STEP 2 — 웹앱 연결 & 캘리브레이션

1. `shadow_arm.html`을 **HTTPS 주소**로 엽니다(배포는 6장).
2. **① 포니봇 연결** → `ESP-000` 선택. **추적 팔**(오른팔/왼팔) 선택.
3. **② 카메라 시작** → 카메라 허용. **상반신 전체**가 화면에 보이게 섭니다.
4. 팔을 천천히 움직이며 **게이지 4개(B·S·E·G)** 가 반응하는지 확인.
5. 관절이 **반대로** 움직이면 해당 **반전 체크박스**(B·S·E·G)를 켭니다.
6. 자세가 흐트러지면 **HOME** 으로 기본 자세 복귀.

> 팔을 들면 어깨(S), 팔꿈치를 굽히면 팔꿈치(E), 팔을 옆으로 벌리면 베이스(B), 엄지·검지를 붙였다 떼면 집게(G)가 움직입니다.

---

## 4. 코드 핵심 — 좌표에서 각도 뽑기

### 팔꿈치 내각 (세 점으로 각도)
```javascript
function angleAt(a, b, c){            // b(팔꿈치)에서의 내각
  const v1x=a.x-b.x, v1y=a.y-b.y;     // 팔꿈치→어깨
  const v2x=c.x-b.x, v2y=c.y-b.y;     // 팔꿈치→손목
  const d=v1x*v2x+v1y*v2y;
  const m=Math.hypot(v1x,v1y)*Math.hypot(v2x,v2y);
  return Math.acos(d/m) * 180/Math.PI;   // 편팔≈175, 굽힘≈40
}
```

### 어깨 들기 (벡터와 '아래'의 각)
```javascript
function raiseFromDown(a, b){         // 위팔(어깨→팔꿈치)이 아래와 이루는 각
  const vy=b.y-a.y, m=Math.hypot(b.x-a.x, vy);
  return Math.acos(vy/m) * 180/Math.PI;  // 0=아래, 90=수평, 180=위
}
```

### 각도 → 서보 (매핑 + 평활)
```javascript
// 예: 팔꿈치 내각 40~175도 → 서보 범위로
ema('E', mapClamp(angleAt(S,E,W), 40,175, R.E, invE));
cur.E += (target - cur.E) * 0.30;    // EMA 평활
```

### 집게 (엄지-검지 손끝)
```javascript
const ratio = dist(hand[4], hand[8]) / dist(hand[0], hand[9]);  // 손 크기로 정규화
ema('G', mapClamp(ratio, 0.15,0.95, R.G, invG));                // 0~90
```

### 전송 & 펌웨어
```javascript
// "B:100,S:70,E:120,G:30"  (변화 있고 80ms 지났을 때만)
```
```python
# ai_arm_ble.py 내부
for part in data.split(','):
    j, val = part.split(':')
    if j in CH: apply(j, float(val))   # 관절별 clamp 후 servo.set_angle
```

---

## 5. 좋은 인식을 위한 팁

- **상반신 전체**가 보이도록 카메라에서 1~2m 거리. 팔이 프레임 밖으로 나가지 않게.
- 밝은 곳, 배경과 대비되는 옷. **추적 팔**과 같은 쪽 **손**이 보여야 집게가 동작.
- 폰이 느리면 웹앱의 `modelComplexity`를 `0`으로 낮추세요(정확도↓ 속도↑).
- 처음엔 **천천히** 움직여 서보 부하를 줄이고, 서보 전원(4.8V↑)을 확인.

---

## 6. GitHub 배포 (HTTPS)

카메라·블루투스는 **HTTPS에서만** 동작(`file://`·`content://`·`blob` ❌).

1. 공개 저장소에 `shadow_arm.html` 업로드
2. **Settings → Pages → Branch `main` / `/(root)` → Save**
3. `live at ...` 확인 후 폰/PC Chrome:
   ```
   https://<아이디>.github.io/<저장소>/shadow_arm.html
   또는  https://cdn.jsdelivr.net/gh/<아이디>/<저장소>@main/shadow_arm.html
   ```
> **Chrome/Edge**(안드로이드·PC)에서 카메라+블루투스 모두 동작. iPhone은 미지원.

---

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 관절이 반대로 움직임 | 서보 방향 | 해당 **반전 체크박스** |
| 팔은 되는데 집게 안 됨 | 손 미검출 | 추적 팔과 같은 손을 화면에 보이기 |
| 서보 떨림/과열 | 평활·전원 | `SMOOTH`↓, 서보 전원 4.8V↑ |
| 각도가 끝으로 튐 | 팔이 프레임 밖/영점 어긋남 | 상반신 다 보이게, R.* 범위 조정 |
| 반응이 느림/끊김 | 폰 성능 | `modelComplexity:0` |
| 장치 안 보임 | 위치 OFF/다른 연결 | 위치 ON, 다른 BLE 해제, 보드 Ctrl+D |
| 앞뒤/좌우 이상 | 추적 팔 설정 | 오른팔/왼팔 드롭다운 변경 |

---

## 8. 도전과제 🎯

> **8-A. 손목 회전 추가** — 손 랜드마크로 손목 방향을 계산해 5번째 서보(손목)까지 복사.

> **8-B. 데드존·속도 제한** — 각 관절에 중앙 데드존과 프레임당 최대 변화(예: 3°)를 넣어 부드럽게.

> **8-C. 양팔 → 두 로봇팔** — 왼팔·오른팔을 각각 두 로봇팔에 매핑.

> **8-D. 동작 녹화·재생** — 팔 동작을 배열에 저장했다가 버튼 한 번으로 재생(Teach & Repeat).

> **8-E. 안전 필터** — 관절 각도 조합이 위험(자기 충돌)하면 자동으로 막는 규칙 추가.

---

## 부록 — `ai_arm_ble.py` (로봇팔 4서보 수신)

```python
# ai_arm_ble.py
from time import sleep
import ble_library
import bluetooth
from ai_ponybot import i2c, PonyMotor, PonyServo, PonyOLED

motor = PonyMotor(i2c)
servo = PonyServo(motor.pwm)
oled  = PonyOLED(i2c)

ble = bluetooth.BLE()
p = ble_library.BLESimplePeripheral(ble, 'ESP-000')

CH    = {'B':1, 'S':2, 'E':3, 'G':4}                  # 베이스/어깨/팔꿈치/집게
LIMIT = {'B':(0,180), 'S':(0,180), 'E':(0,180), 'G':(0,90)}
angle = {'B':90, 'S':90, 'E':90, 'G':45}

def clamp(v,lo,hi): return max(lo,min(hi,v))
def apply(j,val):
    lo,hi = LIMIT[j]; angle[j] = clamp(int(val),lo,hi); servo.set_angle(CH[j], angle[j])
for j in CH: servo.set_angle(CH[j], angle[j])

def oled_show(a,b=""):
    for i in range(1,len(oled.buffer)): oled.buffer[i]=0
    oled.draw_text(0,0,a); oled.draw_text(0,16,b); oled.show()

def on_rx(v):
    data = v.strip().upper()
    if not data: return
    try:
        if data=='HOME':
            for j,d in (('B',90),('S',90),('E',90),('G',45)): apply(j,d)
        elif data=='OPEN':  apply('G',LIMIT['G'][1])
        elif data=='CLOSE': apply('G',LIMIT['G'][0])
        elif ':' in data:
            for part in data.split(','):
                if ':' not in part: continue
                j,val = part.split(':'); j=j.strip()
                if j in CH: apply(j,float(val))
        oled_show("B%-3d S%-3d"%(angle['B'],angle['S']), "E%-3d G%-3d"%(angle['E'],angle['G']))
    except Exception as e:
        print("parse err:", data, e)

p.on_write(on_rx)
oled_show("BLE WAITING","name ESP-000")
print("로봇팔 대기 중... (기기명 ESP-000)")
while True:
    if not p.is_connected():
        oled_show("BLE WAITING","name ESP-000")
    sleep(0.3)
```

> 이 실습으로 **관절 좌표 → 각도 → 서보** 라는 역기구학의 직관을 몸으로 익히고,
> AI 포즈·손 인식이 실제 다축 로봇을 실시간으로 움직이는 전 과정을 경험합니다.
