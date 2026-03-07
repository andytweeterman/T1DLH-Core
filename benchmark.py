import timeit
import pandas as pd
import numpy as np
from logic import apply_context_modifiers, fetch_health_data

# Create a sample dataframe
df = fetch_health_data()

# Measure the execution time of apply_context_modifiers(df, "Travel")
def run_benchmark():
    apply_context_modifiers(df, "Travel")

if __name__ == "__main__":
    n = 10000
    time_taken = timeit.timeit(run_benchmark, number=n)
    print(f"Time taken for {n} iterations: {time_taken:.4f} seconds")
