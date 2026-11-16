"""능력치 강화 창: 골드를 써서 능력치 레벨을 올린다

- 캐릭터 정보 창(status_window.py, C 키)과 따로 쓰는 별도 창 (U 키, 임시)
- 능력치 규칙(STAT_RULES, stat_value, is_max)은 status_window.py 것을 그대로 가져와 씀
  -> 두 창의 숫자가 항상 같음
- 글자(제목·이름·머리말)는 창 그림에 들어 있고, 숫자만 코드에서 그림 -> 폰트 파일 필요 없음

조작: 위/아래 방향키로 능력치 선택, Enter로 강화
화면 위치는 아직 정하지 않음 -> WINDOW_POS 값만 바꾸면 됨
"""
from pico2d import load_image, SDL_KEYDOWN, SDLK_UP, SDLK_DOWN, SDLK_RETURN

import game_framework
from status_window import STAT_RULES, stat_value, is_max

IMAGE_DIR = 'sprites/ui/'          # 실행 위치 기준 경로 - 프로젝트에 맞게 수정
WINDOW_POS = (990, 540)            # TODO: 위치 확정 후 수정 (창 가운데, 화면 좌표)


# ---------------- 강화 비용 (임시) ----------------
def upgrade_cost(key, level):
    """level -> level+1 로 올리는 데 드는 골드.
    TODO: 개발 문서에 비용이 정해지면 수정. 지금은 모든 능력치가 100 x (현재 레벨 + 1)"""
    return 100 * (level + 1)


# ---------------- 창 그림 안 배치 (창 왼쪽 위 기준 px) ----------------
WIN_W, WIN_H = 760, 640
ROW0, ROW_H = 168, 58              # 첫 줄 가운데 y, 줄 간격
ROW_LEFT = 24                      # 선택 표시(712x52) 왼쪽 x
LV_X = 284                         # 레벨 숫자 왼쪽 x
CUR_RIGHT = 430                    # 현재 값 오른쪽 끝 x
NEXT_RIGHT = 566                   # 강화 후 값 오른쪽 끝 x
MAX_X = 494                        # MAX 표시 왼쪽 x (강화 후 + 비용 칸을 덮음)
COST_RIGHT = 728                   # 비용 오른쪽 끝 x
GOLD_Y = 556                       # 보유 골드 줄 가운데 y

GLYPHS = '0123456789.,'
GW, GH = 22, 32
ADVANCE = {'.': 10, ',': 10}       # 나머지(숫자)는 18
WHITE, GOLD, RED, GREEN = 3, 2, 1, 0   # 글자 줄 (pico2d 아래 기준 행 번호)

FLASH_TIME = 0.25                  # 강화 성공 시 줄이 번쩍이는 시간
FAIL_TIME = 0.35                   # 골드 부족/최대 레벨일 때 흔들리는 시간


