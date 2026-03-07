import timeit
import pandas as pd
import numpy as np
from logic import apply_context_modifiers

df = pd.DataFrame({'Glucose_Value': np.zeros(288)})

def run_benchmark():
    apply_context_modifiers(df.copy(), "Travel")

if __name__ == "__main__":
    time_taken = timeit.timeit(run_benchmark, number=10000)
    print(f"Time taken for 10000 iterations: {time_taken:.5f} seconds")
