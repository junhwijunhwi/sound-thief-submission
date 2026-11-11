"""게임 모드의 입력, 갱신, 렌더링 순서를 관리한다."""

from time import monotonic, sleep


def run(mode):
    try:
        mode.init()
        while mode.handle_events():
            mode.update(monotonic())
            mode.render()
            sleep(1 / 30)
    finally:
        mode.finish()
