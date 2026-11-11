import os
from pathlib import Path

import pico2d as pico

from game import Game


ROOT = Path(__file__).resolve().parent
TILE_SIZE = 52
MARGIN = 28
MAP_BOTTOM = 106
COLORS = {
    "#": (39, 49, 69),
    ".": (79, 90, 110),
    "~": (37, 101, 91),
    "E": (43, 105, 149),
    "B": (79, 90, 110),
}
MOVES = {
    pico.SDLK_w: (0, -1), pico.SDLK_UP: (0, -1),
    pico.SDLK_d: (1, 0), pico.SDLK_RIGHT: (1, 0),
    pico.SDLK_s: (0, 1), pico.SDLK_DOWN: (0, 1),
    pico.SDLK_a: (-1, 0), pico.SDLK_LEFT: (-1, 0),
    pico.SDLK_SPACE: (0, 0),
}


def draw(game, font, title_font):
    def cell_position(cell):
        x, y = cell
        return MARGIN + x * TILE_SIZE, MAP_BOTTOM + (game.map.height - 1 - y) * TILE_SIZE

    def marker(cell, label, color, inset):
        x, y = cell_position(cell)
        pico.draw_rectangle(
            x + inset, y + inset, x + TILE_SIZE - inset - 1,
            y + TILE_SIZE - inset - 1, *color, filled=True,
        )
        font.draw(x + TILE_SIZE // 2 - 9, y + TILE_SIZE // 2, label, (255, 255, 255))

    pico.clear_canvas()
    pico.draw_rectangle(
        0, 0, pico.get_canvas_width() - 1, pico.get_canvas_height() - 1,
        18, 24, 37, filled=True,
    )
    map_top = MAP_BOTTOM + game.map.height * TILE_SIZE
    title_font.draw(MARGIN, map_top + 42, "소리 도둑", (249, 250, 252))
    font.draw(MARGIN, map_top + 15, "소리 병을 챙겨 출구로 돌아오세요.", (201, 214, 234))

    for y, row in enumerate(game.map.tiles):
        for x, tile in enumerate(row):
            cell = (x, y)
            left, bottom = cell_position(cell)
            right, top = left + TILE_SIZE - 3, bottom + TILE_SIZE - 3
            pico.draw_rectangle(left, bottom, right, top, *COLORS[tile], filled=True)
            if cell in game.sound_area:
                pico.draw_rectangle(left, bottom, right, top, 209, 176, 252)
            if tile == "E":
                marker(cell, "출", (32, 96, 165), 9)
            elif tile == "B" and not game.has_bottle:
                marker(cell, "병", (135, 100, 19), 9)

    marker(game.guard.position, "경", (175, 81, 36), 6)
    if game.player != game.guard.position:
        marker(game.player, "나", (78, 76, 179), 6)

    status = f"{game.turn}턴   |   소리 병 {'획득' if game.has_bottle else '미획득'}   |   경비 {game.guard.mode}"
    if game.result == "성공":
        status = f"{game.turn}턴 만에 탈출 성공   |   R로 다시 시작"
    elif game.result == "실패":
        status = "경비에게 잡혔습니다   |   R로 재도전"
    elif game.blocked:
        status += "   |   벽에 막힘"
    font.draw(MARGIN, 80, status, (249, 250, 252))
    font.draw(MARGIN, 52, "초록색 카펫은 무음   |   보라색 테두리는 이번 턴의 발소리 범위", (201, 214, 234))
    font.draw(MARGIN, 26, "WASD / 방향키  이동     Space  대기     R  재시작     Esc  종료", (201, 214, 234))
    pico.update_canvas()


def run():
    game = Game(ROOT / "maps" / "week1.json")
    pico.open_canvas(
        game.map.width * TILE_SIZE + 2 * MARGIN,
        MAP_BOTTOM + game.map.height * TILE_SIZE + 70,
    )
    try:
        font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "malgun.ttf"
        font = pico.load_font(str(font_path), 17)
        title_font = pico.load_font(str(font_path), 28)
        while True:
            for event in pico.get_events():
                if event.type == pico.SDL_QUIT:
                    return
                if event.type != pico.SDL_KEYDOWN:
                    continue
                if event.key == pico.SDLK_ESCAPE:
                    return
                if event.key == pico.SDLK_r:
                    game.reset()
                elif event.key in MOVES:
                    game.act(MOVES[event.key])
            draw(game, font, title_font)
            pico.delay(1 / 30)
    finally:
        pico.close_canvas()


if __name__ == "__main__":
    run()
