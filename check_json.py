import json

try:
    with open('standings_history.json') as f:
        data = json.load(f)
        
    sprint_count = 0
    race_count = 0
    
    print(f"Total steps: {len(data)}")
    
    for step in data:
        if step['session'] == 'Sprint':
            sprint_count += 1
            print(f"Found Sprint: {step['eventName']}")
        elif step['session'] == 'Race':
            race_count += 1
            
    print(f"Sprints found: {sprint_count}")
    print(f"Races found: {race_count}")
        
except Exception as e:
    print(e)
