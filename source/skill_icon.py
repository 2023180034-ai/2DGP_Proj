"""스킬 아이콘 + 쿨타임 표시

- 스킬을 쓰면 아이콘 전체가 회백색으로 바뀌고,
  쿨타임이 줄어드는 만큼 회백색 부분의 위쪽 경계가 위에서 아래로 내려감 (경계에 흰 줄)
- 쿨타임이 끝나면 원래 색으로 돌아오며 테두리가 한 번 번쩍임
- 쿨타임 중에 또 누르면 아이콘이 살짝 흔들림 (사용 실패)

그림 (도트 원본, 화면에는 SCALE배):
    skill_<이름>_icon.png      원래 색 아이콘 (32x32, 네모 틀 포함)
    skill_<이름>_icon_cd.png   쿨타임 중 회백색 아이콘
    skill_cd_edge.png          회백색 경계의 흰 줄 (모든 스킬 공용)
    skill_ready_flash.png      쿨타임이 끝날 때 번쩍임 (모든 스킬 공용)

스킬을 판마다 갈아 끼울 수 있게, 그림 이름만 바꾸면 다른 스킬에도 그대로 쓴다.
화면 위치는 아직 정하지 않음 -> ICON_POS 값만 바꾸면 됨
"""
from pathlib import Path

from pico2d import load_image

import game_framework

IMAGE_DIR = str(Path(__file__).resolve().parent.parent / 'sprites' / 'ui') + '/'
SCALE = 3
ICON_POS = (1700, 120)             # TODO: 위치 확정 후 수정 (아이콘 가운데, 화면 좌표)

N = 32                             # 아이콘 원본 크기
INNER = 4                          # 틀 두께 (경계 흰 줄은 틀 안쪽에만 그림)
FLASH_TIME = 0.35                  # 다 찼을 때 번쩍이는 시간
DENY_TIME = 0.2                    # 쿨타임 중에 눌렀을 때 흔들리는 시간


class SkillIcon:
    edge = flash = None

    def __init__(self, name='slash', cooldown=8.0, x=None, y=None):
        """name: 그림 이름 ('slash' -> skill_slash_icon.png) / cooldown: 쿨타임(초)"""
        if SkillIcon.edge is None:
            SkillIcon.edge = load_image(IMAGE_DIR + 'skill_cd_edge.png')
            SkillIcon.flash = load_image(IMAGE_DIR + 'skill_ready_flash.png')
        self.icon = load_image(IMAGE_DIR + f'skill_{name}_icon.png')
        self.icon_cd = load_image(IMAGE_DIR + f'skill_{name}_icon_cd.png')
        self.cooldown = cooldown
        self.remain = 0.0          # 남은 쿨타임 (초)
        self.flash_t = 0.0
        self.deny_t = 0.0
        self.x = x if x is not None else ICON_POS[0]
        self.y = y if y is not None else ICON_POS[1]

    # ---------- 상태 ----------
    @property
    def ready(self):
        return self.remain <= 0

    def use(self):
        """스킬 키를 눌렀을 때 호출. 쓸 수 있으면 쿨타임 시작 후 True, 아니면 흔들고 False"""
        if not self.ready:
            self.deny_t = DENY_TIME
            return False
        self.remain = self.cooldown
        return True

    def reset(self):
        """다시 시작할 때 등: 쿨타임 없애기"""
        self.remain = 0.0

    def update(self, remain=None):
        """remain: 쿨타임을 다른 곳(Player)에서 관리할 때 그 남은 시간을 넘겨 줌.
        None이면 원래대로 아이콘이 직접 쿨타임을 줄인다."""
        dt = game_framework.frame_time
        if remain is not None:
            was = self.remain
            self.remain = max(0.0, remain)
            if self.remain > was:                  # 새로 사용함
                self.cooldown = max(self.cooldown, self.remain)
            if was > 0 and self.remain <= 0:
                self.flash_t = FLASH_TIME          # 다 참 -> 번쩍
        elif self.remain > 0:
            self.remain -= dt
            if self.remain <= 0:
                self.remain = 0.0
                self.flash_t = FLASH_TIME          # 다 참 -> 번쩍
        self.flash_t = max(0.0, self.flash_t - dt)
        self.deny_t = max(0.0, self.deny_t - dt)

    # ---------- 그리기 ----------
    def draw(self):
        x = self.x
        if self.deny_t > 0:                        # 쿨타임 중에 누름: 좌우 흔들림
            x += 4 * (1 if int(self.deny_t * 50) % 2 else -1)
        size = N * SCALE
        if self.flash_t > 0:                       # 다 찼을 때 살짝 커졌다 돌아옴
            size = int(size * (1 + 0.12 * self.flash_t / FLASH_TIME))
        left, bottom = x - size / 2, self.y - size / 2
        s = size / N                               # 원본 1px의 화면 크기

        self.icon.draw(x, self.y, size, size)

        if self.remain > 0:
            # 남은 비율만큼 아래쪽을 회백색 그림으로 덮음 -> 시간이 갈수록 경계가 아래로 내려감
            h = round(N * self.remain / self.cooldown)
            if h > 0:
                self.icon_cd.clip_draw_to_origin(0, 0, N, h, left, bottom, size, h * s)
                if INNER < h < N - INNER:
                    self.edge.draw_to_origin(left + INNER * s, bottom + (h - 1) * s, (N - 2 * INNER) * s, s)

        if self.flash_t > 0:
            self.flash.opacify(self.flash_t / FLASH_TIME)
            fs = (N + 8) * SCALE
            self.flash.draw(x, self.y, fs, fs)
            self.flash.opacify(1.0)