class UpgradeWindow:
    window = glyphs = cursor = flash = max_badge = None

    def __init__(self, x=None, y=None):
        if UpgradeWindow.window is None:
            UpgradeWindow.window = load_image(IMAGE_DIR + 'upgrade_window.png')
            UpgradeWindow.glyphs = load_image(IMAGE_DIR + 'upgrade_glyphs.png')
            UpgradeWindow.cursor = load_image(IMAGE_DIR + 'upgrade_cursor.png')
            UpgradeWindow.flash = load_image(IMAGE_DIR + 'upgrade_flash.png')
            UpgradeWindow.max_badge = load_image(IMAGE_DIR + 'upgrade_max.png')
        self.x = x if x is not None else WINDOW_POS[0]
        self.y = y if y is not None else WINDOW_POS[1]
        self.visible = False
        self.sel = 0                   # 선택한 줄 (0 ~ 5)
        self.flash_t = 0.0
        self.fail_t = 0.0

    def toggle(self):
        self.visible = not self.visible

    # ---------- 입력 ----------
    def handle_event(self, e, levels, wallet):
        """창이 열려 있을 때만 처리. 강화에 성공하면 능력치 키('hp' 등)를 돌려줌, 아니면 None
        levels: {'hp': 3, ...} -> 성공하면 이 딕셔너리의 레벨을 1 올림
        wallet: .gold 와 .spend(amount) 가 있는 객체 (GoldDisplay 그대로 넘기면 됨)"""
        if not self.visible or e.type != SDL_KEYDOWN:
            return None
        if e.key == SDLK_UP:
            self.sel = (self.sel - 1) % len(STAT_RULES)
        elif e.key == SDLK_DOWN:
            self.sel = (self.sel + 1) % len(STAT_RULES)
        elif e.key == SDLK_RETURN:
            return self.try_upgrade(levels, wallet)
        return None

    def try_upgrade(self, levels, wallet):
        key = STAT_RULES[self.sel][0]
        lv = levels.get(key, 0)
        if is_max(key, lv) or not wallet.spend(upgrade_cost(key, lv)):
            self.fail_t = FAIL_TIME
            return None
        levels[key] = lv + 1
        self.flash_t = FLASH_TIME
        return key

    def update(self):
        dt = game_framework.frame_time
        self.flash_t = max(0.0, self.flash_t - dt)
        self.fail_t = max(0.0, self.fail_t - dt)

    # ---------- 숫자 그리기 ----------
    def _width(self, text):
        return sum(ADVANCE.get(ch, 18) for ch in text)

    def _text(self, text, right, center_y, row):
        x = right - self._width(text)
        for ch in text:
            adv = ADVANCE.get(ch, 18)
            self.glyphs.clip_draw(GLYPHS.index(ch) * GW, row * GH, GW, GH, x + adv / 2, center_y)
            x += adv

    def _at(self, wx, wy):
        """창 그림 좌표(왼쪽 위 기준) -> 화면 좌표"""
        return self.x - WIN_W // 2 + wx, self.y + WIN_H // 2 - wy

    @staticmethod
    def _fmt(val, digits):
        return f'{val:.{digits}f}' if digits else f'{int(val):,}'

    # ---------- 그리기 ----------
    def draw(self, levels, gold):
        """levels: 강화 레벨 딕셔너리 / gold: 보유 골드"""
        if not self.visible:
            return
        self.window.draw(self.x, self.y)

        for i, (key, _, _, _, digits) in enumerate(STAT_RULES):
            lv = levels.get(key, 0)
            cy = ROW0 + i * ROW_H
            shake = 0
            if i == self.sel and self.fail_t > 0:              # 실패: 좌우로 흔들림
                shake = int(6 * (self.fail_t / FAIL_TIME)) * (1 if int(self.fail_t * 40) % 2 else -1)

            if i == self.sel:
                rx, ry = self._at(ROW_LEFT, cy)
                self.cursor.draw_to_origin(rx, ry - 26)
                if self.flash_t > 0:
                    self.flash.opacify(self.flash_t / FLASH_TIME)
                    self.flash.draw_to_origin(rx, ry - 26)
                    self.flash.opacify(1.0)

            x, y = self._at(LV_X, cy)
            self._text(str(lv), x + self._width(str(lv)), y, WHITE)
            x, y = self._at(CUR_RIGHT, cy)
            self._text(self._fmt(stat_value(key, lv), digits), x, y, WHITE)

            if is_max(key, lv):
                x, y = self._at(MAX_X, cy)
                self.max_badge.draw_to_origin(x + shake, y - 20)
                continue
            x, y = self._at(NEXT_RIGHT, cy)
            self._text(self._fmt(stat_value(key, lv + 1), digits), x, y, GREEN)
            cost = upgrade_cost(key, lv)
            x, y = self._at(COST_RIGHT, cy)
            self._text(f'{cost:,}', x + shake, y, GOLD if gold >= cost else RED)

        x, y = self._at(COST_RIGHT, GOLD_Y)
        self._text(f'{int(gold):,}', x, y, GOLD)
