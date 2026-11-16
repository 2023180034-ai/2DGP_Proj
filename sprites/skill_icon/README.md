# 스킬 아이콘 + 쿨타임 (연속 베기)

`source/skill_icon.py`의 `SkillIcon`

> **화면 위치와 쿨타임 시간은 아직 정하지 않았다.** 정해지면 `ICON_POS`와 `SkillIcon(..., cooldown=...)` 값만 바꾼다.
> 지금 쿨타임은 임시로 8초.

## 1. 파일 구성

```
sprites/ui/
  skill_slash_icon.png      연속 베기 아이콘 (32x32 도트, 네모 틀 포함 -> 화면 96x96)
  skill_slash_icon_cd.png   쿨타임 중 회백색 아이콘
  skill_cd_edge.png         회백색 부분 위쪽 경계의 흰 줄 (공용)
  skill_ready_flash.png     쿨타임이 끝날 때 번쩍임 (공용)
source/
  skill_icon.py             SkillIcon
```

## 2. 동작

| 상황 | 화면 |
|---|---|
| 스킬 사용 (`use()`) | 아이콘 전체가 회백색으로 바뀜 |
| 쿨타임 중 | 회백색 부분의 위쪽 경계(흰 줄)가 위에서 아래로 내려가며 원래 색이 드러남 |
| 쿨타임 끝 | 원래 색으로 돌아오고, 테두리가 번쩍이며 아이콘이 살짝 커졌다 돌아옴 |
| 쿨타임 중 다시 누름 | 아이콘이 좌우로 살짝 흔들림, `use()`가 `False` |

도트 그림이라 경계는 원본 1px(화면 3px)씩 끊어서 내려간다.

## 3. 코드 작성법

```python
# ingame_mode.py
from skill_icon import SkillIcon

def init():
    global skill_icon
    skill_icon = SkillIcon('slash', cooldown=8.0)     # TODO: 쿨타임 확정 후 수정

def handle_events():
    for e in get_events():
        if e.type == SDL_KEYDOWN and e.key == SDLK_x:
            if skill_icon.use():                      # 쿨타임이면 False
                player.start_skill()                  # 연속 베기 시작
        ...

def update():
    skill_icon.update()
    ...

def draw():
    clear_canvas()
    # ... 맵, 캐릭터, 체력 바 ...
    skill_icon.draw()                                 # UI는 마지막 쪽
    update_canvas()
```

| 함수·값 | 설명 |
|---|---|
| `use()` | 쓸 수 있으면 쿨타임 시작 후 `True`, 쿨타임 중이면 흔들고 `False` |
| `ready` | 지금 쓸 수 있는지 |
| `remain` | 남은 쿨타임 (초) |
| `reset()` | 쿨타임 없애기 (다시 시작할 때 등) |
| `update()`, `draw()` | 매 프레임 호출 |

### 다른 스킬 추가

판마다 스킬을 갈아 끼울 수 있게 그림 이름만 받는다. `skill_<이름>_icon.png`, `skill_<이름>_icon_cd.png` 두 장을 만들면 된다.

```python
skill_icon = SkillIcon('fire', cooldown=12.0)         # skill_fire_icon.png 사용
```

## 4. 위치 (추후 지정)

```python
# skill_icon.py
ICON_POS = (1700, 120)    # TODO: 위치 확정 후 수정 (아이콘 가운데)
```
