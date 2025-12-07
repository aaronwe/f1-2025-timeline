# F1 2025 Season Standings Timeline

An interactive, animated bar chart visualization of the 2025 Formula 1 Championship standings. This web application allows users to step through every race and sprint session of the season to see how the driver standings evolved.

**[Live Demo](https://aaronwe.github.io/f1-2025-timeline/)**

## Features
- **Interactive Timeline**: Step forward and backward through the season.
- **Sprint Support**: Correctly handles Sprint weekends, treating the Sprint and Grand Prix as separate scoring events.
- **Responsive Design**: Validated for mobile and desktop, with touch-friendly controls and dynamic layouts.
- **Contextual Metadata**: Displays the race date and location for every event.
- **Smart Filtering**: Automatically filters out future races that haven't occurred yet.

## Technology Stack
- **Frontend**: Vanilla HTML, CSS, and JavaScript.
- **Data Processing**: Python, Pandas.
- **F1 Data API**: [FastF1](https://github.com/theOehrly/Fast-F1) library.
- **Visualization Logic**: Custom JS implementation inspired by `bar_chart_race`.

## Data Pipeline (Python)

The project uses Python scripts to fetch real-time F1 data and format it for the web app.

### 1. `prepare_web_data.py`
This is the main script for the web application.
- **Purpose**: Fetches the 2025 schedule and session results, calculates cumulative standings after every scoring session (Sprints and Races), and exports the history to `standings_history.json`.
- **Key Features**: 
    - Separates Sprint and Race sessions.
    - Extracts metadata (Date, Location).
    - Filters out empty/future results.
- **Output**: `standings_history.json` (consumed by the frontend).

### 2. `fetch_data.py`
A utility script for raw data extraction.
- **Purpose**: Fetches session results and saves them to CSV format (`f1_2025_raw_points.csv` and `f1_2025_cumulative_standings.csv`). Useful for data analysis or debugging.

### 3. `animate_standings.py`
- **Purpose**: Generates a standalone MP4 video animation of the standings using the `bar_chart_race` library. This was the precursor to the interactive web app.

## Running Locally

1. **Clone the repository**:
   ```bash
   git clone https://github.com/aaronwe/f1-2025-timeline.git
   cd f1-2025-timeline
   ```

2. **(Optional) Update Data**:
   If you want to fetch fresh data:
   ```bash
   # Install dependencies
   pip install fastf1 pandas

   # Run the script
   python prepare_web_data.py
   ```

3. **Start the server**:
   Any static file server will work. Python's built-in one is easy:
   ```bash
   python3 -m http.server 8080
   ```

4. **View**: Open `http://localhost:8080` in your browser.

## Credits
This project was designed and built in collaboration with **Antigravity**, an AI coding assistant.
- **Concept & Direction**: Aaron Weiss
- **Implementation & Documentation**: Antigravity
