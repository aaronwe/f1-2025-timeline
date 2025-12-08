# Formula 1 Standings Visualization (1950-2025)

An interactive, animated bar chart visualization of the Formula 1 Championship standings. This project has been expanded to support **every season in F1 history** (1950–Present), allowing users to explore the evolution of the championship across decades.

**[Live Demo](https://aaronwe.github.io/f1-2025-timeline/)**

## Features
- **Historical Support**: Explore detailed standings for any season from 1950 to today.
- **Accurate Team Colors**: 
    - Includes a comprehensive database of historical team colors (e.g., Maserati Red, Vanwall Green, Shadow Black/Gray).
    - Automatically maps merged or renamed teams (e.g., "Lotus-Climax" uses Lotus colors).
- **Interactive Timeline**: Step forward and backward through every race and sprint session.
- **Sprint Support**: Correctly handles Sprint weekends, treating the Sprint and Grand Prix as separate scoring events.
- **Responsive Design**: Validated for mobile and desktop, with touch-friendly controls.

## Data Pipeline (Python)

The project uses a robust Python pipeline to fetch, clean, and format data using the [FastF1](https://github.com/theOehrly/Fast-F1) library.

### 1. `download_all_seasons.py`
The master script for fetching data.
- **Usage**: `python download_all_seasons.py --start 1950 --end 2025`
- **Features**:
    - Rate-limit aware (pauses to respect API limits).
    - Resumable (maintains a progress log).
    - Caches data locally to `f1_cache`.

### 2. `prepare_web_data.py`
Processes a single season into the JSON format used by the frontend.
- **Usage**: `python prepare_web_data.py --year 1999`
- **Output**: `data/standings_history_1999.json`

### 3. Team Color Management
We maintain a custom database of team colors to ensure charts look great even for defunct teams.
- **`fallback_teams.json`**: The master map of "Team Name" -> "Hex Color".
- **`build_fallbacks.py`**: Scans your downloaded data and automatically adds missing teams to the fallback list (assigning defaults if unknown).
- **`patch_colors.py`**: Directly updates existing JSON data files with the latest colors from the fallback list (no API calls required).
- **`update_colors.sh`**: A helper script that runs the build and patch steps in sequence. Run this if you see missing colors!

## Running Locally

1. **Clone the repository**:
   ```bash
   git clone https://github.com/aaronwe/f1-2025-timeline.git
   cd f1-2025-timeline
   ```

2. **Install Dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install fastf1 pandas
   ```

3. **Fetch Data**:
   To download the current season:
   ```bash
   python prepare_web_data.py
   ```
   To download history (this takes time!):
   ```bash
   python download_all_seasons.py --start 1950 --end 2025
   ```

4. **Start the server**:
   ```bash
   python3 -m http.server 8080
   ```

5. **View**: Open `http://localhost:8080` in your browser.

## Credits
This project was designed and built in collaboration with **Antigravity**, an AI coding assistant.
- **Concept & Direction**: Aaron Weiss
- **Implementation & Documentation**: Antigravity
