import timeit
import pandas as pd
import numpy as np

def setup_data(n=10000):
    df = pd.DataFrame({'diff': np.random.uniform(-20, 20, n)})
    return df

def original_apply(df):
    def get_trend(change):
        if change > 15:
            return 'DoubleUp'
        elif 10 < change <= 15:
            return 'SingleUp'
        elif 5 < change <= 10:
            return 'FortyFiveUp'
        elif -5 <= change <= 5:
            return 'Flat'
        elif -10 <= change < -5:
            return 'FortyFiveDown'
        elif -15 <= change < -10:
            return 'SingleDown'
        else: # change < -15
            return 'DoubleDown'
    return df['diff'].apply(get_trend)

def optimized_select(df):
    conditions = [
        df['diff'] > 15,
        (df['diff'] > 10) & (df['diff'] <= 15),
        (df['diff'] > 5) & (df['diff'] <= 10),
        (df['diff'] >= -5) & (df['diff'] <= 5),
        (df['diff'] >= -10) & (df['diff'] < -5),
        (df['diff'] >= -15) & (df['diff'] < -10)
    ]
    choices = [
        'DoubleUp',
        'SingleUp',
        'FortyFiveUp',
        'Flat',
        'FortyFiveDown',
        'SingleDown'
    ]
    return np.select(conditions, choices, default='DoubleDown')

if __name__ == '__main__':
    df = setup_data(100000)

    # check correctness
    assert (original_apply(df) == optimized_select(df)).all()

    n_iter = 100
    t1 = timeit.timeit(lambda: original_apply(df), number=n_iter)
    t2 = timeit.timeit(lambda: optimized_select(df), number=n_iter)

    print(f"Original apply: {t1:.4f} seconds")
    print(f"Optimized select: {t2:.4f} seconds")
    print(f"Speedup: {t1/t2:.2f}x")
