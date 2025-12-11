import fastf1
from fastf1.ergast import Ergast

def check_1988_standings():
    ergast = Ergast()
    
    print("Fetching 1988 Final Standings (Round 16)...")
    # 1988 had 16 rounds
    standings = ergast.get_driver_standings(season=1988, round=16)
    
    print(f"Type of content: {type(standings.content)}")
    if standings.content:
        df = standings.content[0]
        print(f"Type of first element: {type(df)}")
        print(df.head())
        print(df.columns)
        
        # Iterate over DataFrame
        print("\n--- Official Standings 1988 ---")
        for idx, row in df.iterrows():
             driver = row['givenName'] + " " + row['familyName']
             points = row['points']
             wins = row['wins']
             print(f"{driver}: {points} (Wins: {wins})")
             if idx >= 4: break
        
    print("\nComparing with manual sum from Race Results...")
    # Get all race results and sum them
    schedule = fastf1.get_event_schedule(1988)
    manual_points = {}
    
    for i, row in schedule.iterrows():
        rn = row['RoundNumber']
        session = fastf1.get_session(1988, rn, 'R')
        session.load(telemetry=False, weather=False, messages=False)
        
        for _, race_res in session.results.iterrows():
            d_id = race_res['DriverId'] # or name
            p = race_res['Points']
            
            # Name mapping might be tricky, let's just use LastName or something
            name = race_res['LastName']
            full_name = race_res['FirstName'] + " " + name
            
            manual_points[full_name] = manual_points.get(full_name, 0) + p
            
    print("\n--- Manual Sum 1988 ---")
    # Sort
    sorted_manual = sorted(manual_points.items(), key=lambda x: x[1], reverse=True)
    for name, pts in sorted_manual[:5]:
        print(f"{name}: {pts}")

if __name__ == "__main__":
    check_1988_standings()
