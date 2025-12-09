import json
import glob
import os

"""
build_fallbacks.py

Constructs the `fallback_teams.json` map.
- Scans all `data/standings_history_*.json` files for unique team names.
- Matches names against a hardcoded `HISTORICAL_COLORS` source of truth.
- Normalizes names to handle variations (e.g., "Lotus-Climax" -> "Lotus").
- assigns specific colors or defaults to keep the animation script robust for all eras.
"""

# Base historical colors
HISTORICAL_COLORS = {
    # Modern & recent
    "Mercedes": "#00D2BE",
    "Ferrari": "#DC0000",
    "Red Bull": "#0600EF",
    "McLaren": "#FF8700",
    "Alpine": "#0090FF",
    "Aston Martin": "#006F62", 
    "Sauber": "#006EFF",
    "Haas": "#FFFFFF",
    "Williams": "#005AFF",
    "RB": "#6692FF",
    
    # 2000s - 2010s
    "Renault": "#FFF500",
    "Toyota": "#E10600",
    "BMW": "#0066B1", # BMW Blue
    "BMW Sauber": "#000066", # BMW Dark Blue (Sauber years)
    "Honda": "#C5C5C5",
    "Brawn": "#B8FD6E",
    "Brawn GP": "#B8FD6E",
    "Super Aguri": "#D63838",
    "Spyker": "#F27E1C",
    "Midland": "#808080",
    "Toro Rosso": "#0000FF",
    "Force India": "#F596C8",
    "Racing Point": "#F596C8",
    "Marussia": "#6E0000",
    "Manor": "#D32F2F",
    "Caterham": "#006400",
    "HRT": "#A4660E",
    "Virgin": "#D91E18",
    "Jaguar": "#005A32",
    "Stewart": "#0B2161", # Stewart Tartan Blue
    "Prost": "#00009C",
    "Arrows": "#F27E1C",
    "Benetton": "#79C5E4",
    "Minardi": "#505050",
    "BAR": "#E0E0E0",
    "Jordan": "#E7C513",

    # 1980s - 1990s
    "Lotus": "#004225", # Lotus Green
    "Team Lotus": "#004225",
    "Tyrrell": "#0000FF",
    "Ligier": "#005FBF",
    "Brabham": "#191970",
    "March": "#FFA500",
    "Lola": "#FF4500",
    "Larrousse": "#008000",
    "Simtek": "#4B0082",
    "Pacific": "#23238E",
    "Forti": "#FCE205",
    "Footwork": "#FAFAFA",
    "Leyton House": "#88D6C6",
    "Onyx": "#00008B",
    "Rial": "#0000FF",
    "Zakspeed": "#FF0000",
    "AGS": "#153F77", # JH25 Blue
    "Coloni": "#FFFF00",
    "EuroBrun": "#0A0A2A", # Dark Blue/Black
    "Osella": "#00008B",
    "Dallara": "#B71105",
    "Andrea Moda": "#505050",
    "Life": "#FF0000",
    "Fondmetal": "#505050",
    "Venturi": "#1F4096",
    "Modena": "#153F77",
    
    # 1950s - 1970s
    "Cooper": "#004225",
    "Vanwall": "#004225",
    "BRM": "#004225",
    "Maserati": "#D40000", # Italian Red
    "Alfa Romeo": "#9B0000",
    "Lancia": "#D40000",
    "Gordini": "#318CE7", # French Blue
    "Talbot-Lago": "#318CE7",
    "Matra": "#318CE7",
    "Porsche": "#C0C0C0", # German Silver
    "Mercedes-Benz": "#C0C0C0",
    "Auto Union": "#C0C0C0",
    "Honda": "#FFFFFF", # Japanese White with Red sun usually, keeping white
    "Eagle": "#000080", # American Blue
    "Shadow": "#505050",
    "Wolf": "#C9A004", # Walter Wolf Gold/Black
    "Hesketh": "#D4AF37", # Hesketh Bear Gold accents
    "Surtees": "#2955A3", # Surtees Blue
    "Penske": "#CF102D", # Penske Red
    "Fittipaldi": "#FFFF00", # Brazilian Yellow
    "Copersucar": "#FFFF00",
    "Ensign": "#FF0000",
    "Theodore": "#CE2029", # Teddy Yip Red
    "ATS": "#FFFF00",
    "Merzario": "#FF0000",
    "Rebaque": "#8B4513",
    "Kaukaser": "#FFFFFF",
    "Tecno": "#D40000",
    "Politoys": "#0000FF", # Blue
    "Connew": "#FF0000",
    "Spirit": "#FFFFFF", # Keeping White (Honda/Spirit)
    "RAM": "#006633", # Skoal Bandit Green
    
    # Indy 500 era (approximate)
    "Kurtis Kraft": "#FFFFFF",
    "Kuzma": "#FFFFFF",
    "Epperly": "#FFFFFF",
    "Watson": "#FFFFFF",
    
    # Defaults/Fallbacks for common unlisted ones
    "Veritas": "#C0C0C0",
    "Simca": "#318CE7",
    "OSCA": "#D40000",
    "Connaught": "#004225",
    "Alta": "#004225",
    "HWM": "#004225",
    "ERA": "#004225",
    "Frazer Nash": "#004225",
}

