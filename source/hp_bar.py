from pathlib import Path
import random

import pico2d


SCALE = 3
FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"
BOSS_POS = (990, 1000)
PLAYER_POS = (215, 38)

CHIP_DELAY = 0.6
CHIP_SPEED = 0.35
FLASH_TIME = 0.08
SHAKE_TIME = 0.15

IMAGE_DIRECTORY = (
    Path(__file__).resolve().parent.parent / "sprites" / "ui"
)


def format_k(hp):
    value = hp / 1000
    return f"{value:.0f}K" if value == int(value) else f"{value:.1f}K"


class _ChipBar:
    PREFIX = ""
    FRAME_WIDTH = FRAME_HEIGHT = BAR_WIDTH = BAR_HEIGHT = 0
    BAR_OFFSET_X = BAR_OFFSET_Y = 0
    SHAKE_PIXELS = 2
    _images = {}

    def __init__(self, target, x, y):
        """target: hp, max_hp 속성을 가진 객체(Player, Boss). 바는 표시만 한다."""
        if target.max_hp <= 0:
            raise ValueError("max_hp must be greater than zero")

        if self.PREFIX not in self._images:
            self._images[self.PREFIX] = {
                name: pico2d.load_image(
                    str(IMAGE_DIRECTORY / f"{self.PREFIX}_{name}.png")
                )
                for name in ("frame", "bg", "fill", "chip", "flash")
            }
        self.images = self._images[self.PREFIX]
        self.font = pico2d.load_font(FONT_PATH, 22) if FONT_PATH else None
        self.target = target
        self.x = x
        self.y = y
        self.hp = target.hp
        self.chip_hp = target.hp
        self.delay = 0
        self.flash_time = 0
        self.shake_time = 0

    @property
    def max_hp(self):
        return self.target.max_hp

    def update(self, delta_time):
        delta_time = max(0, delta_time)
        target_hp = max(0, min(self.max_hp, self.target.hp))
        if target_hp < self.hp:
            self.delay = CHIP_DELAY
            self.flash_time = FLASH_TIME
            self.shake_time = SHAKE_TIME
        self.hp = target_hp
        self.chip_hp = min(max(self.chip_hp, self.hp), self.max_hp)

        self.flash_time = max(0, self.flash_time - delta_time)
        self.shake_time = max(0, self.shake_time - delta_time)
        if self.chip_hp > self.hp:
            if self.delay > 0:
                self.delay = max(0, self.delay - delta_time)
            else:
                self.chip_hp = max(
                    self.hp,
                    self.chip_hp - self.max_hp * CHIP_SPEED * delta_time,
                )

    def _draw_fill(self, image, ratio, left, bottom):
        width = int(self.BAR_WIDTH * ratio)
        if width > 0:
            image.clip_draw_to_origin(
                0,
                0,
                width,
                self.BAR_HEIGHT,
                left,
                bottom,
                width * SCALE,
                self.BAR_HEIGHT * SCALE,
            )

    def _draw_bar(self):
        if self.shake_time > 0:
            offset_x = random.randint(-self.SHAKE_PIXELS, self.SHAKE_PIXELS)
            offset_y = random.randint(-1, 1)
        else:
            offset_x = offset_y = 0

        left = self.x - self.FRAME_WIDTH * SCALE // 2 + offset_x
        bottom = self.y - self.FRAME_HEIGHT * SCALE // 2 + offset_y
        bar_left = left + self.BAR_OFFSET_X * SCALE
        bar_bottom = bottom + self.BAR_OFFSET_Y * SCALE
        self.images["frame"].clip_draw_to_origin(
            0,
            0,
            self.FRAME_WIDTH,
            self.FRAME_HEIGHT,
            left,
            bottom,
            self.FRAME_WIDTH * SCALE,
            self.FRAME_HEIGHT * SCALE,
        )
        self._draw_fill(self.images["bg"], 1, bar_left, bar_bottom)
        self._draw_fill(
            self.images["chip"],
            self.chip_hp / self.max_hp,
            bar_left,
            bar_bottom,
        )
        fill = self.images["flash"] if self.flash_time > 0 else self.images["fill"]
        self._draw_fill(fill, self.hp / self.max_hp, bar_left, bar_bottom)
        return (
            left,
            bottom,
            left + self.FRAME_WIDTH * SCALE,
            bottom + self.FRAME_HEIGHT * SCALE,
        )


class BossHpBar(_ChipBar):
    PREFIX = "boss_hp"
    FRAME_WIDTH, FRAME_HEIGHT = 260, 12
    BAR_WIDTH, BAR_HEIGHT = 250, 6
    BAR_OFFSET_X, BAR_OFFSET_Y = 5, 3
    SHAKE_PIXELS = 3

    def __init__(self, target, name=None, x=None, y=None):
        super().__init__(
            target,
            BOSS_POS[0] if x is None else x,
            BOSS_POS[1] if y is None else y,
        )
        self.name = name

    def draw(self):
        left, _, right, top = self._draw_bar()
        if self.font:
            text_y = top + 18
            if self.name:
                self.font.draw(left + 6, text_y, self.name, (236, 226, 210))
            text = f"{format_k(self.hp)} / {format_k(self.max_hp)}"
            self.font.draw(
                right - 12 * len(text),
                text_y,
                text,
                (236, 226, 210),
            )


class PlayerHpBar(_ChipBar):
    PREFIX = "player_hp"
    FRAME_WIDTH, FRAME_HEIGHT = 130, 12
    BAR_WIDTH, BAR_HEIGHT = 110, 6
    BAR_OFFSET_X, BAR_OFFSET_Y = 17, 3

    def __init__(self, target, x=None, y=None):
        super().__init__(
            target,
            PLAYER_POS[0] if x is None else x,
            PLAYER_POS[1] if y is None else y,
        )

    def draw(self):
        _, bottom, right, top = self._draw_bar()
        if self.font:
            text = f"{int(self.hp)} / {int(self.max_hp)}"
            self.font.draw(
                right + 10,
                (bottom + top) // 2,
                text,
                (236, 226, 210),
            )
