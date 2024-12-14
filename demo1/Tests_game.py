import unittest
import os
from src.environment import Environment
from src.genetic_algorithm import GeneticAlgorithm
from src.brain import Brain
from src.game import Game
from train import Trainer  # Предполагаем, что класс Trainer находится в файле trainer.py


class TestTrainer(unittest.TestCase):

    def test_trainer_initialization(self):
        """Тестируем правильную инициализацию тренера."""
        trainer = Trainer()
        self.assertIsNotNone(trainer.env, "Environment должно быть инициализировано.")
        self.assertIsNotNone(trainer.ga, "GeneticAlgorithm должно быть инициализировано.")
        self.assertEqual(trainer.best_fitness, float('-inf'), "Начальный best_fitness должен быть -inf.")
        self.assertTrue(os.path.exists(trainer.results_dir), "Директория для результатов должна существовать.")

    def test_evaluate_genome(self):
        """Тестируем функцию оценки генома."""
        trainer = Trainer()
        genome = [0.1] * 180  # Пример генома
        fitness = trainer.evaluate_genome(genome)
        self.assertIsInstance(fitness, float, "Fitness должен быть float.")
        self.assertGreaterEqual(fitness, 0, "Fitness должен быть неотрицательным.")

    def test_save_genome(self):
        """Тестируем функцию сохранения генома."""
        trainer = Trainer()
        genome = [0.1] * 180  # Пример генома
        generation = 1
        fitness = 10.5
        trainer.save_genome(genome, generation, fitness)
        filename = f"{trainer.results_dir}/genome_gen_{generation}_fit_{fitness:.2f}.txt"
        self.assertTrue(os.path.exists(filename), f"Файл {filename} должен быть создан.")
        with open(filename, 'r') as file:
            saved_genome = file.read()
            self.assertEqual(saved_genome, ','.join(map(str, genome)), "Сохранённый геном должен совпадать с входным.")

if __name__ == '__main__':
    unittest.main()