# 게임 UI (보스 체력 · 플레이어 체력 · 골드)

- `source/hp_bar.py` : 보스 체력 바(`BossHpBar`), 플레이어 체력 바(`PlayerHpBar`)
- `source/gold_display.py` : 골드 표시(`GoldDisplay`)

> **화면 위치는 아직 정하지 않았다. 위치는 따로 알려 줄 예정이며,**
> **정해지면 `hp_bar.py`의 `BOSS_POS`, `PLAYER_POS`, `gold_display.py`의 `GOLD_POS` 값만 바꾼다.**
> (지금 들어 있는 값은 임시 값)

---

## 1. 파일 구성

```
sprites/ui/
  boss_hp_frame.png     보스 바 틀 (원본 260x12 -> 화면 780x36)
  boss_hp_bg.png        바 안쪽 배경
  boss_hp_fill.png      빨간 체력
  boss_hp_chip.png      노란 '깎인 체력'
  boss_hp_flash.png     맞았을 때 번쩍이는 흰 바
  player_hp_frame.png   플레이어 바 틀 (원본 130x12 -> 화면 390x36, 왼쪽 붉은 보석 장식)
  player_hp_bg / fill / chip / flash.png
  gold_panel.png        골드 패널 (원본 78x16 -> 화면 234x48)
  gold_coin.png         동전 회전 6프레임 (한 칸 12x12)
  gold_coin_icon.png    동전 한 장 (정지 그림, 상점 등에 쓰기)
  gold_digits.png       숫자 도트 글꼴 '0123456789,+-' (한 칸 7x9)
source/
  hp_bar.py             BossHpBar, PlayerHpBar
  gold_display.py       GoldDisplay
```

모든 그림은 도트 원본이며, 코드에서 `SCALE = 3`배로 키워 그린다.

---

## 2. 동작

| 상황 | 화면 |
|---|---|
| 맞음 (`damage`) | 빨간 체력이 즉시 줄어듦 + 바가 하얗게 번쩍(0.08초) + 살짝 흔들림(0.15초) |
| 맞은 직후 | 줄어든 만큼 노란 바가 0.6초 남아 있음 (연타 중에는 계속 버팀) |
| 0.6초 뒤 | 노란 바가 빨간 체력까지 천천히 줄어듦 (초당 최대 체력의 35%) |
| 회복 (`heal`) | 빨간 체력이 즉시 늘어남 |

조절 값은 `hp_bar.py` 맨 위 상수: `CHIP_DELAY`, `CHIP_SPEED`, `FLASH_TIME`, `SHAKE_TIME`

---

## 3. 코드 작성법

### 3-1. 준비

```python
# ingame_mode.py
from hp_bar import BossHpBar, PlayerHpBar
```

- `IMAGE_DIR` : 실행 위치 기준 이미지 경로. 프로젝트 실행 위치에 맞게 수정.
- `FONT_PATH` : 이름·숫자를 띄우려면 한글 TTF 경로를 넣는다. `None`이면 바만 그린다.
- `game_framework.frame_time`을 사용하므로 수업 프레임워크의 `game_framework`가 필요하다.

### 3-2. 보스 체력 바

```python
def init():
    global boss_hp_bar
    boss_hp_bar = BossHpBar(max_hp=10000, name='보스 이름')   # 보스 1: 10K / 보스 2: 50K / 보스 3: 100K

def update():
    boss_hp_bar.update()

def draw():
    clear_canvas()
    # ... 맵, 플레이어, 보스 ...
    boss_hp_bar.draw()          # UI는 맨 마지막 (카메라 영향 없음)
    update_canvas()
```

보스가 맞았을 때 (충돌 처리 쪽):

```python
damage = player.atk
boss_hp_bar.damage(damage)
progress.gold += damage * player.gold_rate      # 개발 문서: 획득 골드 = 피해 x 배율
if boss_hp_bar.is_dead():
    # 보스 격파 처리
    ...
```

- 체력 값을 보스 객체가 따로 갖고 있다면, 보스 체력이 바뀔 때마다 같은 양을 `damage()`로 넘겨 주면 된다.
- 숫자는 K 단위로 표시된다 (예: `6.8K / 10K`).

### 3-3. 플레이어 체력 바

