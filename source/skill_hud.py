"""왼쪽 아래(플레이어 체력 바 바로 위) 스킬 표시: 스킬 아이콘 + 쿨타임 + 사용 키(X)

- 아이콘·쿨타임 그림은 팀원 코드 skill_icon.py(SkillIcon)를 그대로 사용
- 쿨타임 값은 Player가 가지고 있고, 여기서는 그 값을 읽어 표시만 한다 (체력 바와 같은 방식)
- 아이콘 오른쪽 아래 모서리에 키 이름(X)을 작은 키캡 모양으로 그린다
"""
import os

import pico2d

from skill_icon import N as ICON_SIZE, SCALE as ICON_SCALE, SkillIcon

# 플레이어 체력 바(가운데 (215, 38), 화면 390x36) 왼쪽 끝에 맞추고 그 위에 올림
HP_BAR_LEFT = 215 - 130 * 3 // 2
HP_BAR_TOP = 38 + 12 * 3 // 2
ICON_GAP = 14
ICON_HALF = ICON_SIZE * ICON_SCALE // 2
SKILL_ICON_POS = (HP_BAR_LEFT + ICON_HALF, HP_BAR_TOP + ICON_GAP + ICON_HALF)

KEY_SIZE = 34                        # 키캡 한 변 (화면 px)
KEY_OVERHANG = 6                     # 아이콘 모서리 밖으로 튀어나오는 정도
KEY_FONT_SIZE = 22
KEY_FONT_PATHS = (
    r"C:\Windows\Fonts\malgunbd.ttf",
    r"C:\Windows\Fonts\malgun.ttf",
)
KEY_FILL = (28, 26, 34)
KEY_BORDER = (214, 196, 150)
KEY_TEXT = (240, 232, 214)


def _load_key_font():
    for path in KEY_FONT_PATHS:
        if os.path.exists(path):
            return pico2d.load_font(path, KEY_FONT_SIZE)
    return None


class SkillHud:
    def __init__(self, skill_name="slash", cooldown=8.0, key_label="X"):
        self.icon = SkillIcon(
            skill_name,
            cooldown=cooldown,
            x=SKILL_ICON_POS[0],
            y=SKILL_ICON_POS[1],
        )
        self.key_label = key_label
        self.font = _load_key_font()

    def reset(self):
        """다시 시작할 때: 번쩍임 없이 쿨타임 표시를 비운다."""
        self.icon.reset()
        self.icon.flash_t = 0.0

    def deny(self):
        """쿨타임 중에 스킬 키를 눌렀을 때 아이콘을 흔든다."""
        self.icon.deny_t = 0.2

    def update(self, cooldown_remaining):
        self.icon.update(cooldown_remaining)

    def draw(self):
        self.icon.draw()
        self._draw_key()

    def _draw_key(self):
        right = SKILL_ICON_POS[0] + ICON_HALF + KEY_OVERHANG
        bottom = SKILL_ICON_POS[1] - ICON_HALF - KEY_OVERHANG
        left = right - KEY_SIZE
        top = bottom + KEY_SIZE
        pico2d.draw_rectangle(left, bottom, right, top, *KEY_FILL, 255, True)
        pico2d.draw_rectangle(left, bottom, right, top, *KEY_BORDER, 255, False)
        pico2d.draw_rectangle(
            left + 1, bottom + 1, right - 1, top - 1, *KEY_BORDER, 255, False
        )
        if self.font:
            # 글자 폭을 대략 맞춰 가운데 정렬 (영문 대문자 한 글자 기준)
            text_x = (left + right) / 2 - KEY_FONT_SIZE * 0.32 * len(self.key_label)
            self.font.draw(text_x, (bottom + top) / 2, self.key_label, KEY_TEXT)
