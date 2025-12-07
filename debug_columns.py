import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_cache')

def inspect_columns():
    # Load one session
    session = fastf1.get_session(2025, 1, 'R')
    session.load(telemetry=False, weather=False, messages=False)
    print("Columns:", session.results.columns.tolist())
    print("First row:", session.results.iloc[0])

if __name__ == "__main__":
    inspect_columns()