```python
def init():
    global player_hp_bar
    player_hp_bar = PlayerHpBar(max_hp=player.max_hp)       # 기본 100

def update():
    player_hp_bar.update()

def draw():
    ...
    player_hp_bar.draw()
```

플레이어가 맞았을 때 / 회복할 때:

```python
if not player.invincible:              # 구르기 무적, 패링 성공이면 넘김
    player_hp_bar.damage(boss_attack_damage)
    if player_hp_bar.is_dead():
        # 사망 처리 -> 결과 화면
        ...

player_hp_bar.heal(30)                 # 회복 아이템
```

강화로 최대 체력이 오를 때 (개발 문서: 레벨업당 +10):

```python
player_hp_bar.set_max_hp(player.max_hp)               # 가득 채움
player_hp_bar.set_max_hp(player.max_hp, refill=False) # 현재 체력은 유지
```

다시 도전할 때 체력 가득 채우기:

```python
player_hp_bar.set_hp(player_hp_bar.max_hp)
boss_hp_bar.set_hp(boss_hp_bar.max_hp)
```

### 3-4. 함수 정리

| 함수 | 보스 | 플레이어 | 설명 |
|---|:---:|:---:|---|
| `damage(amount)` | O | O | 체력 감소 + 번쩍임 + 흔들림 |
| `heal(amount)` | O | O | 체력 회복 |
| `set_hp(hp)` | O | O | 체력을 바로 맞춤 (애니메이션 없음) |
| `is_dead()` | O | O | 체력이 0인지 |
| `set_max_hp(max_hp, refill=True)` |  | O | 최대 체력 변경 |
| `update()` | O | O | 매 프레임 호출 |
| `draw()` | O | O | 매 프레임 호출 (맨 마지막) |

---

## 4. 위치 (추후 지정)

```python
# hp_bar.py
BOSS_POS = (640, 60)      # TODO: 위치 확정 후 수정
PLAYER_POS = (230, 680)   # TODO: 위치 확정 후 수정
```

- 값은 체력 바 **가운데**의 화면 좌표 (pico2d 기준, 아래가 0).
- 객체를 만들 때 `BossHpBar(10000, '이름', x=..., y=...)`처럼 직접 넘길 수도 있다.

---

## 5. 골드 표시 (`gold_display.py`)

### 동작

| 상황 | 화면 |
|---|---|
| 골드 획득 (`add`) | 숫자가 0.5초 동안 새 값까지 빠르게 올라감 + 동전이 한 바퀴 돎 + 패널 아래 `+N`이 떠올랐다 사라짐 |
| 연타로 계속 획득 | 0.25초 안에 들어온 획득은 `+N` 하나로 합쳐짐 |
| 강화에 사용 (`spend`) | 숫자가 바로 줄어듦. 골드가 모자라면 `False` |

숫자는 도트 글꼴 이미지로 그리기 때문에 폰트 파일이 필요 없다. 천 단위마다 쉼표가 들어간다 (예: `12,345`).

### 코드 작성법

```python
from gold_display import GoldDisplay

def init():
    global gold_ui
    gold_ui = GoldDisplay(gold=progress.gold)        # 저장된 골드로 시작

def update():
    gold_ui.update()

def draw():
    ...
    gold_ui.draw()                                   # UI는 맨 마지막
```

보스를 때렸을 때 (개발 문서: 획득 골드 = 피해 x 획득 골드 배율):

```python
damage = player.atk
boss_hp_bar.damage(damage)
gold_ui.add(damage * player.gold_rate)              # 소수는 버림
```

강화 화면에서 사용:

```python
if gold_ui.spend(cost):
    player.level_up(stat)
else:
    # 골드 부족 안내
    ...
```

| 함수 | 설명 |
|---|---|
| `add(amount)` | 골드 획득 (애니메이션) |
| `spend(amount)` | 골드 사용, 모자라면 `False` |
| `set(gold)` | 값 바로 맞춤 (애니메이션 없음) |
| `gold` | 실제 보유 골드 (저장할 때 이 값을 사용) |
| `update()`, `draw()` | 매 프레임 호출 |

### 위치 (추후 지정)

```python
# gold_display.py
GOLD_POS = (1100, 680)    # TODO: 위치 확정 후 수정 (패널 가운데)
```
