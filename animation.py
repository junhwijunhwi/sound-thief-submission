from dataclasses import dataclass


WALK_TIME = 0.18
PICKUP_TIME = 0.30
CAPTURE_TIME = 0.32
FRAME_COUNT = 4


def frame_index(elapsed, duration):
    return min(FRAME_COUNT - 1, int(FRAME_COUNT * elapsed / duration))


@dataclass
class Actor:
    cell: tuple
    facing: tuple = (0, 1)
    frame: int | None = None


@dataclass
class Walk:
    start: tuple
    end: tuple
    facing: tuple

    @classmethod
    def between(cls, start, end, facing):
        if start != end:
            facing = (end[0] - start[0], end[1] - start[1])
        return cls(start, end, facing)

    @property
    def duration(self):
        return WALK_TIME if self.start != self.end else 0

    def pose(self, elapsed):
        if elapsed < 0:
            return Actor(self.start, self.facing)
        if self.duration and elapsed < self.duration:
            progress = elapsed / self.duration
            x = self.start[0] + (self.end[0] - self.start[0]) * progress
            y = self.start[1] + (self.end[1] - self.start[1]) * progress
            return Actor((x, y), self.facing, frame_index(elapsed, self.duration))
        return Actor(self.end, self.facing)


@dataclass
class TurnAnimation:
    started: float
    player: Walk
    guard: Walk
    picked_up: bool
    captured: bool

    @property
    def guard_start(self):
        return self.player.duration + (PICKUP_TIME if self.picked_up else 0)

    @property
    def capture_start(self):
        return self.guard_start + self.guard.duration

    @property
    def duration(self):
        return self.capture_start + (CAPTURE_TIME if self.captured else 0)
