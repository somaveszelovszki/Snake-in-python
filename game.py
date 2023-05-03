from enum import Enum
import pygame
import random


class Color(Enum):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)


class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

    def axis(self) -> tuple:
        match self:
            case Direction.UP | Direction.DOWN:
                return (0, 1)
            case Direction.LEFT | Direction.RIGHT:
                return (1, 0)
            case _:
                raise Exception(f"Unknown direction: {self.name}")

    def apply(self, pos: tuple) -> tuple:
        match self:
            case Direction.UP:
                return (pos[0], pos[1] - 1)
            case Direction.DOWN:
                return (pos[0], pos[1] + 1)
            case Direction.LEFT:
                return (pos[0] - 1, pos[1])
            case Direction.RIGHT:
                return (pos[0] + 1, pos[1])
            case _:
                raise Exception(f"Unknown direction: {self.name}")


def direction(key: int) -> Direction:
    match key:
        case pygame.K_UP | pygame.K_w:
            return Direction.UP
        case pygame.K_DOWN | pygame.K_s:
            return Direction.DOWN
        case pygame.K_LEFT | pygame.K_a:
            return Direction.LEFT
        case pygame.K_RIGHT | pygame.K_d:
            return Direction.RIGHT
        case _:
            return None


class DirectionQueue:
    def __init__(self, current: Direction) -> None:
        self._current = current
        self._queue = []

    def push(self, dir: Direction) -> None:
        self._queue.append(dir)

    def pop(self) -> Direction:
        if self._queue:
            last_idx = self._get_last_valid_index()
            if last_idx is not None:
                self._current = self._queue[last_idx]
                del self._queue[: last_idx + 1]

        return self._current

    def _get_last_valid_index(self) -> int:
        try:
            return next(
                (len(self._queue) - i - 1)
                for i, dir in enumerate(self._queue[::-1])
                if dir.axis() != self._current.axis()
            )
        except:
            return None

    def __str__(self) -> str:
        return f'{{ "current": {self._current}, "queue": {self._queue} }}'


class Field:
    _BORDER_WIDTH = 5

    def __init__(self, size: int) -> None:
        self._size = size

    def get_size(self) -> int:
        return self._size

    def get_overflow_position(self, pos: tuple) -> tuple:
        return (pos[0] % self._size, pos[1] % self._size)

    def draw_block(self, screen: pygame.Surface, pos: tuple, color: Color):
        inner_surface = self._get_inner_surface(screen)
        block = inner_surface.get_size()[0] // self._size

        pygame.draw.rect(
            inner_surface, color.value, (pos[0] * block, pos[1] * block, block, block)
        )

    def draw(self, screen: pygame.Surface):
        inner_surface = self._get_inner_surface(screen)

        pygame.draw.rect(
            screen,
            Color.WHITE.value,
            pygame.Rect(
                inner_surface.get_offset()[0] - self._BORDER_WIDTH,
                inner_surface.get_offset()[1] - self._BORDER_WIDTH,
                inner_surface.get_width() + 2 * self._BORDER_WIDTH,
                inner_surface.get_height() + 2 * self._BORDER_WIDTH,
            ),
        )

        inner_surface.fill(Color.BLACK.value)

    def _get_inner_surface(self, screen) -> pygame.Surface:
        size = min(screen.get_size()) - 2 * self._BORDER_WIDTH
        return screen.subsurface(
            (screen.get_size()[0] - size) // 2,
            (screen.get_size()[1] - size) // 2,
            size,
            size,
        )


class Snake:
    def __init__(self, field: Field) -> None:
        self._alive = True
        self._field = field
        self._blocks = [(field.get_size() // 2, field.get_size() // 2)]
        self._dir_queue = DirectionQueue(random.choice(list(Direction)))
        print(f"Snake created: {self}")

    def change_direction(self, dir: Direction):
        self._dir_queue.push(dir)

    def move(self, food_pos: tuple) -> None:
        new_head_pos = self._field.get_overflow_position(
            self._dir_queue.pop().apply(self._blocks[0])
        )

        self._blocks.insert(0, new_head_pos)
        if new_head_pos != food_pos:
            self._blocks.pop()

        if self.head() in self._blocks[1 : len(self._blocks)]:
            self._alive = False

    def head(self) -> tuple:
        return tuple(list(self._blocks[0]))

    def is_alive(self) -> bool:
        return self._alive

    def draw(self, screen: pygame.Surface):
        for b in self._blocks:
            self._field.draw_block(screen, b, Color.WHITE)

    def __contains__(self, pos: tuple) -> bool:
        return pos in self._blocks

    def __len__(self) -> int:
        return len(self._blocks)

    def __str__(self) -> str:
        return f'{{ "blocks": {self._blocks}, "dir_queue": {self._dir_queue} }}'


class Food:
    def __init__(self, field: Field, snake: Snake) -> None:
        self._field = field
        self._snake = snake
        self._pos = self._snake.head()
        self.respawn()

    def respawn(self):
        while self._pos in self._snake:
            self._pos = (
                random.randint(0, self._field.get_size() - 1),
                random.randint(0, self._field.get_size() - 1),
            )
        print(f"Food respawned at: {self._pos}")

    def draw(self, screen: pygame.Surface):
        self._field.draw_block(screen, self._pos, Color.GREEN)


class Game:
    class Level(Enum):
        EASY = 1
        MEDIUM = 2
        HARD = 4

    MOVEEVENT = pygame.USEREVENT + 1

    def __init__(self, level: Level, highest_score: int) -> None:
        self._field = Field(size=20)
        self._snake = Snake(self._field)
        self._food = Food(self._field, self._snake)
        self._level = level
        self._highest_score = highest_score

    def get_score(self) -> int:
        return len(self._snake) * self._level.value

    def is_running(self) -> bool:
        return self._snake.is_alive()

    def _move(self) -> None:
        self._snake.move(self._food._pos)

        if self._food._pos == self._snake.head():
            self._food.respawn()

    def update(self, events) -> None:
        for event in events:
            match event.type:
                case pygame.QUIT:
                    self._running = False

                case pygame.KEYDOWN:
                    dir = direction(event.key)
                    if dir is not None:
                        self._snake.change_direction(dir)

                case Game.MOVEEVENT:
                    self._move()

    def draw(self, screen: pygame.Surface):
        top_bar_height = 50
        separator_height = 5

        field_surface = screen.subsurface(
            (
                0,
                top_bar_height,
                screen.get_width(),
                screen.get_height() - top_bar_height,
            )
        )

        self._field.draw(field_surface)
        self._snake.draw(field_surface)
        self._food.draw(field_surface)
