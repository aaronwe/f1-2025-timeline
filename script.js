document.addEventListener('DOMContentLoaded', () => {
    let history = [];
    let currentIndex = -1;
    let driverElements = {}; // Map<DriverName, HTMLElement>
    let displayNameMap = {}; // Map<FullName, DisplayName>
    let seasonMaxPoints = 100; // Default, overrides after load

    const eventNameEl = document.getElementById('event-name');
    const eventMetaEl = document.getElementById('event-meta');
    const sessionTypeEl = document.getElementById('session-type');
    const chartContainer = document.getElementById('chart-container');
    const progressBarEl = document.getElementById('progress-bar');
    const stepIndicatorEl = document.getElementById('step-indicator');
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');
    const btnFirst = document.getElementById('btn-first');
    const btnLast = document.getElementById('btn-last');

    const ROW_HEIGHT = 45;

    const seasonSelect = document.getElementById('season-select');

    // 1. Fetch Available Seasons
    fetch('data/seasons.json')
        .then(response => response.json())
        .then(seasons => {
            populateSeasonSelect(seasons);

            // Check URL param first
            const urlParams = new URLSearchParams(window.location.search);
            const urlYear = urlParams.get('year');

            // Load newest season by default or URL year
            if (urlYear && seasons.includes(parseInt(urlYear))) {
                seasonSelect.value = urlYear;
                loadSeason(urlYear);
            } else if (seasons.length > 0) {
                loadSeason(seasons[0]);
            }
        })
        .catch(err => {
            console.error("Failed to load seasons manifest", err);
            // Fallback: Try to load 2025 directly if manifest fails
            loadSeason(2025);
        });

    function populateSeasonSelect(seasons) {
        seasonSelect.innerHTML = '';
        seasons.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            seasonSelect.appendChild(option);
        });

        seasonSelect.addEventListener('change', (e) => {
            loadSeason(e.target.value);
        });
    }

    function loadSeason(year) {
        console.log(`Loading season ${year}...`);

        // Update URL
        const url = new URL(window.location);
        url.searchParams.set('year', year);
        window.history.pushState({}, '', url);

        // Update Navigation Links
        // Use attribute contains selector as href might already have params
        const rankingsLink = document.querySelector('a[href*="rankings.html"]');
        if (rankingsLink) {
            rankingsLink.href = `rankings.html?year=${year}`;
        }

        // Reset state
        currentIndex = -1;
        chartContainer.innerHTML = '';
        driverElements = {};

        fetch(`data/standings_history_${year}.json`)
            .then(response => response.json())
            .then(data => {
                history = data;
                init();
            })
            .catch(err => {
                console.error(`Failed to load data for ${year}`, err);
                chartContainer.innerHTML = `<div class="error">Failed to load data for ${year}</div>`;
            });
    }

    function init() {
        if (history.length > 0) {
            // Calculate Season Max for Fixed Scaling
            // Look at the last step's standings to find the winner's points.
            const lastStep = history[history.length - 1];
            if (lastStep.standings.length > 0) {
                // Assuming standings are sorted, index 0 is max
                const winnerPoints = lastStep.standings[0].points;
                // [FIX] Scale so winner is exactly 95% of width
                seasonMaxPoints = winnerPoints / 0.95;
            }

            currentIndex = 0;
            render();
        }
    }

    function getOrCreateDriverRow(driverData) {
        // [FIX] Use unique key (Full Name) to prevent collisions
        const id = `${driverData.firstName} ${driverData.name}`;
        if (driverElements[id]) {
            return driverElements[id];
        }

        const row = document.createElement('div');
        row.className = 'driver-row';

        // Determine Display Name
        let displayLabel = driverData.name;
        if (displayNameMap[id]) {
            displayLabel = displayNameMap[id];
        }

        // Updated: Show Name (potentially disambiguated)
        row.innerHTML = `
            <div class="label-info">
                <div class="rank"></div>
                <div class="driver-meta">
                    <div class="name">${displayLabel}</div>
                    <div class="team-name">${driverData.team}</div>
                </div>
            </div>
            <div class="bar-container">
                <div class="bar" data-team="${driverData.team}">
                    <div class="bar-points">0</div>
                </div>
            </div>
        `;

        row.style.transform = `translateY(800px)`;

        chartContainer.appendChild(row);
        driverElements[id] = row;
        return row;
    }

    function render() {
        if (currentIndex < 0 || currentIndex >= history.length) return;

        const step = history[currentIndex];

        // Update Header
        eventNameEl.textContent = step.eventName;
        eventMetaEl.textContent = `${step.date} | ${step.location}`;
        sessionTypeEl.textContent = step.session;

        // Update Controls
        stepIndicatorEl.textContent = `${currentIndex + 1} / ${history.length}`;
        const progress = ((currentIndex + 1) / history.length) * 100;
        progressBarEl.style.width = `${progress}%`;

        btnPrev.disabled = currentIndex === 0;
        btnNext.disabled = currentIndex === history.length - 1;
        btnFirst.disabled = currentIndex === 0;
        btnLast.disabled = currentIndex === history.length - 1;

        // Render Chart
        // Render Chart
        // [FIX] Sort by rank to ensure forced ranks (like 1997 DSQ) are respected visually
        const standings = [...step.standings].sort((a, b) => a.rank - b.rank);
        const presentDriverNames = new Set();
        const maxPoints = seasonMaxPoints;

        standings.forEach((driver, index) => {
            const row = getOrCreateDriverRow(driver);
            // Track by unique ID
            presentDriverNames.add(`${driver.firstName} ${driver.name}`);

            // [FIX] Use rankDisplay (e.g. "DSQ") if provided, otherwise standard rank
            row.querySelector('.rank').textContent = driver.rankDisplay || driver.rank;
            row.querySelector('.bar-points').textContent = driver.points;

            let widthPercent = 0;
            if (maxPoints > 0) {
                widthPercent = (driver.points / maxPoints) * 100;
            }
            widthPercent = Math.max(widthPercent, 0);

            const bar = row.querySelector('.bar');
            bar.style.width = `${widthPercent}%`;

            // Toggle inside/outside class
            // Threshold: increased to 20% to prevent cramping on mobile
            const pointsEl = row.querySelector('.bar-points');
            if (widthPercent > 20) {
                pointsEl.classList.add('inside');
            } else {
                pointsEl.classList.remove('inside');
            }

            if (bar.dataset.team !== driver.team) {
                bar.dataset.team = driver.team;
            }

            // Apply dynamic color from data if available
            if (driver.color) {
                bar.style.backgroundColor = driver.color;
            } else {
                bar.style.backgroundColor = ''; // Revert to CSS default/rules
            }

            const translateY = index * ROW_HEIGHT;
            row.style.transform = `translateY(${translateY}px)`;
            row.style.opacity = '1';
        });

        for (const [name, row] of Object.entries(driverElements)) {
            if (!presentDriverNames.has(name)) {
                row.style.opacity = '0';
            }
        }
    }

    btnPrev.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            render();
        }
    });

    btnNext.addEventListener('click', () => {
        if (currentIndex < history.length - 1) {
            currentIndex++;
            render();
        }
    });

    btnFirst.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex = 0;
            render();
        }
    });

    btnLast.addEventListener('click', () => {
        if (currentIndex < history.length - 1) {
            currentIndex = history.length - 1;
            render();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            if (e.shiftKey) btnFirst.click();
            else btnPrev.click();
        }
        if (e.key === 'ArrowRight') {
            if (e.shiftKey) btnLast.click();
            else btnNext.click();
        }
    });
});
