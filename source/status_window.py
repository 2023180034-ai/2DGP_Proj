"""캐릭터 정보 창: 능력치(레벨·현재 값·강화 시 증가량), 보유 골드, 특수 재화

- 능력치 규칙은 개발 문서 '4. 능력치 업그레이드'를 그대로 옮김 (STAT_RULES)
- 글자(제목·이름·단위)는 창 그림에 들어 있고, 숫자만 코드에서 그림 -> 폰트 파일 필요 없음
- C 키로 열고 닫기 (키는 ingame_mode에서 처리)

화면 위치는 아직 정하지 않음 -> WINDOW_POS 값만 바꾸면 됨
"""
from pathlib import Path

from pico2d import load_image

IMAGE_DIR = str(Path(__file__).resolve().parent.parent / 'sprites' / 'ui') + '/'
WINDOW_POS = (990, 540)            # TODO: 위치 확정 후 수정 (창 가운데, 화면 좌표. 1980x1080 기준 화면 가운데)

# ---------------- 능력치 규칙 (개발 문서) ----------------
# 키, 기본값, 레벨업당 증가, 최대 레벨(None = 제한 없음), 표시 소수 자리
STAT_RULES = [
    ('hp', 100, 10, None, 0),
    ('atk', 10, 2, None, 0),
    ('atk_speed', 1.0, 0.3, 10, 1),         # 최대 4.0회/초
    ('stamina', 50, 5, None, 0),
    ('move_speed', 5.0, 0.5, 20, 1),        # 기본 5 -> 최대 15
    ('gold_rate', 1.0, 0.1, None, 1),
]
RULE = {r[0]: r for r in STAT_RULES}


def stat_value(key, level):
    """레벨에 따른 현재 능력치 값"""
    _, base, per, max_lv, _ = RULE[key]
    if max_lv is not None:
        level = min(level, max_lv)
    return base + per * level


def is_max(key, level):
    max_lv = RULE[key][3]
    return max_lv is not None and level >= max_lv


# ---------------- 창 그림 안 배치 (창 왼쪽 위 기준 px) ----------------
WIN_W, WIN_H = 600, 664
ROW0, ROW_H = 158, 56              # 능력치 첫 줄 가운데 y, 줄 간격
LV_X = 312                         # 레벨 숫자 왼쪽 x
VALUE_RIGHT = 440                  # 현재 값 오른쪽 끝 x
MAX_X = 488                        # MAX 표시 왼쪽 x (강화 시 칸을 덮음)
CUR_Y0, CUR_H = 522, 54            # 재화 첫 줄 가운데 y, 줄 간격
CUR_RIGHT = 570                    # 재화 숫자 오른쪽 끝 x

GLYPHS = '0123456789.,x'
GW, GH = 22, 32                    # 글자 한 칸
ADVANCE = {'.': 10, ',': 10, 'x': 17}   # 나머지(숫자)는 18
WHITE, GOLD, PURPLE = 2, 1, 0      # 글자 줄 (pico2d 아래 기준 행 번호: 위에서부터 흰색/금색/보라)


class StatusWindow:
    window = glyphs = max_badge = None

    def __init__(self, x=None, y=None):
        if StatusWindow.window is None:
            StatusWindow.window = load_image(IMAGE_DIR + 'status_window.png')
            StatusWindow.glyphs = load_image(IMAGE_DIR + 'status_glyphs.png')
            StatusWindow.max_badge = load_image(IMAGE_DIR + 'status_max.png')
        self.x = x if x is not None else WINDOW_POS[0]
        self.y = y if y is not None else WINDOW_POS[1]
        self.visible = False

    def toggle(self):
        self.visible = not self.visible

    # ---------- 숫자 그리기 ----------
    def _width(self, text):
        return sum(ADVANCE.get(ch, 18) for ch in text)

    def _text(self, text, left, center_y, row):
        """left, center_y: 화면 좌표"""
        x = left
        for ch in text:
            i = GLYPHS.index(ch)
            adv = ADVANCE.get(ch, 18)
            self.glyphs.clip_draw(i * GW, row * GH, GW, GH, x + adv / 2, center_y)
            x += adv

    def _at(self, wx, wy):
        """창 그림 좌표(왼쪽 위 기준) -> 화면 좌표"""
        left = self.x - WIN_W // 2
        top = self.y + WIN_H // 2
        return left + wx, top - wy

    # ---------- 그리기 ----------
    def draw(self, levels, gold, special):
        """levels: {'hp': 3, 'atk': 5, ...} 강화 레벨 / gold: 보유 골드 / special: 특수 재화"""
        if not self.visible:
            return
        self.window.draw(self.x, self.y)

        for i, (key, _, _, _, digits) in enumerate(STAT_RULES):
            lv = levels.get(key, 0)
            cy = ROW0 + i * ROW_H
            lx, ly = self._at(LV_X, cy)
            self._text(str(lv), lx, ly, WHITE)

            val = stat_value(key, lv)
            text = f'{val:.{digits}f}' if digits else f'{int(val):,}'
            rx, ry = self._at(VALUE_RIGHT, cy)
            self._text(text, rx - self._width(text), ry, WHITE)

            if is_max(key, lv):
                mx, my = self._at(MAX_X, cy)
                self.max_badge.draw_to_origin(mx, my - 18)

        for j, (amount, row) in enumerate(((gold, GOLD), (special, PURPLE))):
            text = f'{int(amount):,}'
            rx, ry = self._at(CUR_RIGHT, CUR_Y0 + j * CUR_H)
            self._text(text, rx - self._width(text), ry, row)
