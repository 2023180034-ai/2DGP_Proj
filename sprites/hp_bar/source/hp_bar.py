"""체력 바 UI: 보스 체력 바 + 플레이어 체력 바

공통 동작
- 맞으면 빨간 체력이 바로 줄고, 줄어든 만큼 노란 '깎인 체력'이 잠깐 남았다가 천천히 따라 줄어듦
- 맞는 순간 바가 하얗게 번쩍이고 살짝 흔들림

화면 위치는 아직 정하지 않음 -> 아래 BOSS_POS, PLAYER_POS 값만 바꾸면 됨
"""
import random

from pico2d import load_image, load_font

import game_framework

IMAGE_DIR = 'sprites/ui/'          # 실행 위치 기준 경로 - 프로젝트에 맞게 수정
FONT_PATH = None                   # 글자(이름·숫자)를 쓰려면 한글 TTF 경로 (예: 'font/NanumGothicBold.ttf')
SCALE = 3                          # 도트 원본 -> 화면 배율

# ---- 화면 위치 (체력 바 가운데, 화면 좌표) : 추후 지정 ----
BOSS_POS = (640, 60)               # TODO: 위치 확정 후 수정
PLAYER_POS = (230, 680)            # TODO: 위치 확정 후 수정

CHIP_DELAY = 0.6                   # 맞은 뒤 노란 체력이 버티는 시간 (초)
CHIP_SPEED = 0.35                  # 노란 체력이 줄어드는 속도 (초당 최대 체력의 비율)
FLASH_TIME = 0.08                  # 하얗게 번쩍이는 시간 (초)
SHAKE_TIME = 0.15                  # 흔들리는 시간 (초)


def format_k(hp):
    """10000 -> '10K', 7250 -> '7.3K'"""
    k = hp / 1000
    return f'{k:.0f}K' if k == int(k) else f'{k:.1f}K'


class _ChipBar:
    """보스/플레이어 공통: 체력 값과 줄어드는 애니메이션"""
    # 하위 클래스에서 정함
    PREFIX = ''
    FRAME_W = FRAME_H = BAR_W = BAR_H = BAR_OX = BAR_OY = 0
    SHAKE_PX = 2
    _images = {}

    def __init__(self, max_hp, x, y):
        key = self.PREFIX
        if key not in _ChipBar._images:
            _ChipBar._images[key] = {n: load_image(f'{IMAGE_DIR}{key}_{n}.png')
                                     for n in ('frame', 'bg', 'fill', 'chip', 'flash')}
        self.img = _ChipBar._images[key]
        self.font = load_font(FONT_PATH, 22) if FONT_PATH else None
        self.x, self.y = x, y
        self.max_hp = max_hp
        self.hp = max_hp                   # 실제 체력 (빨간 바)
        self.chip_hp = max_hp              # 깎인 체력 표시 (노란 바)
        self.delay = 0.0
        self.flash_t = 0.0
        self.shake_t = 0.0

    # ---------- 값 바꾸기 ----------
    def damage(self, amount):
        self.hp = max(0, self.hp - amount)
        self.delay = CHIP_DELAY            # 연타 중에는 노란 바가 계속 버팀
        self.flash_t = FLASH_TIME
        self.shake_t = SHAKE_TIME

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
        self.chip_hp = max(self.chip_hp, self.hp)

    def set_hp(self, hp):
        """체력을 직접 맞출 때 (예: 다시 도전할 때 가득 채우기)"""
        self.hp = self.chip_hp = max(0, min(self.max_hp, hp))

    def is_dead(self):
        return self.hp <= 0

    # ---------- 매 프레임 ----------
    def update(self):
        dt = game_framework.frame_time
        self.flash_t = max(0.0, self.flash_t - dt)
        self.shake_t = max(0.0, self.shake_t - dt)
        if self.chip_hp > self.hp:
            if self.delay > 0:
                self.delay -= dt
            else:
                self.chip_hp = max(self.hp, self.chip_hp - self.max_hp * CHIP_SPEED * dt)
        else:
            self.chip_hp = self.hp

    def _bar(self, image, ratio, left, bottom):
        w = int(self.BAR_W * ratio)
        if w > 0:
            image.clip_draw_to_origin(0, 0, w, self.BAR_H, left, bottom, w * SCALE, self.BAR_H * SCALE)

    def _draw_bar(self):
        """틀과 바를 그리고, 틀의 (왼쪽, 아래, 오른쪽, 위) 화면 좌표를 돌려줌"""
        shaking = self.shake_t > 0
        sx = random.randint(-self.SHAKE_PX, self.SHAKE_PX) if shaking else 0
        sy = random.randint(-1, 1) if shaking else 0
        left = self.x - self.FRAME_W * SCALE // 2 + sx
        bottom = self.y - self.FRAME_H * SCALE // 2 + sy
        il = left + self.BAR_OX * SCALE
        ib = bottom + self.BAR_OY * SCALE
        im = self.img
        im['frame'].clip_draw_to_origin(0, 0, self.FRAME_W, self.FRAME_H, left, bottom,
                                        self.FRAME_W * SCALE, self.FRAME_H * SCALE)
        self._bar(im['bg'], 1.0, il, ib)
        self._bar(im['chip'], self.chip_hp / self.max_hp, il, ib)
        self._bar(im['flash'] if self.flash_t > 0 else im['fill'], self.hp / self.max_hp, il, ib)
        return left, bottom, left + self.FRAME_W * SCALE, bottom + self.FRAME_H * SCALE


class BossHpBar(_ChipBar):
    """화면 아래쪽 큰 보스 체력 바. 위에 보스 이름(왼쪽)과 K 단위 체력(오른쪽)"""
    PREFIX = 'boss_hp'
    FRAME_W, FRAME_H = 260, 12
    BAR_W, BAR_H = 250, 6
    BAR_OX, BAR_OY = 5, 3
    SHAKE_PX = 3

    def __init__(self, max_hp, name=None, x=None, y=None):
        super().__init__(max_hp, x if x is not None else BOSS_POS[0], y if y is not None else BOSS_POS[1])
        self.name = name

    def draw(self):
        left, bottom, right, top = self._draw_bar()
        if self.font:
            ty = top + 18
            if self.name:
                self.font.draw(left + 6, ty, self.name, (236, 226, 210))
            text = f'{format_k(self.hp)} / {format_k(self.max_hp)}'
            self.font.draw(right - 12 * len(text), ty, text, (236, 226, 210))


class PlayerHpBar(_ChipBar):
    """플레이어 체력 바 (왼쪽 붉은 보석 장식). 오른쪽에 '현재 / 최대' 숫자"""
    PREFIX = 'player_hp'
    FRAME_W, FRAME_H = 130, 12
    BAR_W, BAR_H = 110, 6
    BAR_OX, BAR_OY = 17, 3
    SHAKE_PX = 2

    def __init__(self, max_hp, x=None, y=None):
        super().__init__(max_hp, x if x is not None else PLAYER_POS[0], y if y is not None else PLAYER_POS[1])

    def set_max_hp(self, max_hp, refill=True):
        """강화로 최대 체력이 오를 때 (바 길이는 그대로, 비율만 바뀜)"""
        self.max_hp = max_hp
        if refill:
            self.set_hp(max_hp)
        else:
            self.hp = min(self.hp, max_hp)
            self.chip_hp = min(self.chip_hp, max_hp)

    def draw(self):
        left, bottom, right, top = self._draw_bar()
        if self.font:
            text = f'{int(self.hp)} / {int(self.max_hp)}'
            self.font.draw(right + 10, (bottom + top) // 2, text, (236, 226, 210))
