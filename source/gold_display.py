"""재화(골드) 표시 UI

- 패널 왼쪽에 동전, 오른쪽에 보유 골드 (예: 12,345)
- 골드가 늘면 숫자가 빠르게 올라가고, 동전이 한 바퀴 돌며, 패널 아래에 '+N'이 떠올랐다 사라짐
- 숫자는 도트 글꼴 이미지(gold_digits.png)로 그려서 따로 폰트가 필요 없음

화면 위치는 아직 정하지 않음 -> GOLD_POS 값만 바꾸면 됨
"""
from pathlib import Path

from pico2d import load_image

import game_framework

IMAGE_DIR = str(Path(__file__).resolve().parent.parent / 'sprites' / 'ui') + '/'
SCALE = 3
# 오른쪽 아래 (1980x1080 기준, 패널 234x48 가운데). 아래에 '+N'이 뜰 자리를 남겨 둠
GOLD_POS = (1980 - 20 - 78 * 3 // 2, 70)

PANEL_W, PANEL_H = 78, 16          # 패널 원본 크기
COIN = 12                          # 동전 한 칸 크기 (6프레임)
CHARS = '0123456789,+-'
CW, CH = 7, 9                      # 글자 한 칸 (테두리 포함)
ADVANCE = 6                        # 글자 간격 (테두리 1px 겹침)

COUNT_TIME = 0.5                   # 숫자가 새 값까지 올라가는 시간 (초)
SPIN_FPS = 14                      # 동전 회전 속도
POPUP_TIME = 0.9                   # '+N'이 떠 있는 시간


class GoldDisplay:
    panel = coin = digits = None

    def __init__(self, gold=0, x=None, y=None):
        if GoldDisplay.panel is None:
            GoldDisplay.panel = load_image(IMAGE_DIR + 'gold_panel.png')
            GoldDisplay.coin = load_image(IMAGE_DIR + 'gold_coin.png')
            GoldDisplay.digits = load_image(IMAGE_DIR + 'gold_digits.png')
        self.x = x if x is not None else GOLD_POS[0]
        self.y = y if y is not None else GOLD_POS[1]
        self.gold = gold                   # 실제 보유 골드
        self.shown = float(gold)           # 화면에 보이는 숫자 (올라가는 중)
        self.speed = 0.0
        self.spin = 0.0                    # 남은 회전 시간
        self.popups = []                   # [남은 시간, 금액]

    # ---------- 값 바꾸기 ----------
    def add(self, amount):
        """골드 획득 (보스 피해 x 획득 배율). 소수는 버림"""
        amount = int(amount)
        if amount <= 0:
            return
        self.gold += amount
        self.speed = max(1.0, (self.gold - self.shown) / COUNT_TIME)
        self.spin = 6 / SPIN_FPS
        if self.popups and self.popups[-1][0] > POPUP_TIME - 0.25:    # 연타는 한 덩어리로 합침
            self.popups[-1] = [POPUP_TIME, self.popups[-1][1] + amount]
        else:
            self.popups.append([POPUP_TIME, amount])

    def spend(self, amount):
        """강화에 사용. 모자라면 False"""
        if amount > self.gold:
            return False
        self.gold -= amount
        self.shown = float(self.gold)
        return True

    def set(self, gold):
        self.gold = gold
        self.shown = float(gold)

    # ---------- 매 프레임 ----------
    def update(self):
        dt = game_framework.frame_time
        if self.shown < self.gold:
            self.shown = min(self.gold, self.shown + self.speed * dt)
        self.spin = max(0.0, self.spin - dt)
        for p in self.popups:
            p[0] -= dt
        self.popups = [p for p in self.popups if p[0] > 0]

    def _text(self, text, left, bottom, alpha=1.0):
        img = self.digits
        img.opacify(alpha)
        for k, ch in enumerate(text):
            i = CHARS.index(ch)
            img.clip_draw_to_origin(i * CW, 0, CW, CH, left + k * ADVANCE * SCALE, bottom, CW * SCALE, CH * SCALE)
        img.opacify(1.0)

    def draw(self):
        left = self.x - PANEL_W * SCALE // 2
        bottom = self.y - PANEL_H * SCALE // 2
        self.panel.clip_draw_to_origin(0, 0, PANEL_W, PANEL_H, left, bottom, PANEL_W * SCALE, PANEL_H * SCALE)

        frame = int((6 / SPIN_FPS - self.spin) * SPIN_FPS) % 6 if self.spin > 0 else 0
        self.coin.clip_draw_to_origin(frame * COIN, 0, COIN, COIN, left + 3 * SCALE, bottom + 2 * SCALE,
                                      COIN * SCALE, COIN * SCALE)

        text = f'{int(self.shown):,}'
        right = left + (PANEL_W - 3) * SCALE                    # 숫자는 오른쪽 정렬
        tl = right - (ADVANCE * (len(text) - 1) + CW) * SCALE
        self._text(text, tl, bottom + 3 * SCALE)

        for t, amount in self.popups:                            # '+N' 떠오르기
            age = 1 - t / POPUP_TIME
            ptext = f'+{amount:,}'
            pl = right - (ADVANCE * (len(ptext) - 1) + CW) * SCALE
            pb = bottom - (CH + 2) * SCALE + int(age * 6 * SCALE)
            self._text(ptext, pl, pb, alpha=min(1.0, t / (POPUP_TIME * 0.5)))
