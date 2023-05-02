from datetime import datetime
from enum import Enum
import db_connection as db
import pygame
import pygame_menu
import random


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
                raise Exception("Unknown direction: {}".format(self.name))

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
                raise Exception("Unknown direction: {}".format(self.name))


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
            if last_idx != None:
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
        return '{{ "current": {}, "queue": {} }}'.format(self._current, self._queue)


class Field:
    def __init__(self, size: tuple) -> None:
        self.size = size

    def get_overflow_position(self, pos: tuple) -> tuple:
        return (pos[0] % self.size[0], pos[1] % self.size[1])

    def draw_block(
        self, screen: pygame.Surface, pos: tuple, color: tuple = (255, 255, 255)
    ):
        block = screen.get_size()[0] // self.size[0]
        x = pos[0] * block
        y = pos[1] * block
        pygame.draw.rect(screen, color, (x, y, block, block))

    def draw(self, screen: pygame.Surface):
        w = screen.get_size()[0]
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(0, 0, w, w))


class Snake:
    def __init__(self, field: Field) -> None:
        self.field = field
        self._blocks = [(field.size[0] // 2, field.size[1] // 2)]
        self._dir_queue = DirectionQueue(random.choice(list(Direction)))
        print("Snake created: {}".format(self))

    def change_direction(self, dir: Direction):
        self._dir_queue.push(dir)

    def move(self, food_pos: tuple) -> None:
        new_head_pos = self.field.get_overflow_position(
            self._dir_queue.pop().apply(self._blocks[0])
        )

        self._blocks.insert(0, new_head_pos)
        if new_head_pos != food_pos:
            self._blocks.pop()

    def head(self) -> tuple:
        return tuple(list(self._blocks[0]))

    def has_loop(self) -> bool:
        return self.head() in self._blocks[1 : len(self._blocks)]

    def __len__(self) -> int:
        return len(self._blocks)

    def is_alive(self) -> bool:
        return self._blocks.count(self._blocks[0]) == 1

    def draw(self, screen: pygame.Surface):
        for b in self._blocks:
            self.field.draw_block(screen, b)

    def __contains__(self, pos: tuple) -> bool:
        return pos in self._blocks

    def __str__(self) -> str:
        return '{{ "blocks": {}, "dir_queue": {} }}'.format(
            self._blocks, self._dir_queue
        )


class Food:
    def __init__(self, field: Field, snake: Snake) -> None:
        self.field = field
        self.snake = snake
        self.pos = self.snake.head()
        self.respawn()

    def respawn(self):
        while self.pos in self.snake:
            self.pos = (
                random.randint(0, self.field.size[0] - 1),
                random.randint(0, self.field.size[1] - 1),
            )
        print("Food respawned at: {}".format(self.pos))

    def draw(self, screen: pygame.Surface):
        self.field.draw_block(screen, self.pos, (0, 255, 0))


class Game:
    class Level(Enum):
        EASY = 1
        MEDIUM = 2
        HARD = 4

    MOVEEVENT = pygame.USEREVENT + 1

    def __init__(self, level: Level) -> None:
        self._field = Field((20, 20))
        self._snake = Snake(self._field)
        self._food = Food(self._field, self._snake)
        self._level = level

    def change_snake_direction(self, dir: Direction):
        self._snake.change_direction(dir)

    def get_score(self) -> int:
        return len(self._snake) * self._level.value

    def move(self) -> bool:
        self._snake.move(self._food.pos)

        if self._snake.has_loop():
            print("Snake has a loop")
            return False

        if self._food.pos == self._snake.head():
            self._food.respawn()

        return True

    def render(self, screen: pygame.Surface):
        self._field.draw(screen)
        self._snake.draw(screen)
        self._food.draw(screen)


class Settings:
    def __init__(self) -> None:
        self.level = Game.Level.EASY
        self.player_name = ""

    def set_level(self, level: Game.Level) -> None:
        self.level = level

    def set_player_name(self, name: str) -> None:
        self.player_name = name


settings = Settings()


def run_game(screen: pygame.Surface) -> None:
    clock = pygame.time.Clock()
    running = True
    game = Game(settings.level)
    pygame.time.set_timer(Game.MOVEEVENT, 250 // settings.level.value)

    while running:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    running = False

                case pygame.KEYDOWN:
                    dir = direction(event.key)
                    if dir != None:
                        game.change_snake_direction(dir)

                case Game.MOVEEVENT:
                    success = game.move()
                    if not success:
                        running = False

        game.render(screen)
        pygame.display.flip()
        clock.tick(30)

    print("Game finished. Score: {}".format(game.get_score()))
    pygame.quit()


def show_menu(screen: pygame.Surface) -> None:
    menu = pygame_menu.Menu("Start game", 400, 300)
    menu.add.text_input(
        "Player: ", onchange=lambda text: settings.set_player_name(text)
    )
    menu.add.selector(
        "Level: ",
        [
            ("Easy", Game.Level.EASY),
            ("Medium", Game.Level.MEDIUM),
            ("Hard", Game.Level.HARD),
        ],
        onchange=lambda _, level: settings.set_level(level),
    )
    menu.add.button("Play", lambda: run_game(screen))
    menu.add.button("Quit", pygame_menu.events.EXIT)
    menu.mainloop(screen)


def main() -> None:
    random.seed(datetime.now().microsecond)
    db_conn = db.DbConnection()
    print(db_conn.getHighestScores())

    pygame.init()
    screen = pygame.display.set_mode((800, 800))
    show_menu(screen)


if __name__ == "__main__":
    main()
