import json
import glob
import os

def patch_data_colors():
    # 1. Load fallbacks
    try:
        with open('fallback_teams.json', 'r') as f:
            fallbacks = json.load(f)
        print(f"Loaded {len(fallbacks)} fallback colors.")
    except Exception as e:
        print(f"Error loading fallbacks: {e}")
        return

    # 2. Iterate all data files
    files = glob.glob('data/standings_history_*.json')
    print(f"Found {len(files)} data files to patch.")

    total_patched = 0
    files_changed = 0

    for filepath in files:
        changed = False
        try:
            with open(filepath, 'r') as f:
                history = json.load(f)
            
            for step in history:
                for driver in step.get('standings', []):
                    # logic: if color is missing, try to find it in fallbacks
                    if not driver.get('color'):
                        team = driver.get('team')
                        if team and team in fallbacks:
                            driver['color'] = fallbacks[team]
                            changed = True
                            total_patched += 1
            
            if changed:
                with open(filepath, 'w') as f:
                    json.dump(history, f, indent=2)
                files_changed += 1
                
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    print(f"Done. Patched {total_patched} driver entries across {files_changed} files.")

if __name__ == "__main__":
    patch_data_colors()
