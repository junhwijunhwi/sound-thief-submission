import pico2d as pico

import game_framework
from play_mode import PlayMode


def run():
    mode = PlayMode()
    pico.open_canvas(*mode.canvas_size)
    try:
        game_framework.run(mode)
    finally:
        pico.close_canvas()


if __name__ == "__main__":
    run()
