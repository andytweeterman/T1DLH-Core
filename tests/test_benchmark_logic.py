import pytest
import pandas as pd
import numpy as np
from logic import apply_context_modifiers

def test_benchmark_apply_context_modifiers_travel(benchmark):
    # Setup dataframe with a large size to show performance impact clearly
    df = pd.DataFrame({
        'Glucose_Value': np.random.normal(100, 10, 1000000),
        'Trend': 'Steady'
    })

    # Run benchmark
    result = benchmark(apply_context_modifiers, df.copy(), "Travel")

    # Assert
    assert result is not None
