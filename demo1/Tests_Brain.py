import unittest
import os

from src.environment import Environment
from src.genetic_algorithm import GeneticAlgorithm
from src.brain import Brain
from train import Trainer


class TestTrainer(unittest.TestCase):

    def test_trainer_results_dir_exists(self):
        """Проверка создания директории results."""
        trainer = Trainer()
        self.assertTrue(os.path.exists(trainer.results_dir))

    def test_trainer_best_fitness_is_minus_inf(self):
        """Проверка начального значения best_fitness."""
        trainer = Trainer()
        self.assertEqual(trainer.best_fitness, float('-inf'))

    def test_trainer_genome_length(self):
        """Проверка genome_length."""
        trainer = Trainer()
        self.assertEqual(trainer.ga.genome_length, 180)


if __name__ == '__main__':
    unittest.main()