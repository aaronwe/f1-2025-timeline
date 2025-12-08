import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_cache')
session = fastf1.get_session(2020, 1, 'R')
session.load(telemetry=False, weather=False, messages=False)

print("Columns:", session.results.columns)
if 'TeamColor' in session.results.columns:
    print("\nSample Colors:")
    print(session.results[['TeamName', 'TeamColor']].head().to_string())
