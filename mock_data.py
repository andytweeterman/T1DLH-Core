import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_mock_cgm():
    """
    Generates mock CGM (Continuous Glucose Monitor) data.
    Returns a DataFrame with 'glucose' and 'trend' columns.
    """
    # Create a time index for the last hour, every 5 minutes
    dates = [datetime.now() - timedelta(minutes=5*i) for i in range(12)]
    dates.reverse()

    # Mock data
    data = {
        'glucose': [100, 102, 105, 108, 110, 112, 115, 118, 120, 122, 125, 128],
        'trend': ['Flat'] * 12
    }

    df = pd.DataFrame(data, index=dates)

    return df
