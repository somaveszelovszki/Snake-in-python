from enum import Enum
import graphics
import pygame
import random


# Represents a direction in which the snake can move.
class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

    # Gets the axis of movement (either x or y).
    def axis(self) -> tuple:
        match self:
            case Direction.UP | Direction.DOWN:
                return (0, 1)
            case Direction.LEFT | Direction.RIGHT:
                return (1, 0)
            case _:
                raise Exception(f"Unknown direction: {self.name}")

    # Transforms a position according to this direction.
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


# Converts a pressed key value to a direction.
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


# Smart queue implementation for storing the direction user commands.
# Handles corner cases such as:
#   - current direction is pressed again
#   - opposite direction is pressed
#   - direction is pressed multiple times in the same iteration
#   - multiple valid directions are pressed in the same iteration
#   - directions are pressed in the same iterations that can be executed in sequence
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


# Represents the game field.
class Field:
    _BORDER_WIDTH = 5

    def __init__(self, size: int) -> None:
        self._size = size

    def get_size(self) -> int:
        return self._size

    def get_overflow_position(self, pos: tuple) -> tuple:
        return (pos[0] % self._size, pos[1] % self._size)

    def draw_block(self, surface: pygame.Surface, pos: tuple, color: graphics.Color):
        inner_surface = self._get_inner_surface(surface)
        block = inner_surface.get_size()[0] // self._size

        pygame.draw.rect(
            inner_surface, color.value, (pos[0] *
                                         block, pos[1] * block, block, block)
        )

    def draw(self, surface: pygame.Surface):
        inner_surface = self._get_inner_surface(surface)

        pygame.draw.rect(
            surface,
            graphics.Color.WHITE.value,
            pygame.Rect(
                inner_surface.get_offset()[0] - self._BORDER_WIDTH,
                inner_surface.get_offset()[1] - self._BORDER_WIDTH,
                inner_surface.get_width() + 2 * self._BORDER_WIDTH,
                inner_surface.get_height() + 2 * self._BORDER_WIDTH,
            ),
        )

        inner_surface.fill(graphics.Color.BLACK.value)

    def _get_inner_surface(self, surface) -> pygame.Surface:
        min_dimension = min(surface.get_size()) - 2 * self._BORDER_WIDTH
        size = (min_dimension, min_dimension)
        return surface.subsurface(
            graphics.get_centered_offset(surface.get_size(), size), size
        )


# Represents the snake.
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

        if self.head() in self._blocks[1: len(self._blocks)]:
            self._alive = False

    def head(self) -> tuple:
        return tuple(list(self._blocks[0]))

    def is_alive(self) -> bool:
        return self._alive

    def draw(self, surface: pygame.Surface):
        for b in self._blocks:
            self._field.draw_block(surface, b, graphics.Color.WHITE)

    def __contains__(self, pos: tuple) -> bool:
        return pos in self._blocks

    def __len__(self) -> int:
        return len(self._blocks)

    def __str__(self) -> str:
        return f'{{ "blocks": {self._blocks}, "dir_queue": {self._dir_queue} }}'


# Represents the food target.
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

    def draw(self, surface: pygame.Surface):
        self._field.draw_block(surface, self._pos, graphics.Color.GREEN)


# Implements the drawable top bar of the game.
class GameTopBar:
    def __init__(self, highest_score: int) -> None:
        self._highest_score = highest_score
        self.score = 0

    def draw(self, surface: pygame.Surface) -> None:
        text = pygame.font.Font(None, 36).render(
            f"Score: {self.score}", True, graphics.Color.WHITE.value
        )

        surface.blit(
            text, graphics.get_centered_offset(
                surface.get_size(), text.get_size())
        )


# Represents the game, responsible for instantiating the field, the snake and the food target,
# and drawing the game components on the screen.
class Game:
    class Level(Enum):
        EASY = 1
        MEDIUM = 2
        HARD = 4

    MOVEEVENT = pygame.USEREVENT + 1

    def __init__(self, level: Level, highest_score: int) -> None:
        self._top_bar = GameTopBar(highest_score)
        self._field = Field(size=20)
        self._snake = Snake(self._field)
        self._food = Food(self._field, self._snake)
        self._level = level

    def get_score(self) -> int:
        return (len(self._snake) - 1) * self._level.value

    def is_running(self) -> bool:
        return self._snake.is_alive()

    def _move(self) -> None:
        self._snake.move(self._food._pos)

        if self._food._pos == self._snake.head():
            self._food.respawn()
            self._top_bar.score = self.get_score()

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

    def draw(self, surface: pygame.Surface):
        top_bar_height = 50

        top_bar_surface = surface.subsurface(
            (0, 0, surface.get_width(), top_bar_height)
        )
        field_surface = surface.subsurface(
            (
                0,
                top_bar_height,
                surface.get_width(),
                surface.get_height() - top_bar_height,
            )
        )

        surface.fill(graphics.Color.BLACK.value)

        self._top_bar.draw(top_bar_surface)
        self._field.draw(field_surface)
        self._snake.draw(field_surface)
        self._food.draw(field_surface)
