import os
from pathlib import Path

import pico2d as pico

from animation import CAPTURE_TIME, PICKUP_TIME, frame_index


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


class PlayView:
    def __init__(self, tile_map):
        self.map_top = MAP_BOTTOM + tile_map.height * TILE_SIZE
        self.sprites = Sprites()
        font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "malgun.ttf"
        self.font = pico.load_font(str(font_path), 17)
        self.title_font = pico.load_font(str(font_path), 28)

    def cell_position(self, cell):
        x, y = cell
        return MARGIN + x * TILE_SIZE, self.map_top - (y + 1) * TILE_SIZE

    def center(self, cell):
        x, y = self.cell_position(cell)
        return x + (TILE_SIZE - 2) / 2, y + (TILE_SIZE - 2) / 2

    def draw_exit(self, cell):
        x, y = self.cell_position(cell)
        pico.draw_rectangle(
            x + 9, y + 9, x + TILE_SIZE - 10, y + TILE_SIZE - 10,
            32, 96, 165, filled=True,
        )
        self.font.draw(x + TILE_SIZE // 2 - 9, y + TILE_SIZE // 2, "출", (255, 255, 255))

    def draw_board(self, scene):
        game, animation = scene.game, scene.animation
        bottle_visible = not game.has_bottle or (
            animation is not None and animation.picked_up and scene.elapsed < animation.player.duration
        )
        pico.draw_rectangle(
            0, 0, pico.get_canvas_width() - 1, pico.get_canvas_height() - 1,
            18, 24, 37, filled=True,
        )
        for y, row in enumerate(game.map.tiles):
            for x, tile in enumerate(row):
                cell = (x, y)
                left, bottom = self.cell_position(cell)
                right, top = left + TILE_SIZE - 3, bottom + TILE_SIZE - 3
                pico.draw_rectangle(left, bottom, right, top, *COLORS[tile], filled=True)
                if cell in game.sound_area:
                    pico.draw_rectangle(left, bottom, right, top, 209, 176, 252)
                if tile == "E":
                    self.draw_exit(cell)
                elif tile == "B" and bottle_visible:
                    self.sprites.images["sound-bottle"].draw(*self.center(cell))


    def draw_actors(self, scene):
        game, animation, elapsed = scene.game, scene.animation, scene.elapsed
        player, guard = scene.player, scene.guard
        pickup_frame = capture_frame = None
        if animation is not None:
            player = animation.player.pose(elapsed)
            guard = animation.guard.pose(elapsed - animation.guard_start)
            if animation.picked_up and animation.player.duration <= elapsed < animation.guard_start:
                pickup_frame = frame_index(elapsed - animation.player.duration, PICKUP_TIME)
            if animation.captured and elapsed >= animation.capture_start:
                capture_frame = frame_index(elapsed - animation.capture_start, CAPTURE_TIME)
        if game.result != "실패" or animation is not None:
            if pickup_frame is None:
                self.sprites.player(player, *self.center(player.cell))
            else:
                self.sprites.frame("player-pickup", *self.center(player.cell), pickup_frame, flip=player.facing[0] < 0)
        if capture_frame is None:
            self.sprites.guard(guard, *self.center(guard.cell))
        else:
            flip = guard.facing[0] < 0
            if animation.guard.duration == 0:
                flip = animation.player.start[0] < guard.cell[0]
            self.sprites.frame("hearing-guard-capture", *self.center(guard.cell), capture_frame, flip=flip)


    def draw_hud(self, scene):
        game, animation = scene.game, scene.animation
        self.title_font.draw(MARGIN, self.map_top + 42, "소리 도둑", (249, 250, 252))
        self.font.draw(MARGIN, self.map_top + 15, "소리 병을 챙겨 출구로 돌아오세요.", (201, 214, 234))
        status = f"{game.turn}턴   |   소리 병 {'획득' if game.has_bottle else '미획득'}   |   경비 {game.guard.mode}"
        if game.result == "성공" and animation is None:
            status = f"{game.turn}턴 만에 탈출 성공   |   R로 다시 시작"
        elif game.result == "실패" and animation is None:
            status = "경비에게 잡혔습니다   |   R로 재도전"
        elif game.blocked:
            status += "   |   벽에 막힘"
        self.font.draw(MARGIN, 80, status, (249, 250, 252))
        self.font.draw(MARGIN, 52, "초록색 카펫은 무음   |   보라색 테두리는 이번 턴의 발소리 범위", (201, 214, 234))
        self.font.draw(MARGIN, 26, "WASD / 방향키  이동     Space  대기     R  재시작     Esc  종료", (201, 214, 234))
