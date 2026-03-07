import timeit
import pandas as pd
import numpy as np
import logic

def run_benchmark_unoptimized():
    df = pd.DataFrame({'Glucose_Value': np.zeros(288)})
    spikes = np.zeros(len(df))
    indices = np.random.choice(range(len(df)), size=3, replace=False)
    for idx in indices:
        x = np.arange(len(df))
        spikes += 60 * np.exp(-0.5 * ((x - idx) / 6)**2)

def run_benchmark_optimized():
    df = pd.DataFrame({'Glucose_Value': np.zeros(288)})
    spikes = np.zeros(len(df))
    indices = np.random.choice(range(len(df)), size=3, replace=False)
    x = np.arange(len(df))
    for idx in indices:
        spikes += 60 * np.exp(-0.5 * ((x - idx) / 6)**2)

if __name__ == "__main__":
    time_unoptimized = timeit.timeit(run_benchmark_unoptimized, number=100000)
    print(f"Time taken for 100000 unoptimized iterations: {time_unoptimized:.5f} seconds")

    time_optimized = timeit.timeit(run_benchmark_optimized, number=100000)
    print(f"Time taken for 100000 optimized iterations: {time_optimized:.5f} seconds")
