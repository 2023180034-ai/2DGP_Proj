import pico2d
import pico2d.pico2d as pico2d_core


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FRAME_RATE = 60

_mode_stack = []
_running = False


class Mode:
    def enter(self):
        pass

    def exit(self):
        pass

    def pause(self):
        pass

    def resume(self):
        pass

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self):
        pass


def push_mode(mode):
    if not _running:
        raise RuntimeError("Modes can only be pushed while the game is running.")

    if _mode_stack:
        _mode_stack[-1].pause()
    mode.enter()
    _mode_stack.append(mode)


def pop_mode():
    if not _running or not _mode_stack:
        raise RuntimeError("There is no active mode to pop.")

    _mode_stack.pop().exit()
    if _mode_stack:
        _mode_stack[-1].resume()
    else:
        quit()


def change_mode(mode):
    if not _running or not _mode_stack:
        raise RuntimeError("There is no active mode to change.")

    _mode_stack.pop().exit()
    mode.enter()
    _mode_stack.append(mode)


def quit():
    global _running
    _running = False


def run(start_mode):
    global _running

    if _running:
        raise RuntimeError("The game framework is already running.")

    pico2d.open_canvas(SCREEN_WIDTH, SCREEN_HEIGHT)
    _running = True
    try:
        pico2d_core.SDL_SetWindowResizable(pico2d_core.window, True)
        if pico2d_core.SDL_RenderSetLogicalSize(
            pico2d_core.renderer, SCREEN_WIDTH, SCREEN_HEIGHT
        ) != 0:
            error = pico2d_core.SDL_GetError().decode("utf-8", errors="replace")
            raise RuntimeError(f"Could not set the game canvas size: {error}")
        pico2d_core.SDL_MaximizeWindow(pico2d_core.window)

        start_mode.enter()
        _mode_stack.append(start_mode)

        while _running and _mode_stack:
            for event in pico2d.get_events():
                if event.type == pico2d.SDL_QUIT:
                    quit()
                    break
                if _mode_stack:
                    _mode_stack[-1].handle_event(event)

            if not _running or not _mode_stack:
                break

            _mode_stack[-1].update()
            pico2d.clear_canvas()
            _mode_stack[-1].draw()
            pico2d.update_canvas()
            pico2d.delay(1 / FRAME_RATE)
    finally:
        _running = False
        try:
            while _mode_stack:
                _mode_stack.pop().exit()
        finally:
            pico2d.close_canvas()
