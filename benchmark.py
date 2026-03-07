import timeit
import numpy as np
import pandas as pd
from logic import apply_context_modifiers

# Create a sample DataFrame
np.random.seed(42)
df = pd.DataFrame({
    'Glucose_Value': np.random.normal(130, 10, 1000000), # 1 Million rows
    'Trend': ['Steady'] * 1000000
})

def run_benchmark():
    # Make a copy so we don't modify the original during benchmark iterations (though it shouldn't matter for speed here)
    apply_context_modifiers(df.copy(), "Travel")

if __name__ == "__main__":
    # Run benchmark
    num_runs = 20
    time_taken = timeit.timeit(run_benchmark, number=num_runs)
    print(f"Time taken for {num_runs} runs: {time_taken:.4f} seconds")
