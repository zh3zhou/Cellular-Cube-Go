"""Rule-aware rewards and isolated evolution-zone lifecycle."""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable, Optional

import numpy as np
import pygame

from config.game_config import GameConfig
from src.core.rules import RuleSpec, get_rule
from src.entities.evolution_zone import EvolutionZone
from src.patterns.catalog import PatternCatalog
from src.patterns.selector import PatternSelector, SelectionContext


@dataclass(frozen=True)
class RewardType:
    id: str
    rule_id: str
    color: tuple[int, int, int]
    minimum_weight: float
    padding: int


@dataclass(frozen=True)
class RewardInstance:
    row: int
    col: int
    type_id: str
    pattern_id: str | None = None

    @property
    def position(self) -> tuple[int, int]:
        return self.row, self.col


REWARD_TYPES = (
    RewardType("life", "life", (110, 220, 139), 0.55, 8),
    RewardType("highlife", "highlife", (185, 120, 255), 0.0, 8),
    RewardType("seeds", "seeds", (255, 165, 64), 0.0, 12),
    RewardType("day_night", "day_night", (90, 210, 235), 0.0, 8),
    RewardType(
        "wolfram_code_52", "wolfram_code_52", (250, 214, 64), 0.0, 10
    ),
)
REWARD_TYPE_BY_ID = {reward_type.id: reward_type for reward_type in REWARD_TYPES}


