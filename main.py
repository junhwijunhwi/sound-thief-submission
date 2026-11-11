import os
from pathlib import Path
from time import monotonic

import pico2d as pico

from animation import Actor, CAPTURE_TIME, PICKUP_TIME, TurnAnimation, Walk, frame_index
from game import Game


ROOT = Path(__file__).resolve().parent
TILE_SIZE = 52
MARGIN = 28
MAP_BOTTOM = 106
SPRITE_SIZE = 48
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


class Sprites:
    def __init__(self):
        names = (
            "player-idle", "player-walk-front", "player-walk-right",
            "hearing-guard-idle", "hearing-guard-walk", "sound-bottle",
            "player-pickup", "hearing-guard-capture",
        )
        self.images = {
            name: pico.load_image(str(ROOT / "assets" / "sprites" / f"{name}.png"))
            for name in names
        }

    def frame(self, name, x, y, index=0, bottom=0, flip=False):
        self.images[name].clip_composite_draw(
            index * SPRITE_SIZE, bottom, SPRITE_SIZE, SPRITE_SIZE,
            0, "h" if flip else "", x, y, SPRITE_SIZE, SPRITE_SIZE,
        )

    def player(self, actor, x, y):
        horizontal = actor.facing[0]
        if actor.frame is not None or not horizontal:
            direction = "right" if horizontal else "front"
            self.frame(f"player-walk-{direction}", x, y, actor.frame if actor.frame is not None else 1,
                       flip=horizontal < 0)
        else:
            self.frame("player-idle", x, y, flip=horizontal < 0)

    def guard(self, actor, x, y):
        horizontal = actor.facing[0]
        if actor.frame is None and horizontal:
            self.frame("hearing-guard-idle", x, y, flip=horizontal < 0)
        else:
            self.frame("hearing-guard-walk", x, y, actor.frame if actor.frame is not None else 1,
                       bottom=0 if horizontal else SPRITE_SIZE, flip=horizontal < 0)


def draw(game, font, title_font, sprites, player, guard, animation, elapsed):
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

    def center(cell):
        x, y = cell_position(cell)
        return x + (TILE_SIZE - 2) / 2, y + (TILE_SIZE - 2) / 2

    bottle_visible = not game.has_bottle
    pickup_frame = capture_frame = None
    if animation is not None:
        player = animation.player.pose(elapsed)
        guard = animation.guard.pose(elapsed - animation.guard_start)
        if animation.picked_up:
            if elapsed < animation.player.duration:
                bottle_visible = True
            elif elapsed < animation.guard_start:
                pickup_frame = frame_index(elapsed - animation.player.duration, PICKUP_TIME)
        if animation.captured and elapsed >= animation.capture_start:
            capture_frame = frame_index(elapsed - animation.capture_start, CAPTURE_TIME)

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
            elif tile == "B" and bottle_visible:
                sprites.images["sound-bottle"].draw(*center(cell))

    if game.result != "실패" or animation is not None:
        if pickup_frame is None:
            sprites.player(player, *center(player.cell))
        else:
            sprites.frame("player-pickup", *center(player.cell), pickup_frame, flip=player.facing[0] < 0)
    if capture_frame is None:
        sprites.guard(guard, *center(guard.cell))
    else:
        flip = guard.facing[0] < 0
        if animation.guard.duration == 0:
            flip = animation.player.start[0] < guard.cell[0]
        sprites.frame("hearing-guard-capture", *center(guard.cell), capture_frame, flip=flip)

    status = f"{game.turn}턴   |   소리 병 {'획득' if game.has_bottle else '미획득'}   |   경비 {game.guard.mode}"
    if game.result == "성공" and animation is None:
        status = f"{game.turn}턴 만에 탈출 성공   |   R로 다시 시작"
    elif game.result == "실패" and animation is None:
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
        sprites = Sprites()
        font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "malgun.ttf"
        font = pico.load_font(str(font_path), 17)
        title_font = pico.load_font(str(font_path), 28)
        player, guard = Actor(game.player), Actor(game.guard.position)
        animation = None
        pending_move = None
        while True:
            now = monotonic()
            if animation is not None and now - animation.started >= animation.duration:
                animation = None
            for event in pico.get_events():
                if event.type == pico.SDL_QUIT:
                    return
                if event.type != pico.SDL_KEYDOWN:
                    continue
                if event.key == pico.SDLK_ESCAPE:
                    return
                if event.key == pico.SDLK_r:
                    game.reset()
                    player, guard = Actor(game.player), Actor(game.guard.position)
                    animation = None
                    pending_move = None
                elif event.key in MOVES:
                    if pending_move is None and game.result is None:
                        pending_move = MOVES[event.key]
            if animation is None and pending_move is not None:
                old_turn, had_bottle = game.turn, game.has_bottle
                game.act(pending_move)
                pending_move = None
                if game.turn != old_turn:
                    player_walk = Walk.between(player.cell, game.player, player.facing)
                    guard_walk = Walk.between(guard.cell, game.guard.position, guard.facing)
                    animation = TurnAnimation(
                        now, player_walk, guard_walk, game.has_bottle and not had_bottle, game.result == "실패",
                    )
                    player = Actor(game.player, player_walk.facing)
                    guard = Actor(game.guard.position, guard_walk.facing)
                    if not animation.duration:
                        animation = None
            elapsed = now - animation.started if animation is not None else 0
            draw(game, font, title_font, sprites, player, guard, animation, elapsed)
            pico.delay(1 / 30)
    finally:
        pico.close_canvas()


if __name__ == "__main__":
    run()
