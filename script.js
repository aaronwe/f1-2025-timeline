document.addEventListener('DOMContentLoaded', () => {
    let history = [];
    let currentIndex = -1;
    let driverElements = {}; // Map<DriverName, HTMLElement>
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

            // Load newest season by default
            if (seasons.length > 0) {
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
                // Add room for 25 more points as requested
                seasonMaxPoints = winnerPoints + 25;
            }

            currentIndex = 0;
            render();
        }
    }

    function getOrCreateDriverRow(driverData) {
        const id = driverData.name;
        if (driverElements[id]) {
            return driverElements[id];
        }

        const row = document.createElement('div');
        row.className = 'driver-row';
        // Updated: Only show Last Name (driverData.name)
        row.innerHTML = `
            <div class="label-info">
                <div class="rank"></div>
                <div class="driver-meta">
                    <div class="name">${driverData.name}</div>
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
        const standings = step.standings;
        // Use seasonMaxPoints for globally consistent scaling
        const maxPoints = seasonMaxPoints;

        const presentDriverNames = new Set();

        standings.forEach((driver, index) => {
            const row = getOrCreateDriverRow(driver);
            presentDriverNames.add(driver.name);

            row.querySelector('.rank').textContent = driver.rank;
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
