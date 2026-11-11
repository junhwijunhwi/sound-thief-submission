import json
from collections import deque
from pathlib import Path


DIRECTIONS = ((0, -1), (1, 0), (0, 1), (-1, 0))
HEARING_RANGE = 4


class TileMap:
    def __init__(self, tiles):
        self.tiles = tiles
        self.width = len(tiles[0])
        self.height = len(tiles)

    def tile(self, cell):
        x, y = cell
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return "#"

    def search(self, start, limit=None):
        """통과 가능한 칸까지의 거리와 최단 경로의 첫 걸음을 구한다."""
        paths = {start: (0, start)}
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            distance, first_step = paths[cell]
            if limit is not None and distance >= limit:
                continue
            x, y = cell
            for dx, dy in DIRECTIONS:
                neighbor = (x + dx, y + dy)
                if neighbor in paths or self.tile(neighbor) == "#":
                    continue
                paths[neighbor] = (distance + 1, neighbor if cell == start else first_step)
                queue.append(neighbor)
        return paths


class HearingGuard:
    def __init__(self, patrol):
        self.patrol = patrol
        self.patrol_index = 0
        self.position = patrol[0]
        self.sound_target = None
        self.mode = "순찰"

    def advance(self, tile_map, sound_cells):
        paths = tile_map.search(self.position)
        # 같은 거리에서는 먼저 전달된 소리가 우선이다.
        audible = [
            cell for cell in sound_cells
            if cell in paths and paths[cell][0] <= HEARING_RANGE
        ]
        if audible:
            self.sound_target = min(audible, key=lambda cell: paths[cell][0])

        if self.sound_target is not None:
            self.mode = "소리 조사"
            self.position = paths[self.sound_target][1]
            if self.position == self.sound_target:
                self.sound_target = None
            return

        patrol_cell = self.patrol[self.patrol_index]
        if self.position != patrol_cell:
            self.mode = "순찰 복귀"
            self.position = paths[patrol_cell][1]
            return

        self.mode = "순찰"
        self.patrol_index = (self.patrol_index + 1) % len(self.patrol)
        self.position = paths[self.patrol[self.patrol_index]][1]


class Game:
    def __init__(self, map_path):
        data = json.loads(Path(map_path).read_text(encoding="utf-8"))
        self.map = TileMap(data["tiles"])
        self.start = tuple(data["player_start"])
        self.patrol = tuple(map(tuple, data["guard_patrol"]))
        self.reset()

    def reset(self):
        self.player = self.start
        self.guard = HearingGuard(self.patrol)
        self.turn = 0
        self.has_bottle = False
        self.sound_area = set()
        self.result = None
        self.blocked = False

    def act(self, direction):
        if self.result is not None:
            return

        dx, dy = direction
        x, y = self.player
        destination = (x + dx, y + dy)
        tile = self.map.tile(destination)
        self.blocked = tile == "#"
        if self.blocked:
            return

        moved = destination != self.player
        self.player = destination
        self.turn += 1
        self.sound_area = set()
        if self.player == self.guard.position:
            self.result = "실패"
            return

        if tile == "B":
            self.has_bottle = True
        sound = [destination] if moved and tile != "~" else []
        if sound:
            self.sound_area = set(self.map.search(destination, HEARING_RANGE))
        self.guard.advance(self.map, sound)

        if self.player == self.guard.position:
            self.result = "실패"
        elif tile == "E" and self.has_bottle:
            self.result = "성공"
