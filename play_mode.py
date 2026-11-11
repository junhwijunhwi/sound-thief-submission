import pico2d as pico

from animation import Actor, TurnAnimation, Walk
from game import Game
from game_world import World
from play_view import MAP_BOTTOM, MARGIN, ROOT, TILE_SIZE, PlayView


MOVES = {
    pico.SDLK_w: (0, -1), pico.SDLK_UP: (0, -1),
    pico.SDLK_d: (1, 0), pico.SDLK_RIGHT: (1, 0),
    pico.SDLK_s: (0, 1), pico.SDLK_DOWN: (0, 1),
    pico.SDLK_a: (-1, 0), pico.SDLK_LEFT: (-1, 0),
    pico.SDLK_SPACE: (0, 0),
}


class PlayMode:
    def __init__(self, map_path=ROOT / "maps" / "week1.json"):
        self.game = Game(map_path)
        self.world = World()
        self.canvas_size = (
            self.game.map.width * TILE_SIZE + 2 * MARGIN,
            MAP_BOTTOM + self.game.map.height * TILE_SIZE + 70,
        )

    def init(self):
        self.reset()
        view = PlayView(self.game.map)
        self.world.add_object(view.draw_board, 0)
        self.world.add_object(view.draw_actors, 1)
        self.world.add_object(view.draw_hud, 2)

    def finish(self):
        self.world.clear()

    def reset(self):
        self.game.reset()
        self.player = Actor(self.game.player)
        self.guard = Actor(self.game.guard.position)
        self.animation = None
        self.elapsed = 0
        self.pending_move = None

    def handle_events(self):
        for event in pico.get_events():
            if event.type == pico.SDL_QUIT:
                return False
            if event.type != pico.SDL_KEYDOWN:
                continue
            if event.key == pico.SDLK_ESCAPE:
                return False
            if event.key == pico.SDLK_r:
                self.reset()
            elif event.key in MOVES and self.pending_move is None and self.game.result is None:
                self.pending_move = MOVES[event.key]
        return True

    def update(self, now):
        if self.animation is not None and now - self.animation.started >= self.animation.duration:
            self.animation = None
        if self.animation is None and self.pending_move is not None:
            self.advance_turn(now)
        self.elapsed = now - self.animation.started if self.animation is not None else 0

    def advance_turn(self, now):
        game = self.game
        previous_turn, had_bottle = game.turn, game.has_bottle
        game.act(self.pending_move)
        self.pending_move = None
        if game.turn == previous_turn:
            return

        player_walk = Walk.between(self.player.cell, game.player, self.player.facing)
        guard_walk = Walk.between(self.guard.cell, game.guard.position, self.guard.facing)
        animation = TurnAnimation(
            now, player_walk, guard_walk, game.has_bottle and not had_bottle, game.result == "실패",
        )
        self.player = Actor(game.player, player_walk.facing)
        self.guard = Actor(game.guard.position, guard_walk.facing)
        self.animation = animation if animation.duration else None

    def render(self):
        pico.clear_canvas()
        self.world.render(self)
        pico.update_canvas()
