import timeit
import numpy as np
import pandas as pd

def orig_trend(df):
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

def opt_trend(df):
    conditions = [
        df['diff'] > 15,
        (df['diff'] > 10) & (df['diff'] <= 15),
        (df['diff'] > 5) & (df['diff'] <= 10),
        (df['diff'] >= -5) & (df['diff'] <= 5),
        (df['diff'] >= -10) & (df['diff'] < -5),
        (df['diff'] >= -15) & (df['diff'] < -10)
    ]
    choices = [
        'DoubleUp', 'SingleUp', 'FortyFiveUp', 'Flat', 'FortyFiveDown', 'SingleDown'
    ]
    return np.select(conditions, choices, default='DoubleDown')

if __name__ == "__main__":
    df = pd.DataFrame({'diff': np.random.randint(-20, 20, 10000)})

    t_orig = timeit.timeit(lambda: orig_trend(df), number=100)
    t_opt = timeit.timeit(lambda: opt_trend(df), number=100)
    print(f"Original trend: {t_orig:.4f}s")
    print(f"Optimized trend: {t_opt:.4f}s")
