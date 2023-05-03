from enum import Enum
import pygame


class Color(Enum):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)


def get_centered_offset(parent_size: tuple, child_size: tuple) -> tuple:
    return (
        (parent_size[0] - child_size[0]) // 2,
        (parent_size[1] - child_size[1]) // 2,
    )


class Button:
    def __init__(
        self,
        offset: tuple,
        size: tuple,
        text: str,
        background_color: Color,
        hover_color: Color,
        text_color: Color,
    ) -> None:
        self._rect = pygame.Rect(offset, size)
        self.text = text
        self.background_color = background_color
        self.hover_color = hover_color
        self.text_color = text_color
        self._pressed = False

    def draw(self, surface: pygame.Surface) -> bool:
        prev_pressed = self._pressed
        self._draw_background(surface)

        text = pygame.font.Font(None, 36).render(self.text, True, self.text_color.value)
        text_offset = get_centered_offset(self._rect.size, text.get_size())
        surface.blit(
            text, (self._rect.x + text_offset[0], self._rect.y + text_offset[1])
        )

        return not prev_pressed and self._pressed

    def _draw_background(self, surface: pygame.Surface) -> None:
        abs_offset = surface.get_abs_offset()
        abs_rect = pygame.Rect(
            (abs_offset[0] + self._rect.x, abs_offset[1] + self._rect.y),
            self._rect.size,
        )

        hovered = abs_rect.collidepoint(pygame.mouse.get_pos())
        self._pressed = hovered and pygame.mouse.get_pressed(num_buttons=3)[0]

        pygame.draw.rect(surface, self.text_color.value, self._rect)

        border_width = 2
        inner_rect = pygame.Rect(
            self._rect.x + border_width,
            self._rect.y + border_width,
            self._rect.width - 2 * border_width,
            self._rect.height - 2 * border_width,
        )

        pygame.draw.rect(
            surface,
            (self.hover_color if hovered else self.background_color).value,
            inner_rect,
        )