class RewardManager:
    """Spawn colored rewards and mature their local ecosystems into Conway."""

    direction_offsets = {
        # The player has already left the reward in ``direction``. Place the
        # greenhouse on the opposite side so continuing forward never forces
        # an immediate dodge or a manual backtrack.
        "up": (3, 0),
        "down": (-3, 0),
        "left": (0, 3),
        "right": (0, -3),
        "up-left": (2, 2),
        "up-right": (2, -2),
        "down-left": (-2, 2),
        "down-right": (-2, -2),
        "center": (0, 0),
        None: (0, 0),
    }

    def __init__(
        self,
        *,
        rng: random.Random | None = None,
        catalog: PatternCatalog | None = None,
    ) -> None:
        self.rng = rng or random.Random()
        self.catalog = catalog or PatternCatalog.load_default()
        self.selector = PatternSelector(self.catalog, rng=self.rng)
        self.rewards: list[RewardInstance] = []
        self.contacted_rewards: set[tuple[int, int]] = set()
        self.evolution_zones: list[EvolutionZone] = []
        self.creation_counter = 0
        self._current_state: np.ndarray | None = None
        self.committed_this_update = False
        self.successful_rewards = 0
        self.survival_seconds = 0.0
        self._context_cache_key = None
        self._context_cache: SelectionContext | None = None

    @property
    def reward_cells(self) -> list[tuple[int, int]]:
        """Compatibility view used by existing CA and diagnostics."""
        return [reward.position for reward in self.rewards]

    def get_reward_cells(self) -> list[tuple[int, int]]:
        return self.reward_cells if GameConfig.REWARD_SYSTEM_ENABLED else []

    def iter_rewards(self) -> Iterable[tuple[RewardInstance, RewardType]]:
        if not GameConfig.REWARD_SYSTEM_ENABLED:
            return ()
        return tuple(
            (reward, REWARD_TYPE_BY_ID[reward.type_id]) for reward in self.rewards
        )

    def get_evolution_zones(self) -> list[EvolutionZone]:
        return self.evolution_zones if GameConfig.REWARD_SYSTEM_ENABLED else []

    @property
    def progress(self) -> float:
        duration = max(1.0, float(GameConfig.VARIETY_DURATION_SECONDS))
        return min(
            1.0,
            0.7 * self.survival_seconds / duration
            + 0.3 * self.successful_rewards / 8.0,
        )

    def update(
        self,
        state,
        player,
        *,
        survival_seconds: float | None = None,
    ) -> Optional[tuple[int, int]]:
        """Update rewards, then advance zones and commit mature cells."""
        self.committed_this_update = False
        if survival_seconds is not None:
            self.survival_seconds = max(0.0, float(survival_seconds))
        if not GameConfig.REWARD_SYSTEM_ENABLED:
            self.rewards.clear()
            self.contacted_rewards.clear()
            self.evolution_zones.clear()
            return None

        self._current_state = np.asarray(state)
        self._cleanup_occupied_rewards()
        self._try_create_reward()
        converted = self._check_player_contact(player)
        # Keep a newly created greenhouse at its exact reward color for its
        # first rendered frame; older zones continue evolving normally.
        created_zone = (
            self.evolution_zones[-1]
            if converted is not None and self.evolution_zones
            else None
        )
        self._advance_evolution_zones(skip_zone=created_zone)
        return converted

    def _cleanup_occupied_rewards(self) -> None:
        state = self._require_state()
        retained = []
        for reward in self.rewards:
            if not state[reward.row, reward.col]:
                retained.append(reward)
            else:
                self.contacted_rewards.discard(reward.position)
        self.rewards = retained

    def _try_create_reward(self) -> None:
        self.creation_counter += 1
        if self.creation_counter < GameConfig.REWARD_CREATE_INTERVAL:
            return
        self.creation_counter = 0
        if len(self.rewards) >= GameConfig.MAX_ACTIVE_EVOLUTION_ZONES:
            return
        self._create_reward_cell()

    def _create_reward_cell(self) -> None:
        state = self._require_state()
        height, width = state.shape
        if height < 3 or width < 3:
            return
        for _ in range(100):
            row = self.rng.randint(1, height - 2)
            col = self.rng.randint(1, width - 2)
            if any(reward.position == (row, col) for reward in self.rewards):
                continue
            if not self._is_3x3_area_empty(row, col):
                continue
            reward_type, pattern_id = self.choose_reward_offer()
            self.rewards.append(
                RewardInstance(row, col, reward_type.id, pattern_id)
            )
            return

    def _selection_context(self) -> SelectionContext:
        key = (
            self.progress,
            tuple(
                (item.rule_id, self.selector.recent_ids(item.rule_id))
                for item in REWARD_TYPES
            ),
        )
        if key == self._context_cache_key and self._context_cache is not None:
            return self._context_cache
        context = self.selector.build_context(
            self.progress,
            max_width=max(1, GameConfig.WORLD_WIDTH - 2),
            max_height=max(1, GameConfig.WORLD_HEIGHT - 2),
            rule_ids=tuple(item.rule_id for item in REWARD_TYPES),
        )
        self._context_cache_key = key
        self._context_cache = context
        return context

    def reward_route_weights(
        self,
        context: SelectionContext | None = None,
    ) -> dict[str, float]:
        """Return dynamic weights; Conway always receives at least 55%."""
        context = context or self._selection_context()
        secondary = REWARD_TYPES[1:]
        scales = {
            item.id: math.sqrt(len(context.candidates.get(item.rule_id, ())))
            for item in secondary
        }
        scale_total = sum(scales.values())
        life_floor = REWARD_TYPE_BY_ID["life"].minimum_weight
        result = {"life": life_floor}
        distributed = 0.0
        for item in secondary:
            remainder = 1.0 - life_floor
            nominal = 0.0 if not scale_total else remainder * scales[item.id] / scale_total
            fresh_count = len(context.fresh_candidates.get(item.rule_id, ()))
            actual = nominal * min(1.0, fresh_count / 5.0)
            result[item.id] = actual
            distributed += actual
        result["life"] += (1.0 - life_floor) - distributed
        return result

    def choose_reward_offer(self) -> tuple[RewardType, str | None]:
        """Choose color and Pattern from one frozen candidate context."""
        if not hasattr(self.catalog, "patterns_for"):
            return REWARD_TYPE_BY_ID["life"], None
        context = self._selection_context()
        weights = self.reward_route_weights(context)
        reward_type = self.rng.choices(
            REWARD_TYPES,
            weights=[weights[item.id] for item in REWARD_TYPES],
            k=1,
        )[0]
        pattern = self.selector.select_from_context(
            reward_type.rule_id, context, record=False
        )
        if pattern is None:
            reward_type = REWARD_TYPE_BY_ID["life"]
            pattern = self.selector.select_from_context(
                "life", context, record=False
            )
        return reward_type, None if pattern is None else pattern.id

    def choose_reward_type(self) -> RewardType:
        """Compatibility view for tests and callers that only need the color."""
        return self.choose_reward_offer()[0]

    def _is_3x3_area_empty(self, row: int, col: int) -> bool:
        state = self._require_state()
        if np.any(state[row - 1 : row + 2, col - 1 : col + 2]):
            return False
        return not any(
            r0 <= row < r1 and c0 <= col < c1
            for r0, c0, r1, c1 in (
                zone.reserved_rect for zone in self.evolution_zones
            )
        )

    def _check_player_contact(self, player) -> Optional[tuple[int, int]]:
        _, player_rect = player.create_surface_and_rect()
        for reward in tuple(self.rewards):
            reward_rect = pygame.Rect(
                reward.col * GameConfig.CELL_SIZE,
                reward.row * GameConfig.CELL_SIZE,
                GameConfig.CELL_SIZE,
                GameConfig.CELL_SIZE,
            )
            if player_rect.colliderect(reward_rect):
                self.contacted_rewards.add(reward.position)
            elif reward.position in self.contacted_rewards:
                self.contacted_rewards.discard(reward.position)
                if self._convert_reward_to_zone(reward, player.last_direction):
                    return reward.position
        return None

    def _convert_reward_to_zone(
        self,
        reward: RewardInstance,
        player_direction: str | None,
    ) -> bool:
        if len(self.evolution_zones) >= GameConfig.MAX_ACTIVE_EVOLUTION_ZONES:
            return False
        reward_type = REWARD_TYPE_BY_ID[reward.type_id]
        state = self._require_state()
        world_height, world_width = state.shape

        if hasattr(self.catalog, "patterns_for"):
            context = self.selector.build_context(
                self.progress,
                max_width=max(1, world_width - 2),
                max_height=max(1, world_height - 2),
                rule_ids=(reward_type.rule_id,),
            )
            definitions = list(context.candidates.get(reward_type.rule_id, ()))
            self.rng.shuffle(definitions)
            if reward.pattern_id is not None:
                definitions.sort(key=lambda item: item.id != reward.pattern_id)
            definitions = definitions[:12]
        else:
            definition = self.catalog.select(
                reward_type.rule_id,
                self.rng,
                allow_large=True,
                max_width=max(1, world_width - 2),
                max_height=max(1, world_height - 2),
            )
            definitions = [] if definition is None else [definition]

        for definition in definitions:
            pattern = self._orient_pattern(
                definition.to_matrix(), player_direction
            )
            pattern_height, pattern_width = pattern.shape
            if (
                pattern_height > world_height or pattern_width > world_width
            ) and pattern_width <= world_height and pattern_height <= world_width:
                pattern = np.rot90(pattern).copy()
                pattern_height, pattern_width = pattern.shape
            if pattern_height > world_height or pattern_width > world_width:
                continue
            start_row, start_col = self._calculate_seed_position(
                reward.position,
                player_direction,
                pattern_height,
                pattern_width,
                world_height,
                world_width,
            )
            rule = get_rule(reward_type.rule_id)
            incubation_generations = calculate_incubation_generations(
                rule,
                complexity_score=float(
                    getattr(definition, "complexity_score", 0.0)
                ),
                bounding_area=pattern_height * pattern_width,
            )
            zone = EvolutionZone(
                pattern,
                start_row,
                start_col,
                rule,
                padding=reward_type.padding,
                base_color=reward_type.color,
                world_shape=state.shape,
                # Incubation is a fixed visual/evolution schedule. Stability
                # is still tracked, but no longer makes the zone jump to white
                # before its size/complexity-derived gradient is complete.
                min_generations=incubation_generations,
                max_generations=incubation_generations,
            )
            if any(zone.overlaps(existing, buffer=1) for existing in self.evolution_zones):
                continue
            r0, c0, r1, c1 = zone.reserved_rect
            state[r0:r1, c0:c1] = 0
            self.evolution_zones.append(zone)
            self.rewards.remove(reward)
            if hasattr(definition, "id"):
                self.selector.record_choice(reward_type.rule_id, definition)
                self._context_cache_key = None
            self.successful_rewards += 1
            return True
        return False

    def _calculate_seed_position(
        self,
        reward_position: tuple[int, int],
        direction: str | None,
        pattern_height: int,
        pattern_width: int,
        world_height: int,
        world_width: int,
    ) -> tuple[int, int]:
        offset_row, offset_col = self.direction_offsets.get(direction, (0, 0))
        if offset_row < 0:
            start_row = reward_position[0] + offset_row - pattern_height + 1
        elif offset_row > 0:
            start_row = reward_position[0] + offset_row
        else:
            start_row = reward_position[0] - pattern_height // 2
        if offset_col < 0:
            start_col = reward_position[1] + offset_col - pattern_width + 1
        elif offset_col > 0:
            start_col = reward_position[1] + offset_col
        else:
            start_col = reward_position[1] - pattern_width // 2
        return (
            max(0, min(start_row, world_height - pattern_height)),
            max(0, min(start_col, world_width - pattern_width)),
        )

    @staticmethod
    def _orient_pattern(pattern, direction: str | None) -> np.ndarray:
        cells = np.asarray(pattern, dtype=np.uint8)
        rotations = {
            "right": 3,
            "down-right": 3,
            "down": 2,
            "down-left": 2,
            "left": 1,
            "up-left": 1,
        }
        return np.rot90(cells, rotations.get(direction, 0)).copy()

    def _advance_evolution_zones(
        self,
        *,
        skip_zone: EvolutionZone | None = None,
    ) -> None:
        state = self._require_state()
        finished: list[EvolutionZone] = []
        for zone in self.evolution_zones:
            if zone is skip_zone:
                continue
            if not zone.step():
                continue
            for row, col in zone.commit_coordinates():
                if 0 <= row < state.shape[0] and 0 <= col < state.shape[1]:
                    state[row, col] = 1
            finished.append(zone)
        for zone in finished:
            self.evolution_zones.remove(zone)
        self.committed_this_update = any(
            zone.status == "mature" for zone in finished
        )

    def _require_state(self) -> np.ndarray:
        if self._current_state is None:
            raise RuntimeError("RewardManager.update must receive a state first")
        return self._current_state


def calculate_incubation_generations(
    rule: RuleSpec,
    *,
    complexity_score: float,
    bounding_area: int,
) -> int:
    """Map Pattern complexity and size onto the rule's incubation range."""
    normalized_complexity = min(100.0, max(0.0, float(complexity_score)))
    normalized_area = min(1.0, max(0, int(bounding_area)) / 400.0)
    incubation_ratio = min(
        0.30,
        0.20 * normalized_complexity / 100.0 + 0.10 * normalized_area,
    )
    return rule.min_generations + round(
        (rule.max_generations - rule.min_generations) * incubation_ratio
    )
