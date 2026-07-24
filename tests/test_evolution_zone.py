import unittest

from src.core.rules import CONWAY_LIFE, RULES
from src.entities.evolution_zone import EvolutionZone, ZoneStatus


class EvolutionZoneTests(unittest.TestCase):
    def test_padding_and_world_coordinates(self):
        zone = EvolutionZone([[1]], 4, 5, CONWAY_LIFE, padding=2)
        self.assertEqual(zone.reserved_rect, (2, 3, 7, 8))
        self.assertEqual(tuple(zone.iter_world_cells()), ((4, 5),))

    def test_static_pattern_matures_after_three_recurrences(self):
        zone = EvolutionZone(
            [[1, 1], [1, 1]], 5, 5, "life", padding=2,
            min_generations=0, max_generations=20,
        )
        self.assertFalse(zone.step())
        self.assertFalse(zone.step())
        self.assertTrue(zone.step())
        self.assertEqual(zone.status, ZoneStatus.MATURE)
        self.assertEqual(zone.stable_period, 1)
        self.assertEqual(zone.finish_reason, "stable")

    def test_period_two_requires_three_complete_recurrences(self):
        zone = EvolutionZone(
            [[1, 1, 1]], 5, 5, "life", padding=3,
            min_generations=0, max_generations=20,
        )
        for _ in range(5):
            self.assertFalse(zone.step())
        self.assertTrue(zone.step())
        self.assertEqual(zone.stable_period, 2)

    def test_translation_normalization_detects_glider_period_four(self):
        zone = EvolutionZone(
            [[0, 1, 0], [0, 0, 1], [1, 1, 1]], 8, 8, "life", padding=6,
            min_generations=0, max_generations=30,
        )
        for _ in range(11):
            self.assertFalse(zone.step())
        self.assertTrue(zone.step())
        self.assertEqual(zone.stable_period, 4)

    def test_extinction_never_commits(self):
        zone = EvolutionZone(
            [[1]], 2, 2, "life", padding=1,
            min_generations=0, max_generations=10,
        )
        self.assertTrue(zone.step())
        self.assertTrue(zone.extinct)
        self.assertEqual(zone.commit_coordinates(), ())

    def test_hard_limit_commits_current_cells(self):
        zone = EvolutionZone(
            [[1, 1, 1]], 5, 5, "life", padding=3,
            min_generations=1, max_generations=1,
        )
        self.assertTrue(zone.step())
        self.assertEqual(zone.finish_reason, "max_generations")
        self.assertTrue(zone.commit_coordinates())

    def test_overlap_includes_requested_buffer(self):
        first = EvolutionZone([[1, 1]], 2, 2, "life", padding=0)
        second = EvolutionZone([[1]], 2, 5, "life", padding=0)
        self.assertFalse(first.overlaps(second, buffer=1))
        adjacent = EvolutionZone([[1]], 2, 4, "life", padding=0)
        self.assertTrue(first.overlaps(adjacent, buffer=1))

    def test_all_rule_colors_interpolate_from_base_to_white(self):
        for rule in RULES.values():
            with self.subTest(rule=rule.id):
                zone = EvolutionZone(
                    [[1, 1], [1, 1]],
                    2,
                    2,
                    rule,
                    padding=1,
                    min_generations=10,
                    max_generations=10,
                )
                self.assertEqual(zone.get_color(), rule.color)
                zone.current_step = 5
                self.assertEqual(
                    zone.get_color(),
                    tuple(
                        int(round(channel + (255 - channel) * 0.5))
                        for channel in rule.color
                    ),
                )
                zone.current_step = 10
                self.assertEqual(zone.get_color(), (255, 255, 255))

    def test_stability_tracking_does_not_extend_incubation(self):
        zone = EvolutionZone(
            [[1, 1], [1, 1]],
            5,
            5,
            "life",
            padding=2,
            min_generations=12,
            max_generations=12,
        )
        for _ in range(11):
            self.assertFalse(zone.step())
        self.assertTrue(zone.step())
        self.assertEqual(zone.current_step, 12)
        self.assertEqual(zone.finish_reason, "stable")


if __name__ == "__main__":
    unittest.main()
