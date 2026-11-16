"""사망 화면: 'DEAD' 제목 + '다시 시작' / '강화' / '게임 종료' 버튼

- 그림(제목, 버튼 3개)을 game_over.png 한 장에 묶어 둠
- 플레이어가 죽으면 start() -> 화면이 어두워지고 제목이 떠오른 뒤 버튼이 나타남
- 위/아래 방향키 + Enter, 또는 마우스로 선택

사용법:
    from game_over import GameOverUI
    game_over = GameOverUI()
    game_over.start()                         # 플레이어 사망 시
    game_over.update(); game_over.draw()      # 매 프레임 (draw는 맨 마지막)
    result = game_over.handle_event(e)        # 'restart' / 'upgrade' / 'quit' / None
"""
from pico2d import (load_image, SDL_KEYDOWN, SDLK_UP, SDLK_DOWN, SDLK_RETURN,
                    SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN)

import game_framework

IMAGE_DIR = 'sprites/ui/'          # 실행 위치 기준 경로 - 프로젝트에 맞게 수정
SCREEN_W, SCREEN_H = 1980, 1080    # 논리 해상도 (개발 문서)

# ---------------- game_over.png 안 위치 (pico2d 아래 기준: left, bottom, w, h) ----------------
SHEET_H = 332
TITLE = (0, SHEET_H - 180, 720, 180)    # 'DEAD'
BTN_W, BTN_H = 300, 72
BTN_NORMAL_BOTTOM = SHEET_H - 252          # 보통 버튼 줄
BTN_SELECT_BOTTOM = SHEET_H - 324          # 선택된 버튼 줄
DIM = (0, 0, 8, 8)                         # 화면을 어둡게 덮는 검은 칸

# ---------------- 화면 배치 ----------------
TITLE_Y = 640                      # 제목 가운데 y
BUTTON_YS = (450, 355, 260)        # 다시 시작, 강화, 게임 종료 가운데 y
DIM_ALPHA = 0.75                   # 최대 어둡기
DIM_TIME = 0.8                     # 어두워지는 시간
TITLE_START, TITLE_TIME = 0.4, 1.0 # 제목이 나타나기 시작하는 때, 걸리는 시간
BUTTON_START = 1.4                 # 버튼이 나타나는 때 (이전엔 입력도 안 받음)

RESULTS = ('restart', 'upgrade', 'quit')


class GameOverUI:
    image = None

    def __init__(self):
        if GameOverUI.image is None:
            GameOverUI.image = load_image(IMAGE_DIR + 'game_over.png')
        self.active = False
        self.t = 0.0
        self.sel = 0

    def start(self):
        self.active = True
        self.t = 0.0
        self.sel = 0

    def stop(self):
        self.active = False

    def update(self):
        if self.active:
            self.t += game_framework.frame_time

    # ---------- 입력 ----------
    def _button_at(self, mx, my):
        for i, by in enumerate(BUTTON_YS):
            if abs(mx - SCREEN_W / 2) <= BTN_W / 2 and abs(my - by) <= BTN_H / 2:
                return i
        return None

    def handle_event(self, e):
        """버튼이 나타난 뒤에만 처리. 고르면 'restart' / 'upgrade' / 'quit'을 돌려줌"""
        if not self.active or self.t < BUTTON_START:
            return None
        if e.type == SDL_KEYDOWN:
            if e.key == SDLK_UP:
                self.sel = (self.sel - 1) % len(RESULTS)
            elif e.key == SDLK_DOWN:
                self.sel = (self.sel + 1) % len(RESULTS)
            elif e.key == SDLK_RETURN:
                return RESULTS[self.sel]
        elif e.type in (SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN):
            # pico2d 이벤트 y는 위가 0 -> 아래 기준으로 바꿈
            # (창 크기가 논리 해상도와 다르면 여기서 비율도 맞춰야 함)
            i = self._button_at(e.x, SCREEN_H - 1 - e.y)
            if i is not None:
                self.sel = i
                if e.type == SDL_MOUSEBUTTONDOWN:
                    return RESULTS[i]
        return None

    # ---------- 그리기 ----------
    def draw(self):
        if not self.active:
            return
        img = self.image
        cx = SCREEN_W // 2

        img.opacify(DIM_ALPHA * min(1.0, self.t / DIM_TIME))
        img.clip_draw_to_origin(*DIM, 0, 0, SCREEN_W, SCREEN_H)

        k = min(1.0, max(0.0, (self.t - TITLE_START) / TITLE_TIME))
        if k > 0:
            k = 1 - (1 - k) ** 2                       # 부드럽게 멈춤
            img.opacify(k)
            img.clip_draw(*TITLE, cx, TITLE_Y - 30 * (1 - k))

        if self.t >= BUTTON_START:
            img.opacify(min(1.0, (self.t - BUTTON_START) / 0.3))
            for i, by in enumerate(BUTTON_YS):
                bottom = BTN_SELECT_BOTTOM if i == self.sel else BTN_NORMAL_BOTTOM
                img.clip_draw(i * BTN_W, bottom, BTN_W, BTN_H, cx, by)
        img.opacify(1.0)
