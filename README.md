# F1 Championship History Visualizer

An interactive dashboard for exploring Formula 1 World Championship history. This project provides two distinct ways to visualize the evolution of a season: a **Standings Animation** (bar chart race) and a **Rankings Graph** (bump chart view).

It currently supports **1991–Present**, handling scoring quirks, disqualifications, and team changes with (what I believe to be) high accuracy.

> **[Live Demo](https://aaronwe.github.io/f1-standings-timeline/)**

## ✨ Features

-   **Dual Visualizations**:
    -   **Standings Animation**: Watch the season unfold race-by-race with an animated leaderboard.
    -   **Rankings Graph**: A full-season "bump chart" (Rankings view) that lets you trace every driver's rise and fall throughout the year.

-   **Deep Historical Accuracy**:
    -   Handles complex edge cases like **Michael Schumacher's 1997 Disqualification** (showing him as DSQ in the final standings but tracking his points accurately during the season).
    -   **Dynamic Team Colors**: A massive database of historical liveries ensures every team looks right, from the iconic Ferrari Red to the 90s Jordan Gold and Benetton Blue.
    -   **Driver Disambiguation**: Robust handling of namesakes (e.g., Michael vs. Ralf Schumacher) to ensure data integrity.

-   **Mobile-First Design**:
    -   Fully responsive layouts for both charts.
    -   **Vertical Scrolling**: The rankings graph automatically expands for dense seasons (like 1992's 30+ drivers), preventing overcrowding.
    -   **High-Contrast UI**: Dark mode optimized with smart text coloring (white/black context-aware labels) and clear data outlines.

## 🛠️ Tech Stack

-   **Frontend**: Vanilla JavaScript, [Chart.js](https://www.chartjs.org/) (for the rankings graph), and CSS3 Variables for easy theming.
-   **Backend**: Python pipeline using [FastF1](https://github.com/theOehrly/Fast-F1) and [Ergast API](http://ergast.com/mrd/) via Pandas for data fetching and normalization.

## 🚀 Getting Started

### 1. Installation

Clone the repository and install the Python dependencies:

```bash
git clone https://github.com/aaronwe/f1-standings-timeline.git
cd f1-standings-timeline

python3 -m venv venv
source venv/bin/activate
pip install fastf1 pandas requests
```

### 2. Generate Data

The project comes with a set of scripts to fetch and process F1 data.

**Fetch a single season:**
```bash
# Downloads data for 1997 and generates 'data/standings_history_1997.json'
python generate_season.py --year 1997
```

**Bulk download history:**
```bash
# Downloads a range of seasons (Rate-limit aware)
python download_all_seasons.py --start 1991 --end 2024
```

> **Note**: Historical data download can take some time as it respects API rate limits.

### 3. Run Locally

Start a simple HTTP server to view the dashboard:

```bash
python3 -m http.server 8000
```

Open **http://localhost:8000** in your browser.

## 📂 Project Structure

-   `rankings.html` / `rankings.js`: The Bump Chart visualization.
-   `index.html` / `script.js`: The Standings Animation visualization.
-   `prepare_web_data.py`: The core logic for processing raw F1 data into frontend-ready JSON.
-   `generate_season.py`: Wrapper script for easy season generation.
-   `data/`: Storage for the generated JSON files (fed into the frontend).
-   `style.css`: Shared styling for the dark/premium UI.

## Credits

Designed by **Aaron Weiss**, coded by **Antigravity**, Google's AI-powered IDE.
Data courtesy of the [FastF1 Library](https://github.com/theOehrly/Fast-F1) and [Ergast](http://ergast.com/mrd/).
