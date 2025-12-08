import json
import glob
import os

def analyze_teams():
    files = glob.glob('data/standings_history_*.json')
    all_teams = set()
    missing_color_teams = set()
    
    print(f"Scanning {len(files)} files...")
    
    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                history = json.load(f)
                
            for step in history:
                for driver in step.get('standings', []):
                    team = driver.get('team')
                    color = driver.get('color')
                    
                    if team:
                        all_teams.add(team)
                        if not color:
                            missing_color_teams.add(team)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    print(f"\nTotal unique teams found: {len(all_teams)}")
    print(f"Teams missing colors: {len(missing_color_teams)}")
    
    print("\n--- Teams Missing Colors ---")
    for team in sorted(missing_color_teams):
        print(team)

if __name__ == "__main__":
    analyze_teams()
