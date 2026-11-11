"""배경, 오브젝트, UI를 깊이 순서대로 그린다."""


class World:
    def __init__(self):
        self.layers = [[], [], []]

    def add_object(self, draw, depth=1):
        self.layers[depth].append(draw)

    def render(self, scene):
        for layer in self.layers:
            for draw in layer:
                draw(scene)

    def clear(self):
        for layer in self.layers:
            layer.clear()
