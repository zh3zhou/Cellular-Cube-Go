import unittest

import numpy as np

from src.core.rules import CONWAY_LIFE, DAY_AND_NIGHT, HIGHLIFE, SEEDS, get_rule


def _trim(state):
    rows, cols = np.nonzero(state)
    return state[rows.min() : rows.max() + 1, cols.min() : cols.max() + 1]


class RuleSpecTests(unittest.TestCase):
    def test_life_blinker(self):
        state = np.array([[0, 0, 0], [1, 1, 1], [0, 0, 0]], dtype=np.uint8)
        expected = np.array([[0, 1, 0], [0, 1, 0], [0, 1, 0]], dtype=np.uint8)
        np.testing.assert_array_equal(CONWAY_LIFE.evolve(state), expected)

    def test_rule_specific_birth_and_survival(self):
        self.assertEqual(HIGHLIFE.apply(0, 6), 1)
        self.assertEqual(CONWAY_LIFE.apply(0, 6), 0)
        self.assertEqual(SEEDS.apply(0, 2), 1)
        self.assertEqual(SEEDS.apply(1, 2), 0)
        self.assertEqual(DAY_AND_NIGHT.apply(0, 8), 1)
        self.assertEqual(DAY_AND_NIGHT.apply(1, 5), 0)

    def test_highlife_replicator_after_twelve_generations(self):
        state = np.zeros((25, 25), dtype=np.uint8)
        state[10:15, 10:15] = np.array(
            [
                [0, 0, 1, 1, 1],
                [0, 1, 0, 0, 1],
                [1, 0, 0, 0, 1],
                [1, 0, 0, 1, 0],
                [1, 1, 1, 0, 0],
            ],
            dtype=np.uint8,
        )
        for _ in range(12):
            state = HIGHLIFE.evolve(state)
        expected = np.array(
            [
                [0, 0, 1, 1, 1, 0, 0, 0, 0],
                [0, 1, 0, 0, 1, 0, 0, 0, 0],
                [1, 0, 0, 0, 1, 0, 0, 0, 0],
                [1, 0, 0, 1, 0, 0, 0, 0, 0],
                [1, 1, 1, 0, 0, 0, 1, 1, 1],
                [0, 0, 0, 0, 0, 1, 0, 0, 1],
                [0, 0, 0, 0, 1, 0, 0, 0, 1],
                [0, 0, 0, 0, 1, 0, 0, 1, 0],
                [0, 0, 0, 0, 1, 1, 1, 0, 0],
            ],
            dtype=np.uint8,
        )
        np.testing.assert_array_equal(_trim(state), expected)

    def test_seeds_domino_first_generation(self):
        state = np.zeros((5, 4), dtype=np.uint8)
        state[2, 1:3] = 1
        expected = np.array([[1, 1], [0, 0], [1, 1]], dtype=np.uint8)
        np.testing.assert_array_equal(_trim(SEEDS.evolve(state)), expected)

    def test_day_and_night_full_square_first_generation(self):
        state = np.zeros((7, 7), dtype=np.uint8)
        state[2:5, 2:5] = 1
        expected = np.array(
            [
                [0, 0, 1, 0, 0],
                [0, 1, 0, 1, 0],
                [1, 0, 1, 0, 1],
                [0, 1, 0, 1, 0],
                [0, 0, 1, 0, 0],
            ],
            dtype=np.uint8,
        )
        np.testing.assert_array_equal(_trim(DAY_AND_NIGHT.evolve(state)), expected)

    def test_edges_do_not_wrap(self):
        state = np.zeros((3, 3), dtype=np.uint8)
        state[0, 0] = state[0, 2] = state[2, 0] = 1
        self.assertEqual(int(CONWAY_LIFE.evolve(state)[2, 2]), 0)

    def test_registry_accepts_ids_aliases_and_rulestrings(self):
        self.assertIs(get_rule("life"), CONWAY_LIFE)
        self.assertIs(get_rule("B36/S23"), HIGHLIFE)
        self.assertIs(get_rule("daynight"), DAY_AND_NIGHT)


if __name__ == "__main__":
    unittest.main()
