from datetime import datetime
import db_connection as db
import game
import pygame
import pygame_menu
import random


class Settings:
    def __init__(self) -> None:
        self.level = game.Game.Level.EASY
        self.player_name = ""

    def set_level(self, level: game.Game.Level) -> None:
        self.level = level

    def set_player_name(self, name: str) -> None:
        self.player_name = name


class App:
    def __init__(self) -> None:
        self._running = True
        self._settings = Settings()
        self._game = None

        random.seed(datetime.now().microsecond)

        with open("db_connection.txt", "r") as file:
            self._db_conn = db.DbConnection(file.read())
            if self._db_conn.is_connected():
                print(self._db_conn.get_highest_scores(limit=10))

        pygame.init()
        pygame.font.init()
        self._screen = pygame.display.set_mode((800, 800))
        self._clock = pygame.time.Clock()
        self._initialize_menu()

    def __del__(self):
        print("Application exited")
        pygame.quit()

    def is_running(self) -> bool:
        return self._running

    def loop(self) -> None:
        events = pygame.event.get()

        if any(e.type == pygame.QUIT for e in events):
            self._running = False
            return

        if self._menu.is_enabled():
            self._menu.update(events)
            if self._menu.is_enabled():
                self._menu.draw(self._screen)

        if self._game is not None:
            self._game.update(events)
            self._game.draw(self._screen)
            if not self._game.is_running():
                self._menu.enable()

                if self._db_conn is not None and self._db_conn.is_connected():
                    self._db_conn.update_highest_score(
                        self._settings.player_name, self._game.get_score()
                    )

                self._game = None

        pygame.display.flip()
        self._clock.tick(30)

    def _initialize_menu(self) -> None:
        self._menu = pygame_menu.Menu("Start game", 400, 300)
        self._menu.add.text_input(
            "Player: ", onchange=lambda text: self._settings.set_player_name(text)
        )
        self._menu.add.selector(
            "Level: ",
            [
                ("Easy", game.Game.Level.EASY),
                ("Medium", game.Game.Level.MEDIUM),
                ("Hard", game.Game.Level.HARD),
            ],
            onchange=lambda _, level: self._settings.set_level(level),
        )
        self._menu.add.button("Play", lambda: self._initialize_game())
        self._menu.add.button("Quit", pygame_menu.events.EXIT)

    def _initialize_game(self) -> None:
        self._menu.disable()

        if self._db_conn is not None and self._db_conn.is_connected():
            self._db_conn.create_user(self._settings.player_name)
            highest_score = self._db_conn.get_highest_score(self._settings.player_name)
        else:
            highest_score = 0

        self._game = game.Game(self._settings.level, highest_score)
        pygame.time.set_timer(game.Game.MOVEEVENT, 250 // self._settings.level.value)


def main() -> None:
    app = App()

    while app.is_running():
        app.loop()


if __name__ == "__main__":
    main()
