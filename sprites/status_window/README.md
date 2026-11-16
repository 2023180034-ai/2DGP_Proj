# 캐릭터 정보 창 (능력치 · 보유 골드 · 특수 재화)

`source/status_window.py`의 `StatusWindow`

> **화면 위치는 아직 정하지 않았다. 위치는 따로 알려 줄 예정이며,**
> **정해지면 `status_window.py`의 `WINDOW_POS` 값만 바꾼다.** (지금 값은 1980×1080 화면 가운데, 임시)

---

## 1. 파일 구성

```
sprites/ui/
  status_window.png    창 (600x664, 제목·능력치 이름·단위·강화 시 증가량·아이콘이 그려져 있음)
  status_glyphs.png    숫자 글꼴 '0123456789.,x' 3색 (위에서부터 흰색 / 금색 / 보라), 한 칸 22x32
  status_max.png       최대 레벨일 때 '강화 시' 칸을 덮는 MAX 표시
  icon_*.png           능력치·재화 아이콘 (36x36, 다른 화면에서 재사용용)
source/
  status_window.py     StatusWindow, stat_value(), is_max(), STAT_RULES
```

창 그림은 화면 크기 그대로(1배) 그린다. 숫자만 코드에서 그리므로 폰트 파일이 필요 없다.

---

## 2. 보여 주는 내용

| 줄 | 레벨 | 현재 값 | 강화 시 |
|---|---|---|---|
| 체력 | Lv.N | 100 + 10×N | +10 |
| 공격력 | Lv.N | 10 + 2×N | +2 |
| 공격 속도 | Lv.N | 1.0 + 0.3×N 회/초 (최대 10레벨 = 4.0) | +0.3 / MAX |
| 스태미나 | Lv.N | 50 + 5×N | +5 |
| 이동 속도 | Lv.N | 5.0 + 0.5×N (최대 20레벨 = 15.0) | +0.5 / MAX |
| 획득 골드 | Lv.N | 1.0 + 0.1×N 배 | +0.1 |
| 보유 골드 | | 금색 숫자 (쉼표) | |
| 특수 재화 | | 보라 숫자 (보스 처치 시 획득) | |

규칙은 `STAT_RULES` 한 곳에만 있다. 개발 문서 수치가 바뀌면 여기만 고친다.
플레이어 능력치 계산에도 같은 함수를 쓰면 창과 실제 값이 항상 일치한다.

```python
from status_window import stat_value
player.max_hp = stat_value('hp', levels['hp'])
player.atk = stat_value('atk', levels['atk'])
```

---

## 3. 코드 작성법

```python
# ingame_mode.py
from pico2d import *
from status_window import StatusWindow

def init():
    global status
    status = StatusWindow()

def handle_events():
    for e in get_events():
        if e.type == SDL_KEYDOWN and e.key == SDLK_c:
            status.toggle()                      # C 키로 열기/닫기
        ...

def draw():
    clear_canvas()
    # ... 맵, 캐릭터, 체력 바, 골드 ...
    status.draw(levels, gold_ui.gold, special)   # 맨 마지막 (다른 UI 위에)
    update_canvas()
```

`draw()`에 넘기는 값:

| 인자 | 내용 | 예 |
|---|---|---|
| `levels` | 능력치별 강화 레벨 딕셔너리 | `{'hp': 3, 'atk': 5, 'atk_speed': 10, 'stamina': 1, 'move_speed': 4, 'gold_rate': 2}` |
| `gold` | 보유 골드 | `gold_ui.gold` (GoldDisplay를 쓰는 경우) |
| `special` | 특수 재화 개수 | `progress.special` |

빠진 키는 0레벨로 본다. 창이 닫혀 있으면 `draw()`는 아무것도 그리지 않는다.

보스를 처치했을 때 특수 재화 추가 (획득량은 미정):

```python
if boss_hp_bar.is_dead():
    progress.special += 1        # TODO: 보스별 획득량 확정 후 수정
```

- 창이 열린 동안 게임을 멈추고 싶으면, 맵 선택 패널(M 키)처럼 `game_framework.push_mode()`로 별도 모드를 만들어 그 안에서 `draw()`하면 된다.
- 열기 키(C)는 아직 개발 문서에 없는 임시 키다. 창 아래 'C 키로 닫기' 문구도 창 그림에 들어 있으므로, 키를 바꾸면 그림도 다시 만들어야 한다.

---

## 4. 위치 (추후 지정)

```python
# status_window.py
WINDOW_POS = (990, 540)   # TODO: 위치 확정 후 수정 (창 가운데)
```
