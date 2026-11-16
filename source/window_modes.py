"""게임을 멈추고 띄우는 창 모드: 캐릭터 정보 창(C 키), 능력치 강화 창

둘 다 맵 선택 패널(M 키)처럼 game_framework.push_mode()로 띄워서,
창이 열린 동안 뒤의 게임(IngameMode)은 update되지 않고 화면만 그대로 보인다.
"""
import pico2d

import game_framework


class StatusMode(game_framework.Mode):
    """C 키: 현재 능력치·보유 골드·특수 재화를 보여 주는 정보 창. C 또는 ESC로 닫기."""

    def __init__(self, ingame_mode):
        self.ingame_mode = ingame_mode

    def enter(self):
        self.ingame_mode.status_window.visible = True

    def exit(self):
        self.ingame_mode.status_window.visible = False

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key in (
            pico2d.SDLK_c,
            pico2d.SDLK_ESCAPE,
        ):
            game_framework.pop_mode()

    def draw(self):
        ingame = self.ingame_mode
        ingame.draw()
        ingame.status_window.draw(
            ingame.levels,
            ingame.gold_ui.gold,
            ingame.special,
        )


class UpgradeMode(game_framework.Mode):
    """사망 화면의 '강화' 버튼으로만 여는 능력치 강화 창.

    U 또는 ESC로 닫으면 사망 화면으로 돌아간다.
    """

    def __init__(self, ingame_mode):
        self.ingame_mode = ingame_mode

    def enter(self):
        self.ingame_mode.upgrade_window.visible = True

    def exit(self):
        self.ingame_mode.upgrade_window.visible = False

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key in (
            pico2d.SDLK_u,
            pico2d.SDLK_ESCAPE,
        ):
            game_framework.pop_mode()
            return
        ingame = self.ingame_mode
        upgraded = ingame.upgrade_window.handle_event(
            event,
            ingame.levels,
            ingame.gold_ui,
        )
        if upgraded:
            ingame.apply_upgrades()

    def update(self, delta_time):
        self.ingame_mode.upgrade_window.update()
        self.ingame_mode.gold_ui.update()

    def draw(self):
        ingame = self.ingame_mode
        ingame.draw()
        ingame.upgrade_window.draw(ingame.levels, ingame.gold_ui.gold)