def normalize_team_name(name):
    """
    Simplifies team names by removing engine suppliers and common suffixes.
    e.g. "Lotus-Climax" -> "Lotus"
         "Cooper-Maserati" -> "Cooper"
    """
    # Common prefixes to keep as is if possible, but usually just taking the first word works well for old teams
    # except for "Team Lotus" or "Red Bull"
    
    name_check = name.lower()
    
    # Special cases
    if "red bull" in name_check: return "Red Bull"
    if "toro rosso" in name_check: return "Toro Rosso"
    if "aston martin" in name_check: return "Aston Martin"
    if "alpha tauri" in name_check or "alphatauri" in name_check: return "AlphaTauri"
    if "racing point" in name_check: return "Racing Point"
    if "force india" in name_check: return "Force India"
    if "super aguri" in name_check: return "Super Aguri"
    if "brawn" in name_check: return "Brawn"
    if "manor" in name_check: return "Manor"
    if "virgin" in name_check: return "Virgin"
    if "lotus" in name_check: return "Lotus" 
    if "alfa romeo" in name_check: return "Alfa Romeo"
    
    # Aggressive dash splitting for chassis-engine combos (common in old data)
    # e.g. "Brabham-Repco" -> "Brabham"
    if "-" in name:
        parts = name.split("-")
        # usually first part is chassis
        return parts[0].strip()
        
    return name

def build_fallbacks():
    # 1. Load existing
    current_fallbacks = {}
    if os.path.exists('fallback_teams.json'):
        with open('fallback_teams.json', 'r') as f:
            current_fallbacks = json.load(f)

    # 2. Scan data for missing teams
    files = glob.glob('data/standings_history_*.json')
    all_teams = set()
    
    print(f"Scanning {len(files)} files for teams...")
    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                history = json.load(f)
            for step in history:
                for driver in step.get('standings', []):
                    team = driver.get('team')
                    if team:
                        all_teams.add(team)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            
    print(f"Found {len(all_teams)} unique team names.")
    
    # 3. Build new map
    new_fallbacks = current_fallbacks.copy()
    
    # Enforce known colors from source of truth
    for team, color in HISTORICAL_COLORS.items():
        new_fallbacks[team] = color
    
    count_added = 0
    count_unknown = 0
    
    for team in all_teams:
        if team in new_fallbacks:
            continue
            
        normalized = normalize_team_name(team)
        
        # Try finding color for normalized name
        color = None
        
        # Direct match in HISTORICAL_COLORS
        if team in HISTORICAL_COLORS:
            color = HISTORICAL_COLORS[team]
        # Match normalized
        elif normalized in HISTORICAL_COLORS:
            color = HISTORICAL_COLORS[normalized]
        # Match keys in HISTORICAL_COLORS (case insensitive or partial)
        else:
            # Try to find a substring match in historical keys
            # e.g. "Cooper-Ford" matches key "Cooper"
            for key, val in HISTORICAL_COLORS.items():
                if key.lower() == normalized.lower():
                    color = val
                    break
        
        if color:
            new_fallbacks[team] = color
            count_added += 1
        else:
            # Assign a generic gray for completely unknown privateers to avoid crashing/empty
            # But maybe better to leave blank to alert us? 
            # User asked: "If there's not a backup color in our table, create one. Use your best guess"
            # So we should probably default to Silver/Grey for the older eras if unknown.
            
            # Simple heuristic for unknown:
            # Check for generic nationality-based guessing or just grey
            new_fallbacks[team] = "#C0C0C0" 
            count_unknown += 1

    # 4. Save
    print(f"Added {count_added} mapped colors.")
    print(f"Assigned fallback grey to {count_unknown} unknown teams.")
    
    with open('fallback_teams.json', 'w') as f:
        json.dump(new_fallbacks, f, indent=4)
    print("Updated fallback_teams.json")

if __name__ == "__main__":
    build_fallbacks()
