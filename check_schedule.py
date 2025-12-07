import fastf1
import pandas as pd

fastf1.Cache.enable_cache('f1_cache')
schedule = fastf1.get_event_schedule(2025)
print(schedule[['RoundNumber', 'EventName', 'EventFormat']].to_string())
