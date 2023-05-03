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
    def __init__(self, offset: tuple, size: tuple, text: str, onclick=None) -> None:
        pass

    def draw(surface: pygame.Surface):
        pass
