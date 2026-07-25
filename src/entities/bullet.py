"""Off-screen Conway gliders that enter and join the visible world."""
from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Iterator

import numpy as np
import pygame

from config.game_config import GameConfig
from src.core.rules import CONWAY_LIFE


# Direction numbers preserve the historical random routing:
# 1 NE outward / SW inward, 2 NW / SE, 3 SW / NE, 4 SE / NW.
_OUTWARD_VECTORS = {
    1: (-1, 1),
    2: (-1, -1),
    3: (1, -1),
    4: (1, 1),
}
_CANONICAL_GLIDER = np.array(
    [[0, 1, 0], [0, 0, 1], [1, 1, 1]],
    dtype=np.uint8,
)
_INWARD_GLIDERS = {
    1: np.rot90(_CANONICAL_GLIDER, 3).copy(),  # down-left
    2: _CANONICAL_GLIDER.copy(),               # down-right
    3: np.rot90(_CANONICAL_GLIDER, 1).copy(),  # up-right
    4: np.rot90(_CANONICAL_GLIDER, 2).copy(),  # up-left
}


@dataclass
class InboundGlider:
    """A Conway glider evolving on an unbounded local grid."""

    pattern: np.ndarray
    start_row: int
    start_col: int
    visible_generations: int = 0

    def __post_init__(self) -> None:
        cells = np.asarray(self.pattern, dtype=np.uint8)
        if cells.ndim != 2 or not cells.size or np.any(cells > 1):
            raise ValueError("glider pattern must be a non-empty binary grid")
        self.pattern = cells.copy()

    def step(self, world_shape: tuple[int, int]) -> bool:
        """Evolve once; return False only if the local structure dies."""
        padded = np.pad(self.pattern, 1, mode="constant")
        evolved = CONWAY_LIFE.evolve(padded)
        live = np.argwhere(evolved == 1)
        if not live.size:
            self.pattern = np.zeros((0, 0), dtype=np.uint8)
            return False

        top, left = live.min(axis=0)
        bottom, right = live.max(axis=0) + 1
        self.start_row += int(top) - 1
        self.start_col += int(left) - 1
        self.pattern = np.ascontiguousarray(
            evolved[top:bottom, left:right]
        )
        if any(self.iter_visible_cells(world_shape)):
            self.visible_generations += 1
        return True

    def iter_world_cells(self) -> Iterator[tuple[int, int]]:
        for row, col in np.argwhere(self.pattern == 1):
            yield self.start_row + int(row), self.start_col + int(col)

    def iter_visible_cells(
        self,
        world_shape: tuple[int, int],
    ) -> Iterator[tuple[int, int]]:
        height, width = world_shape
        for row, col in self.iter_world_cells():
            if 0 <= row < height and 0 <= col < width:
                yield row, col

    def is_fully_inside(self, world_shape: tuple[int, int]) -> bool:
        cells = tuple(self.iter_world_cells())
        if not cells:
            return False
        height, width = world_shape
        return all(
            0 <= row < height and 0 <= col < width
            for row, col in cells
        )

    def commit(self, state: np.ndarray) -> None:
        for row, col in self.iter_world_cells():
            if 0 <= row < state.shape[0] and 0 <= col < state.shape[1]:
                state[row, col] = 1


class BulletManager:
    """Launch valid Conway gliders from beyond the visible hard boundary."""

    def __init__(self, *, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.bullets: list[InboundGlider] = []
        self.creation_counter = 0
        self.last_direction = 1
        self.world_shape = (
            GameConfig.WORLD_HEIGHT,
            GameConfig.WORLD_WIDTH,
        )

    def update(self, state, player_pos: tuple[int, int]) -> None:
        cells = np.asarray(state)
        world_shape = cells.shape
        self.world_shape = world_shape
        for glider in tuple(self.bullets):
            if not glider.step(world_shape):
                self.bullets.remove(glider)
                continue
            if glider.is_fully_inside(world_shape):
                glider.commit(cells)
                self.bullets.remove(glider)

        self.creation_counter += 1
        if self.creation_counter >= GameConfig.BULLET_CREATE_INTERVAL:
            self._create_bullet_pattern(cells, player_pos)
            self.creation_counter = 0

    def _create_bullet_pattern(
        self,
        state: np.ndarray,
        player_pos: tuple[int, int],
    ) -> None:
        self.world_shape = state.shape
        direction_num = self._choose_direction()
        start_row, start_col = self._offscreen_start(
            state.shape,
            player_pos,
            direction_num,
        )
        self.bullets.append(
            InboundGlider(
                _INWARD_GLIDERS[direction_num],
                start_row,
                start_col,
            )
        )

    def _choose_direction(self) -> int:
        choices = tuple(
            direction for direction in _OUTWARD_VECTORS
            if direction != self.last_direction
        )
        direction = self.rng.choice(choices)
        self.last_direction = direction
        return direction

    @staticmethod
    def _offscreen_start(
        world_shape: tuple[int, int],
        player_pos: tuple[int, int],
        direction_num: int,
    ) -> tuple[int, int]:
        """Project through the player, then place the full seed outside."""
        height, width = world_shape
        player_row, player_col = player_pos
        row_direction, col_direction = _OUTWARD_VECTORS[direction_num]
        row_steps = (
            player_row + 1
            if row_direction < 0
            else height - player_row
        )
        col_steps = (
            player_col + 1
            if col_direction < 0
            else width - player_col
        )

        if row_steps <= col_steps:
            hit_col = player_col + col_direction * row_steps
            start_row = -3 if row_direction < 0 else height
            start_col = max(0, min(hit_col - 1, width - 3))
        else:
            hit_row = player_row + row_direction * col_steps
            start_row = max(0, min(hit_row - 1, height - 3))
            start_col = -3 if col_direction < 0 else width
        return start_row, start_col

    def get_bullet_rects(self) -> list[pygame.Rect]:
        """Return every currently visible inbound cell for rendering."""
        cell_size = GameConfig.CELL_SIZE
        return [
            pygame.Rect(
                col * cell_size,
                row * cell_size,
                cell_size,
                cell_size,
            )
            for glider in self.bullets
            for row, col in glider.iter_visible_cells(self.world_shape)
        ]

    def get_dangerous_bullet_rects(self) -> list[pygame.Rect]:
        """Give each entering structure one visible frame before it is lethal."""
        cell_size = GameConfig.CELL_SIZE
        return [
            pygame.Rect(
                col * cell_size,
                row * cell_size,
                cell_size,
                cell_size,
            )
            for glider in self.bullets
            if glider.visible_generations > 1
            for row, col in glider.iter_visible_cells(self.world_shape)
        ]

    def clear(self) -> None:
        self.bullets.clear()
        self.creation_counter = 0
