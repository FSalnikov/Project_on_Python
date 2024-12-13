from typing import List, Dict
import math

class Brain:
    def __init__(self, genome: List[int]):
        """
        Инициализация мозга с геномом
        genome: список из 180 битов (0 или 1)
        """
        if len(genome) != 180:
            raise ValueError("Genome must be 180 bits long")
        
        self.genome = genome
        self.engine_coefficients = self._bits_to_coefficients(genome[:90])
        self.wheel_coefficients = self._bits_to_coefficients(genome[90:])

    def _bits_to_coefficients(self, bits: List[int]) -> List[float]:
        """
        Преобразование битов в коэффициенты
        Каждые 10 бит -> 1 коэффициент
        """
        coefficients = []
        for i in range(0, len(bits), 10):
            coef_bits = bits[i:i+10]
            value = self._binary_to_float(coef_bits)
            coefficients.append(value)
        return coefficients

    def _binary_to_float(self, bits: List[int]) -> float:
        """
        Преобразование 10 бит в число с плавающей точкой
        1 бит знака + 4 бита экспоненты + 5 битов мантиссы
        """
        if len(bits) != 10:
            raise ValueError("Expected 10 bits")

        # Знак (1 бит)
        sign = -1 if bits[0] else 1

        # Экспонента (4 бита)
        exponent_bits = bits[1:5]
        exponent = sum(bit * (2 ** i) for i, bit in enumerate(reversed(exponent_bits)))
        exponent = exponent - 7  # Смещение для отрицательных значений

        # Мантисса (5 битов)
        mantissa_bits = bits[5:]
        mantissa = sum(bit * (2 ** -(i + 1)) for i, bit in enumerate(mantissa_bits))

        # Итоговое значение с ограничением
        result = sign * (1 + mantissa) * (2 ** exponent)
        # Ограничиваем результат для предотвращения переполнения
        return max(min(result, 100), -100)

    def make_decision(self, sensors: List[float]) -> Dict[str, int]:
        """
        Принятие решения на основе данных с сенсоров
        """
        if len(sensors) != 8:
            raise ValueError("Expected 8 sensor values")

        # Нормализация входных данных
        sensors = [max(min(s, 100), 0) for s in sensors]

        # Вычисление сигнала для двигателя
        engine_signal = sum(c * s for c, s in zip(self.engine_coefficients[:-1], sensors))
        engine_signal += self.engine_coefficients[-1]  # Добавление смещения

        # Вычисление сигнала для руля
        wheel_signal = sum(c * s for c, s in zip(self.wheel_coefficients[:-1], sensors))
        wheel_signal += self.wheel_coefficients[-1]  # Добавление смещения

        # Ограничение сигналов
        engine_signal = max(min(engine_signal, 100), -100)
        wheel_signal = max(min(wheel_signal, 100), -100)

        return {
            'engine': self._signal_to_action(engine_signal),
            'wheels': self._signal_to_action(wheel_signal)
        }

    def _signal_to_action(self, signal: float) -> int:
        """
        Преобразование сигнала в действие (-1, 0, 1)
        Использует сигмоидоподобную функцию с порогами
        """
        try:
            # Ограничиваем сигнал для предотвращения переполнения
            signal = max(min(signal, 500), -500)
            normalized = 1 / (1 + math.exp(-signal))
        except (OverflowError, ValueError):
            # В случае ошибки используем пороговое значение
            normalized = 1.0 if signal > 0 else 0.0
        
        # Преобразование в действие
        if normalized < 0.33:
            return -1
        elif normalized > 0.66:
            return 1
        return 0

    def get_coefficients(self) -> Dict[str, List[float]]:
        """
        Получение текущих коэффициентов для отладки
        """
        return {
            'engine': self.engine_coefficients,
            'wheels': self.wheel_coefficients
        }

    def get_genome(self) -> List[int]:
        """
        Получение генома
        """
        return self.genome