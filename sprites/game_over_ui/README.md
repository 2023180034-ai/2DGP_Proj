# 사망 화면 (DEAD)

`source/game_over.py`의 `GameOverUI`

## 1. 파일 구성

```
sprites/ui/
  game_over.png     제목 + 버튼 3개를 한 장에 묶음 (900x332)
source/
  game_over.py      GameOverUI
```

`game_over.png` 안 배치 (그림 위 기준 px):

| 위치 (x, y, w, h) | 내용 |
|---|---|
| (0, 0, 720, 180) | `DEAD` 제목 |
| (0, 180, 300, 72) | 다시 시작 (보통) |
| (300, 180, 300, 72) | 강화 (보통) |
| (600, 180, 300, 72) | 게임 종료 (보통) |
| (0 / 300 / 600, 252, 300, 72) | 위 세 버튼의 선택된 모습 (금색 테 + 양옆 마름모) |
| (0, 324, 8, 8) | 화면을 어둡게 덮는 검은 칸 |

pico2d `clip_draw`는 아래 기준이므로 코드에는 `SHEET_H - y - h`로 바꾼 값이 들어 있다.

## 2. 동작

| 시간 | 화면 |
|---|---|
| 0 ~ 0.8초 | 게임 화면이 점점 어두워짐 (최대 75%) |
| 0.4 ~ 1.4초 | `DEAD`가 살짝 떠오르며 나타남 |
| 1.4초 ~ | 버튼 3개(다시 시작 / 강화 / 게임 종료)가 나타나고 입력을 받음 (그 전에는 실수로 눌리지 않게 무시) |

- 위/아래 방향키로 선택, Enter로 결정
- 마우스를 올리면 선택, 클릭하면 결정
- `handle_event()`가 돌려주는 값: `'restart'`, `'upgrade'`, `'quit'`, 아무것도 안 골랐으면 `None`

조절 값은 `game_over.py` 위쪽 상수: `TITLE_Y`, `BUTTON_YS`, `DIM_ALPHA`, `DIM_TIME`, `BUTTON_START`

## 3. 코드 작성법

'강화'를 고르면 능력치 강화 창(`upgrade_window.py`)을 연다. 강화 창을 닫으면 다시 사망 화면 버튼으로 돌아온다.

```python
# ingame_mode.py
from game_over import GameOverUI
from upgrade_window import UpgradeWindow

def init():
    global game_over, upgrade
    game_over = GameOverUI()
    upgrade = UpgradeWindow()

def handle_events():
    for e in get_events():
        if upgrade.visible:                       # 강화 창이 열려 있으면 그쪽이 먼저
            if e.type == SDL_KEYDOWN and e.key == SDLK_u:
                upgrade.toggle()                  # 닫으면 사망 화면으로 돌아감
            elif upgrade.handle_event(e, levels, gold_ui):
                player.apply_stats(levels)
            continue
        if game_over.active:
            result = game_over.handle_event(e)
            if result == 'restart':
                game_over.stop()
                restart()                         # 체력 채우고 보스·플레이어 위치 초기화
            elif result == 'upgrade':
                upgrade.toggle()                  # 강화 창 열기
            elif result == 'quit':
                game_framework.quit()
            continue                              # 사망 중에는 플레이어 조작 막기
        ...

def update():
    upgrade.update()
    if game_over.active:
        game_over.update()
        return                                    # 게임 멈춤 (화면은 그대로 보임)
    ...
    if player_hp_bar.is_dead():
        game_over.start()

def draw():
    clear_canvas()
    # ... 맵, 캐릭터, UI ...
    game_over.draw()
    upgrade.draw(levels, gold_ui.gold)            # 강화 창이 사망 화면 위에
    update_canvas()
```

다시 시작할 때 체력 채우기 (강화로 최대 체력이 올랐어도 새 값으로 가득 참):

```python
def restart():
    player_hp_bar.set_max_hp(player.max_hp)
    boss_hp_bar.set_hp(boss_hp_bar.max_hp)
    # 플레이어·보스 위치, 보스 패턴 상태 초기화 ...
```

- 따로 모드로 만들고 싶으면 `game_over_mode.py`를 만들어 `game_framework.push_mode()`로 띄우고, 그 안에서 `GameOverUI`와 `UpgradeWindow`를 쓰면 된다.
- 마우스 좌표는 창 크기가 논리 해상도(1980x1080)와 같다고 보고 계산한다. 창을 줄여서 띄운다면 `handle_event()` 안에서 `e.x`, `e.y`에 비율을 곱해야 한다.
