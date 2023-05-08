from datetime import datetime
from enum import Enum
import db_connection
import game
import graphics
import high_score
import pygame
import pygame_menu
import random

# The following file contains sensitive information, therefore it is not added to the repository.
# If you would like to provide your own MongoDB connection,
# please implement the db_credentials module according to the db_credentials.py.sample file.
import db_credentials


# Stores settings that the user can change in the main menu.
class Settings:
    def __init__(self) -> None:
        self.level = game.Game.Level.EASY
        self.player_name = ""

    def set_level(self, level: game.Game.Level) -> None:
        self.level = level

    def set_player_name(self, name: str) -> None:
        self.player_name = name


# Represents a state of the application.
class AppState(Enum):
    INITIALIZING = 1    # App is initializing
    MENU = 2            # Main menu is shown
    GAME = 3            # Game is ongoing
    HIGH_SCORES = 4     # High scores are displayed
    EXIT_REQUESTED = 5  # User requested to exit the app


# Responsible for instantiating the main components,
# drawing the active window and handling user actions.
class App:
    def __init__(self) -> None:
        self._state = AppState.INITIALIZING
        self._settings = Settings()
        self._game = None

        random.seed(datetime.now().microsecond)

        self._db_conn = db_connection.DbConnection(
            db_credentials.DB_CONNECTION_STRING)
        if self._db_conn.is_connected():
            print(self._db_conn.get_highest_scores(limit=10))

        pygame.init()
        pygame.font.init()
        self._screen = pygame.display.set_mode((800, 850))
        self._clock = pygame.time.Clock()
        pygame.display.set_caption('Snake')
        self._show_menu()

    def __del__(self):
        print("Application exited")
        pygame.quit()

    def is_running(self) -> bool:
        return self._state != AppState.EXIT_REQUESTED

    # This function is executed periodically.
    # It handles user actions and draws the active window on the display.
    def loop(self) -> None:
        events = pygame.event.get()

        if any(e.type == pygame.QUIT for e in events):
            self._state = AppState.EXIT_REQUESTED
            return

        match self._state:
            case AppState.MENU:
                self._menu.update(events)
                if self._menu is not None:
                    self._screen.fill(graphics.Color.BLACK.value)
                    self._menu.draw(self._screen)

            case AppState.GAME:
                self._game.update(events)
                self._game.draw(self._screen)
                if not self._game.is_running():
                    if (self._settings.player_name and self._db_conn.is_connected()):
                        self._db_conn.update_highest_score(
                            self._settings.player_name, self._game.get_score()
                        )

                    self._show_high_scores()

            case AppState.HIGH_SCORES:
                self._high_score_window.draw(self._screen)
                if not self._high_score_window.is_running():
                    self._show_menu()

        pygame.display.flip()
        self._clock.tick(30)

    # Initializes the main menu and sets it as the active window.
    def _show_menu(self) -> None:
        self._state = AppState.MENU
        self._menu = pygame_menu.Menu("Start game", 400, 300)
        self._game = None
        self._high_score_window = None

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

        self._menu.add.button("Play", lambda: self._show_game())
        self._menu.add.button("High scores", lambda: self._show_high_scores())
        self._menu.add.button("Quit", pygame_menu.events.EXIT)

    # Initializes the game and sets it as the active window.
    def _show_game(self) -> None:
        if (self._settings.player_name and self._db_conn.is_connected()):
            self._db_conn.create_user(self._settings.player_name)
            highest_score = self._db_conn.get_highest_score(
                self._settings.player_name)
        else:
            highest_score = 0

        pygame.time.set_timer(game.Game.MOVEEVENT, 250 //
                              self._settings.level.value)

        self._state = AppState.GAME
        self._menu = None
        self._game = game.Game(self._settings.level, highest_score)
        self._high_score_window = None

    # Initializes the high scores window and sets it as the active window.
    def _show_high_scores(self) -> None:
        if self._db_conn.is_connected():
            high_scores = self._db_conn.get_highest_scores(limit=10)
        else:
            high_scores = []

        self._state = AppState.HIGH_SCORES
        self._menu = None
        self._game = None
        self._high_score_window = high_score.HighScoreWindow(high_scores)


def main() -> None:
    app = App()

    while app.is_running():
        app.loop()


if __name__ == "__main__":
    main()
