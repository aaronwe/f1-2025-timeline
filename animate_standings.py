import pandas as pd
import bar_chart_race as bcr
import json
import matplotlib.pyplot as plt

import matplotlib.font_manager as fm

def animate():
    # 1. Load Data
    try:
        with open('standings_history.json', 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        print("standings_history.json not found. Run prepare_web_data.py first.")
        return

    print(f"Loaded {len(history)} steps from history.")

    # Register Custom Google Fonts
    try:
        fm.fontManager.addfont('fonts/Outfit-Regular.ttf')
        fm.fontManager.addfont('fonts/Outfit-Bold.ttf')
        print("Custom font 'Outfit' loaded successfully.")
    except Exception as e:
        print(f"Error loading custom fonts: {e}")

    # 2. Process into DataFrame for bar_chart_race
    # Structure: Index = Time Steps, Columns = Drivers, Values = Points
    
    # Collect all unique driver names first
    all_drivers = set()
    for step in history:
        for driver in step['standings']:
            all_drivers.add(driver['name'])
    
    sorted_drivers = sorted(list(all_drivers))
    
    # Build data rows
    # Initialize with Step 0 (Season Start)
    # To prevent visual jumping, we seed Step 0 with "epsilon points" 
    # based on the first race (Step 1) results. This pre-sorts the bars.
    step0_row = {}
    
    # Get Step 1 points (first entry in history)
    if len(history) > 0:
        step1_standings = {d['name']: d['points'] for d in history[0]['standings']}
    else:
        step1_standings = {}

    for driver in sorted_drivers:
        p1 = step1_standings.get(driver, 0)
        # Use a tiny fraction so it sorts correctly but displays as 0 (due to integer formatting)
        step0_row[driver] = p1 * 0.0001
        
    data_rows = [step0_row]
    period_labels = ["Season Start\n2025"]
    
    # We need to map driver names to their teams for coloring
    driver_team_map = {}

    for step in history:
        # Create a label for this step: "Event Name - Session\nDate | Location"
        label = f"{step['eventName']} | {step['session']}\n{step['date']} | {step['location']}"
        period_labels.append(label)
        
        row = {driver: 0 for driver in sorted_drivers}
        for driver_data in step['standings']:
            name = driver_data['name']
            points = driver_data['points']
            row[name] = points
            
            # Update team map (latest team takes precedence if they transfer, unlikely but safe)
            driver_team_map[name] = driver_data['team']
            
        data_rows.append(row)

    # Explicitly set columns to ensure order matches color list
    df = pd.DataFrame(data_rows, index=period_labels, columns=sorted_drivers)
    
    # 3. Define Colors
    # Map from style.css
    team_colors = {
        "Red Bull Racing": "#3671C6",
        "Ferrari": "#F91536",
        "Mercedes": "#6CD3BF",
        "McLaren": "#F58020",
        "Aston Martin": "#358C75",
        "Alpine": "#2293D1",
        "Williams": "#37BEDD",
        "Haas F1 Team": "#B6BABD",
        "Kick Sauber": "#52E252",
        "RB": "#6692FF",
        "Racing Bulls": "#6692FF" # Alias found in json
    }
    
    # Create color list aligned with sorted_drivers
    # We use a LIST because dict support is broken in this version's get_bar_colors validation
    bar_colors = []
    for driver in sorted_drivers:
        team = driver_team_map.get(driver, "Unknown")
        color = team_colors.get(team, "#555555") # Fallback grey
        bar_colors.append(color)

    print("Generating animation (1080x1080)... this will take a moment.")

    # 4. Generate Animation
    # Set global dark mode style (handles ticks, spines, etc.)
    plt.style.use('dark_background')

    # Manually create figure to control layout margins (prevent title overlap)
    fig = plt.figure(figsize=(10.8, 10.8), dpi=100, facecolor='black')
    
    # Add axes with explicit margins
    ax = fig.add_axes([0.15, 0.05, 0.80, 0.77], facecolor='black')
    
    # Hide X-axis ticks and labels (clean look)
    ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    # Hide Y-axis ticks but keep labels
    ax.tick_params(axis='y', which='both', left=False, right=False)
    # Hide axis spines (lines)
    for spine in ax.spines.values():
        spine.set_visible(False)
        
    # Force X-Axis scale to be fixed
    max_points = df.max().max()
    # Increase buffer to 15% to prevent cutting off labels (e.g. 408)
    ax.set_xlim(0, max_points * 1.15) 
    
    # Add Static Title manually
    # Switched to Outfit Bold (Loaded from fonts/)
    # Align Title with the Axes Left Edge (x=0.15)
    fig.suptitle('F1 2025 Championship Standings', fontsize=36, fontweight='bold', y=0.95, x=0.15, ha='left', fontfamily='Outfit', color='white')
    
    bcr.bar_chart_race(
        df=df,
        filename='f1_2025_standings.mp4',
        orientation='h',
        sort='desc',
        n_bars=10,
        fixed_order=False,
        fixed_max=True, 
        steps_per_period=20, 
        period_length=750, # 0.75s animation
        end_period_pause=250, # 0.25s pause between steps
        interpolate_period=False, 
        bar_size=.70, # Thinner bars (0.7)
        # Position metadata (Race Name)
        period_label={'x': 0.0, 'y': 1.02, 'ha': 'left', 'va': 'bottom', 'size': 18, 'weight': 'bold', 'family': 'Outfit', 'color': 'white'}, 
        period_template='{x}', 
        colors=bar_colors, 
        filter_column_colors=False, 
        title=None, 
        bar_label_font=18, # Larger point values
        # Explicitly set font family and color for driver names
        tick_label_font={'size': 18, 'family': 'Outfit', 'color': 'white'}, 
        # Shared font dict for bar labels
        shared_fontdict={'family': 'Outfit', 'weight': 'normal', 'color': 'white'},
        scale='linear',
        writer='ffmpeg',
        fig=fig, 
        # White edges for bars
        bar_kwargs={'alpha': .9, 'ec': 'whitesmoke', 'lw': 1} 
    )
    
    print("Animation saved to f1_2025_standings.mp4")

if __name__ == "__main__":
    animate()
