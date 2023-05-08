import graphics
import pygame


# Stores the high-score information for a user.
class HighScore:
    def __init__(self, rank: int, name: str, score: int) -> None:
        self.rank = rank
        self.name = name
        self.score = score

    def __str__(self) -> str:
        return (
            f'{{ "rank": {self.rank}, "name": "{self.name}", "score": {self.score} }}'
        )

    def __repr__(self) -> str:
        return str(self)

    def draw(self, surface: pygame.Surface):
        text = pygame.font.Font(None, 36).render(
            f"{self.rank}. {self.name}: {self.score}", True, graphics.Color.WHITE.value
        )

        surface.blit(
            text,
            graphics.get_centered_offset(surface.get_size(), text.get_size()),
        )


# Implements a drawable top bar for the high-score window.
class HighScoreTopBar:
    def __init__(self, height: int) -> None:
        self._height = height
        self._back_button = graphics.Button(
            offset=(10, 0),
            size=(100, self._height),
            text="Back",
            background_color=graphics.Color.BLACK,
            hover_color=graphics.Color.WHITE,
            text_color=graphics.Color.WHITE,
        )

        self._back_navigation_requested = False

    def get_height(self) -> int:
        return self._height

    def back_navigation_requested(self) -> bool:
        return self._back_navigation_requested

    def draw(self, surface: pygame.Surface):
        if self._back_button.draw(surface):
            self._back_navigation_requested = True

        text = pygame.font.Font(None, 36).render(
            f"High scores", True, graphics.Color.WHITE.value
        )

        surface.blit(
            text, graphics.get_centered_offset(
                surface.get_size(), text.get_size())
        )


# Implements a drawable high-score table.
class HighScoreTable:
    def __init__(self, high_scores: list, row_size: tuple) -> None:
        self._high_scores = high_scores
        self._row_size = row_size
        self._running = True

    def is_running(self) -> bool:
        return self._running

    def get_size(self) -> tuple:
        return (self._row_size[0], self._row_size[1] * len(self._high_scores))

    def draw(self, surface: pygame.Surface):
        for i, high_score in enumerate(self._high_scores):
            offset = (
                (surface.get_width() - self._row_size[0]) // 2,
                (surface.get_height() -
                 self._row_size[1] * len(self._high_scores)) // 2
                + i * self._row_size[1],
            )

            high_score.draw(surface.subsurface(offset, self._row_size))


# Implements the high-score window that instantiates the top bar and the table,
# and draws them on the screen.
class HighScoreWindow:
    def __init__(self, high_scores: list) -> None:
        self._top_bar = HighScoreTopBar(50)
        self._table = HighScoreTable(high_scores, row_size=(400, 50))

    def is_running(self) -> bool:
        return not self._top_bar.back_navigation_requested()

    def draw(self, surface: pygame.Surface):
        surface.fill(graphics.Color.BLACK.value)

        content_size = (
            surface.get_width(),
            self._top_bar.get_height() + self._table.get_size()[1],
        )
        content_surface = surface.subsurface(
            (
                graphics.get_centered_offset(surface.get_size(), content_size),
                content_size,
            )
        )

        top_bar_surface = content_surface.subsurface(
            (0, 0, content_surface.get_width(), self._top_bar.get_height())
        )

        table_surface = content_surface.subsurface(
            (
                0,
                self._top_bar.get_height(),
                content_surface.get_width(),
                content_surface.get_height() - self._top_bar.get_height(),
            )
        )

        self._top_bar.draw(top_bar_surface)
        self._table.draw(table_surface)
