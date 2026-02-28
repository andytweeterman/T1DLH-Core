import timeit
import numpy as np

def original():
    num_points = 288
    glucose_values = []
    current_value = np.random.randint(90, 150)
    glucose_values.append(current_value)
    current_trend_val = 0

    for _ in range(num_points - 1):
        trend_delta = np.random.randint(-2, 3)
        current_trend_val += trend_delta
        if abs(current_trend_val) > 8:
            current_trend_val = int(current_trend_val * 0.8)
        noise = np.random.randint(-2, 3)
        change = current_trend_val + noise
        current_value += change
        if current_value < 70:
            current_value = 70
            current_trend_val = abs(current_trend_val) // 2 + 1
        elif current_value > 220:
            current_value = 220
            current_trend_val = -(abs(current_trend_val) // 2 + 1)
        glucose_values.append(current_value)
    return glucose_values

def optimized():
    num_points = 288
    glucose_values = np.zeros(num_points, dtype=int)
    glucose_values[0] = np.random.randint(90, 150)

    current_value = glucose_values[0]
    current_trend_val = 0

    trend_deltas = np.random.randint(-2, 3, size=num_points - 1)
    noises = np.random.randint(-2, 3, size=num_points - 1)

    for i in range(num_points - 1):
        current_trend_val += trend_deltas[i]

        if abs(current_trend_val) > 8:
            current_trend_val = int(current_trend_val * 0.8)

        current_value += current_trend_val + noises[i]

        if current_value < 70:
            current_value = 70
            current_trend_val = abs(current_trend_val) // 2 + 1
        elif current_value > 220:
            current_value = 220
            current_trend_val = -(abs(current_trend_val) // 2 + 1)

        glucose_values[i + 1] = current_value
    return glucose_values

if __name__ == "__main__":
    t_orig = timeit.timeit(original, number=1000)
    t_opt = timeit.timeit(optimized, number=1000)
    print(f"Original: {t_orig:.4f}s")
    print(f"Optimized: {t_opt:.4f}s")
