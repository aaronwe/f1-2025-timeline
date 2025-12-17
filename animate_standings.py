import pandas as pd
import bar_chart_race as bcr
import json
import matplotlib.pyplot as plt
import warnings

"""
animate_standings.py

Generates an MP4 animation of the Formula 1 Championship standings for a given year.
- Reads JSON data from `data/standings_history_{year}.json`.
- Uses `bar_chart_race` to visualize points progression.
- Applies team colors (from data or fallback map) and custom styling.
- Outputs video to `animations/`.
"""

# Suppress FutureWarning from bar_chart_race regarding fillna(method='ffill')
warnings.simplefilter(action='ignore', category=FutureWarning)

import matplotlib.font_manager as fm

import argparse
import sys

def animate(year):
    # 1. Load Data
    filename = f'data/standings_history_{year}.json'
    try:
        with open(filename, 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        print(f"{filename} not found. Run prepare_web_data.py --year {year} first.")
        return

    print(f"Loaded {len(history)} steps from history for {year}.")

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
    period_labels = [f"Season Start\n{year}"]
    
    # We need to map driver names to their teams/colors
    driver_team_map = {} # Name -> Team
    driver_color_map = {} # Name -> HexColor

    # Track last row for the "pause/label switch" step
    last_row = step0_row

    for i, step in enumerate(history):
        # Create a label for this step: "Event Name - Session\nDate | Location"
        label = f"{step['eventName']} | {step['session']}\n{step['date']} | {step['location']}"
        
        # 1. Add "Pre-Animation" Step:
        # Show the NEW label, but keep the OLD points.
        # This allows the viewer to see "Race X" before the bars start moving.
        period_labels.append(label)
        data_rows.append(last_row)
        
        # 2. Add "Animation" Step:
        # Show the NEW label and NEW points.
        period_labels.append(label)
        
        row = {driver: 0 for driver in sorted_drivers}
        for driver_data in step['standings']:
            name = driver_data['name']
            points = driver_data['points']
            
            # [FIX] 1997 Exception: Michael Schumacher DSQ
            # Force points to 0 in the final step so he strictly "falls off" the chart
            if year == 1997 and name == "Michael Schumacher" and i == len(history) - 1:
                points = 0
            
            row[name] = points
            
            # Update maps
            driver_team_map[name] = driver_data['team']
            # Use color from JSON if available
            if 'color' in driver_data and driver_data['color']:
                 driver_color_map[name] = driver_data['color']
            
        data_rows.append(row)
        last_row = row

    # Explicitly set columns to ensure order matches color list
    df = pd.DataFrame(data_rows, index=period_labels, columns=sorted_drivers)

    # [NEW] Rename columns to include Team Name (e.g. "Name\nTEAM")
    # This displays the team under the driver name on the Y-axis
    rename_map = {}
    for driver in sorted_drivers:
        team = driver_team_map.get(driver, "").upper()
        rename_map[driver] = f"{driver}\n{team}"
    
    df.rename(columns=rename_map, inplace=True)
    
    # 3. Define Colors
    # Fallback Map (for years where API provides no color, or gaps)
    # Includes 2024/2025 teams plus historical ones.
    # Load Fallback Colors
    try:
        with open('fallback_teams.json', 'r') as f:
            fallback_team_colors = json.load(f)
    except FileNotFoundError:
        print("fallback_teams.json not found. Using empty fallback.")
        fallback_team_colors = {}

    # Build color list aligned with sorted_drivers
    bar_colors = []
    for driver in sorted_drivers:
        # Priority 1: Color from JSON (API)
        color = driver_color_map.get(driver)
        
        # If API returns grey #555555, treat it as missing to use fallback
        if color == "#555555":
            color = None
        
        # Priority 2: Fallback map based on Team Name
        if not color:
            team = driver_team_map.get(driver, "Unknown")
            color = fallback_team_colors.get(team)
            if color:
                 pass # print(f"Using fallback color {color} for {driver} ({team})")
        
        # Priority 3: Grey
        if not color:
            color = "#555555"
            
        bar_colors.append(color)

    print("Generating animation (1920x1080)... this will take a moment.")
    
    # 4. Generate Animation
    # Set global dark mode style (handles ticks, spines, etc.)
    plt.style.use('dark_background')
    
    # [FIX] Full HD 1920x1080
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor='black')
    
    # Add axes with explicit margins (Adjusted for 16:9)
    # Add axes with explicit margins (Adjusted for 16:9)
    # Left margin needs to be wide enough for "Long Name + Team"
    # [FIX] Reduced height from 0.83 to 0.78 to make room at the top
    ax = fig.add_axes([0.15, 0.05, 0.80, 0.78], facecolor='black')
    
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
    # [FIX] Moved up to 0.95 and aligned right to 0.15 to match chart margin
    fig.suptitle(f'F1 {year} Championship Standings', fontsize=36, fontweight='bold', y=0.95, x=0.15, ha='left', fontfamily='Outfit', color='white')
    
    # Ensure output directory exists
    import os
    if not os.path.exists('animations'):
        os.makedirs('animations')
    
    output_filename = f'animations/f1_{year}_standings.mp4'
    
    bcr.bar_chart_race(
        df=df,
        filename=output_filename,
        orientation='h',
        sort='desc',
        n_bars=10,
        fixed_order=False,
        fixed_max=True, 
        steps_per_period=20, 
        period_length=750, # 0.75s animation
        end_period_pause=100, # 0.1s pause between steps
        interpolate_period=False, 
        bar_size=.70, # Thinner bars (0.7)
        # Position metadata (Race Name)
        # [FIX] Position label lower (1.00 instead of 1.02)
        period_label={'x': 0.0, 'y': 1.00, 'ha': 'left', 'va': 'bottom', 'size': 18, 'weight': 'bold', 'family': 'Outfit', 'color': 'white'}, 
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
    
    print(f"Animation saved to {output_filename}")

if __name__ == "__main__":
    import datetime
    current_year = datetime.datetime.now().year

    parser = argparse.ArgumentParser(description="Animate F1 standings")
    parser.add_argument("--year", type=int, default=current_year, help=f"Season year to animate (default: {current_year})")
    args = parser.parse_args()
    
    animate(args.year)
