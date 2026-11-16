# 능력치 강화 창

`source/upgrade_window.py`의 `UpgradeWindow`

캐릭터 정보 창(`status_window.py`, C 키)과 **따로 쓰는 별도 창**이다.
- 정보 창: 능력치·재화를 **보기만** 한다.
- 강화 창: 골드를 써서 능력치를 **올린다**.

> **화면 위치, 여는 키(U), 강화 비용은 아직 정하지 않은 임시 값이다.**
> 정해지면 `WINDOW_POS`, `upgrade_cost()`만 바꾸면 된다. 키를 바꾸면 창 아래 'U 키로 닫기' 문구가 그림에 들어 있으므로 그림도 다시 만들어야 한다.

---

## 1. 파일 구성

```
sprites/ui/
  upgrade_window.png   창 (760x640, 제목·머리말·능력치 이름·아이콘·화살표·안내 문구가 그려져 있음)
  upgrade_glyphs.png   숫자 글꼴 '0123456789.,' 4색 (위에서부터 흰색 / 금색 / 빨강 / 초록), 한 칸 22x32
  upgrade_cursor.png   선택한 줄 표시 (금색 테, 712x52)
  upgrade_flash.png    강화 성공 시 줄이 하얗게 번쩍임 (712x52)
  upgrade_max.png      최대 레벨일 때 '강화 후 + 비용' 칸을 덮는 MAX 표시
source/
  upgrade_window.py    UpgradeWindow, upgrade_cost()
```

**`status_window.py`가 같은 폴더에 있어야 한다.** 능력치 규칙(`STAT_RULES`, `stat_value`, `is_max`)을 거기서 가져오기 때문에 두 창의 숫자가 항상 같다.

---

## 2. 보여 주는 내용

| 칸 | 내용 | 색 |
|---|---|---|
| 레벨 | Lv.N | 흰색 |
| 현재 | 지금 능력치 값 | 흰색 |
| 강화 후 | 한 단계 올렸을 때 값 | 초록 |
| 비용 | 다음 강화에 드는 골드 | 금색, **골드가 모자라면 빨강** |
| 보유 골드 | 맨 아래 | 금색 |

- 최대 레벨(공격 속도 10, 이동 속도 20)이면 '강화 후 + 비용' 칸이 `MAX · 최대 레벨`로 바뀐다.
- 강화 성공: 그 줄이 0.25초 하얗게 번쩍인다.
- 실패(골드 부족, 최대 레벨): 그 줄의 비용이 좌우로 흔들린다.

### 강화 비용 (임시)

```python
def upgrade_cost(key, level):
    return 100 * (level + 1)      # 0->1레벨 100골드, 1->2레벨 200골드 ...
```

개발 문서에 비용이 없어 임시로 넣었다. 능력치마다 다르게 하려면 `key`로 나눠서 쓰면 된다.

---

## 3. 코드 작성법

```python
# ingame_mode.py
from status_window import StatusWindow
from upgrade_window import UpgradeWindow

def init():
    global status, upgrade
    status = StatusWindow()
    upgrade = UpgradeWindow()

def handle_events():
    for e in get_events():
        if e.type == SDL_KEYDOWN and e.key == SDLK_c:
            status.toggle()                          # C: 정보 창
        elif e.type == SDL_KEYDOWN and e.key == SDLK_u:
            upgrade.toggle()                         # U: 강화 창 (임시 키)
        elif upgrade.visible:
            stat = upgrade.handle_event(e, levels, gold_ui)   # 위/아래 선택, Enter 강화
            if stat:
                player.apply_stats(levels)           # 플레이어 실제 능력치 다시 계산
        else:
            player.handle_event(e)                   # 창이 열려 있으면 플레이어 조작은 막음

def update():
    upgrade.update()
    ...

def draw():
    clear_canvas()
    # ... 맵, 캐릭터, 체력 바, 골드 ...
    status.draw(levels, gold_ui.gold, special)
    upgrade.draw(levels, gold_ui.gold)              # 맨 마지막
    update_canvas()
```

- `levels`: 능력치별 레벨 딕셔너리 (정보 창과 같은 것). 강화에 성공하면 이 안의 값이 1 올라간다.
- `gold_ui`: `GoldDisplay`. 강화 창이 `gold_ui.spend(cost)`로 골드를 쓰므로 골드 표시도 바로 줄어든다.
- `handle_event()`는 강화에 성공하면 `'hp'` 같은 능력치 키를, 아니면 `None`을 돌려준다.

강화했을 때 플레이어 능력치 다시 계산 (예):

```python
from status_window import stat_value

def apply_stats(self, levels):
    self.max_hp = stat_value('hp', levels.get('hp', 0))
    self.atk = stat_value('atk', levels.get('atk', 0))
    ...
    player_hp_bar.set_max_hp(self.max_hp, refill=False)
```

- 두 창이 동시에 열리면 겹친다. 하나를 열 때 다른 하나를 닫거나(`status.visible = False`), 위치를 다르게 주면 된다.
- 창이 열린 동안 게임을 멈추고 싶으면 맵 선택 패널(M 키)처럼 `game_framework.push_mode()`로 별도 모드를 만들어 그 안에서 쓰면 된다.

---

## 4. 위치 (추후 지정)

```python
# upgrade_window.py
WINDOW_POS = (990, 540)   # TODO: 위치 확정 후 수정 (창 가운데)
```
