document.addEventListener('DOMContentLoaded', () => {
    const seasonSelect = document.getElementById('season-select');
    const ctx = document.getElementById('rankingsChart').getContext('2d');
    const scrollArea = document.querySelector('.chart-scroll-area');

    let chartInstance = null;
    let fallbackColors = {};

    // 1. Fetch Fallback Colors
    fetch('fallback_teams.json')
        .then(res => res.json())
        .then(data => {
            fallbackColors = data;
            fallbackColors = data;
            // 2. Fetch Seasons
            return fetch('data/seasons.json');
        })
        .then(res => res.json())
        .then(seasons => {
            populateSeasonSelect(seasons);

            // Check URL param first
            const urlParams = new URLSearchParams(window.location.search);
            const urlYear = urlParams.get('year');

            if (urlYear && seasons.includes(parseInt(urlYear))) {
                seasonSelect.value = urlYear;
                loadSeason(urlYear);
            } else if (seasons.length > 0) {
                loadSeason(seasons[0]);
            }
        })
        .catch(err => {
            console.error("Initialization error:", err);
            // Fallback load
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
        console.log(`Loading rankings for ${year}...`);

        // Update URL
        const url = new URL(window.location);
        url.searchParams.set('year', year);
        window.history.pushState({}, '', url);

        // Update Navigation Links
        // Use attribute contains selector as href might already have params
        const standingsLink = document.querySelector('a[href*="index.html"]');
        if (standingsLink) {
            standingsLink.href = `index.html?year=${year}`;
        }

        // Add cache buster to ensure new data is loaded
        fetch(`data/standings_history_${year}.json?t=${new Date().getTime()}`)
            .then(res => res.json())
            .then(data => {
                renderChart(data, year);
            })
            .catch(err => {
                console.error("Data load error:", err);
            });
    }

    function renderChart(history, year) {
        // Destroy previous chart
        if (chartInstance) {
            chartInstance.destroy();
        }

        // --- Data Processing ---

        // 1. Get Labels (Events)
        const labels = history.map(step => {
            // Shorten label: "Bahrain" or "Bahrain (S)" 
            let name = step.eventName.replace(" Grand Prix", "").replace("Pre-Season", "Test");
            if (step.session === 'Sprint') {
                name += " (S)";
            }
            return name;
        });

        // Helper to normalize names (Accents -> ASCII)
        function normalizeName(text) {
            return text
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "")
                .toLowerCase()
                .trim();
        }

        // 2. Extract Drivers and construct datasets
        const driverMap = {}; // Name -> { points: [], ranks: [], team: "", color: "" }

        // Initialize drivers from the FINAL step (to get everyone who participated?)
        // Or iterate all steps to catch one-off drivers

        // Track duplicate last names to trigger disambiguation
        const lastNameCounts = {};

        history.forEach((step, stepIndex) => {
            step.standings.forEach(d => {
                const key = d.name; // Full Name "Max Verstappen"
                const lname = d.name.split(' ').pop();

                if (!driverMap[key]) {
                    // Extract First Name for disambiguation key
                    const parts = d.name.split(' ');
                    const firstName = parts[0];
                    const lastName = parts.slice(1).join(' ');

                    // [FIX] Use stored lookupKey matches backend exactly
                    const lookupKey = d.lookupKey || `${normalizeName(lastName)}_${normalizeName(firstName)}`;

                    driverMap[key] = {
                        label: d.name,
                        name: d.name,
                        firstName: firstName,
                        lastName: lastName,
                        lookupKey: lookupKey,
                        points: new Array(history.length).fill(null),
                        data: new Array(history.length).fill(null),
                        rankLabels: new Array(history.length).fill(null), // [FIX] Initialize rankLabels
                        team: d.constructor?.name || "",
                        borderColor: d.color,
                        backgroundColor: d.color,
                        tension: 0.1,
                        fill: false,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        borderWidth: 3
                    }

                    if (!lastNameCounts[lastName]) lastNameCounts[lastName] = 0;
                    lastNameCounts[lastName]++;
                }

                const driverEntry = driverMap[key];

                // Update Color
                if ((!driverEntry.borderColor || driverEntry.borderColor === "#555555") && d.color) {
                    driverEntry.borderColor = d.color;
                    driverEntry.backgroundColor = d.color;
                }

                // Set Rank and Points
                driverEntry.data[stepIndex] = d.rank;
                driverEntry.points[stepIndex] = d.points;
                driverEntry.rankLabels[stepIndex] = d.rankDisplay || d.rank; // Fallback to rank if missing
            });
        });

        // Detect overlaps (drivers with same Last Name)
        // Actually, checking counts isn't enough (could be same driver in multiple entries? No, key is full name).
        // We need to know if MULTIPLE UNIQUE KEYS map to the same LAST NAME.
        const lastNameToKeys = {};
        Object.keys(driverMap).forEach(key => {
            const d = driverMap[key];
            const ln = d.lastName;
            if (!lastNameToKeys[ln]) lastNameToKeys[ln] = [];
            lastNameToKeys[ln].push(key);
        });

        // Update labels for disambiguation
        Object.keys(driverMap).forEach(key => {
            const d = driverMap[key];
            if (lastNameToKeys[d.lastName].length > 1) {
                // Disambiguate: "M. Schumacher"
                d.displayName = `${d.firstName.charAt(0)}. ${d.lastName}`;
            } else {
                d.displayName = d.lastName;
            }
        });
        // Post-process colors (Fallback)
        Object.values(driverMap).forEach(dataset => {
            if (!dataset.borderColor || dataset.borderColor === "#555555") {
                const teamName = dataset.team;
                if (fallbackColors[teamName]) {
                    dataset.borderColor = fallbackColors[teamName];
                    dataset.backgroundColor = fallbackColors[teamName];
                } else {
                    dataset.borderColor = "#999999"; // Default grey
                    dataset.backgroundColor = "#999999";
                }
            }

            // Adjust visual style for points inside dots
            dataset.pointRadius = 14; // Increased for 5-char scores
            dataset.pointHoverRadius = 16;
            dataset.pointBackgroundColor = dataset.borderColor; // Fill dot with color
            dataset.pointBorderWidth = 1; // [FIX] Add outline
            dataset.pointBorderColor = '#ffffff'; // [FIX] White outline for visibility
        });

        // Sort datasets by final rank (for legend order)
        const datasets = Object.values(driverMap).sort((a, b) => {
            // Get last non-null rank
            const rankA = a.data.filter(r => r !== null).pop() || 999;
            const rankB = b.data.filter(r => r !== null).pop() || 999;
            return rankA - rankB;
        });

        // --- Layout Calculation ---
        // Dynamically size width based on number of races to allow scrolling
        // Fixed density: 115px per race + 200px for labels (100 left, 100 right)
        const minWidthPerRace = 115; // px
        const totalWidth = (labels.length * minWidthPerRace) + 200;

        // Dynamically size height based on number of drivers
        // Fixed density: 40px per driver line?
        // Minimum screen height or calculated height
        const minHeightPerDriver = 40;
        const minContainerHeight = document.getElementById('rankings-container').clientHeight || 600;
        const calculatedHeight = Math.max(minContainerHeight, datasets.length * minHeightPerDriver + 100); // +100 for padding

        console.log(`Setting layout: ${totalWidth}px x ${calculatedHeight}px (Drivers: ${datasets.length})`);

        scrollArea.style.width = `${totalWidth}px`;
        scrollArea.style.height = `${calculatedHeight}px`;

        // --- Custom Plugin for Side Labels ---
        const driverLabelsPlugin = {
            id: 'driverLabels',
            afterDatasetsDraw(chart, args, options) {
                const { ctx, chartArea: { left, right }, scales: { y } } = chart;
                ctx.save();
                ctx.textBaseline = 'middle';

                const leftLabels = [];
                const rightLabels = [];

                // Helper for contrast
                function getContrastYIQ(hexcolor) {
                    if (!hexcolor) return 'white';
                    hexcolor = hexcolor.replace("#", "");
                    var r = parseInt(hexcolor.substr(0, 2), 16);
                    var g = parseInt(hexcolor.substr(2, 2), 16);
                    var b = parseInt(hexcolor.substr(4, 2), 16);
                    var yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
                    return (yiq >= 128) ? 'black' : 'white';
                }

                chart.data.datasets.forEach((dataset, i) => {
                    const meta = chart.getDatasetMeta(i);
                    const lastDataIndex = dataset.data.length - 1;

                    // Draw Points Inside Dots
                    if (!meta.hidden) {
                        const pointsArray = dataset.points || [];
                        // Determine contrast color for this dataset
                        const textColor = getContrastYIQ(dataset.borderColor);
                        ctx.fillStyle = textColor;
                        ctx.textAlign = 'center';
                        ctx.font = 'bold 9px Outfit, sans-serif';

                        meta.data.forEach((element, index) => {
                            if (dataset.data[index] !== null && pointsArray[index] !== undefined && pointsArray[index] !== null) {
                                let ptVal = pointsArray[index];
                                if (ptVal % 1 !== 0) ptVal = ptVal.toFixed(1); // Handle half points clearly
                                ctx.fillText(ptVal, element.x, element.y);
                            }
                        });
                    }

                    // --- Side Labels Logic ---
                    ctx.font = 'bold 12px Outfit, sans-serif';

                    // Find start index (first non-null)
                    let startIndex = 0;
                    for (let k = 0; k < dataset.data.length; k++) {
                        if (dataset.data[k] !== null) {
                            startIndex = k;
                            break;
                        }
                    }

                    // Find end index (last non-null)
                    let endIndex = lastDataIndex;
                    for (let k = lastDataIndex; k >= 0; k--) {
                        if (dataset.data[k] !== null) {
                            endIndex = k;
                            break;
                        }
                    }

                    // Collect Left Label
                    if (!meta.hidden && meta.data[startIndex]) {
                        const startPoint = meta.data[startIndex];
                        leftLabels.push({
                            text: dataset.label,
                            y: startPoint.y,
                            x: startPoint.x,
                            color: dataset.borderColor,
                            isMidSeason: startIndex > 0 // Flag for mid-season joiners
                        });
                    }

                    // Collect Right Label
                    if (!meta.hidden && meta.data[endIndex]) {
                        const endPoint = meta.data[endIndex];
                        rightLabels.push({
                            text: dataset.label,
                            y: endPoint.y,
                            x: endPoint.x,
                            color: dataset.borderColor,
                            isMidSeason: endIndex < lastDataIndex // Flag for mid-season leavers
                        });
                    }
                });

                // Helper to draw stacked labels
                function drawStacked(labels, align) {
                    // Sort by Y position
                    labels.sort((a, b) => a.y - b.y);

                    // Simple collision detection
                    for (let i = 0; i < labels.length; i++) {
                        if (i > 0) {
                            const prev = labels[i - 1];
                            const curr = labels[i];

                            // Only collide if they are roughly in the same X column
                            // (e.g. both starting at Round 1)
                            if (Math.abs(curr.x - prev.x) < 50) {
                                const dist = curr.y - prev.y;
                                const minSpacing = 14; // Font size + padding

                                if (dist < minSpacing) {
                                    // Push current down
                                    curr.y = prev.y + minSpacing;
                                }
                            }
                        }
                    }

                    labels.forEach(l => {
                        // [NEW] Box Logic
                        // 1. Measure Text
                        const metrics = ctx.measureText(l.text);
                        const textWidth = metrics.width;
                        const boxHeight = 18;
                        const boxPadding = 8;
                        const boxWidth = textWidth + (boxPadding * 2);

                        // 2. Determine Coordinates
                        // If align is 'right' (Left labels), box ends at tx. 
                        // If align is 'left' (Right labels), box starts at tx.
                        const offset = l.isMidSeason ? 20 : 60;
                        let tx, ty = l.y;
                        let boxX;

                        if (align === 'right') {
                            tx = l.x - offset;
                            boxX = tx - boxWidth; // Box extends to the left of the anchor
                        } else {
                            tx = l.x + offset;
                            boxX = tx; // Box starts at anchor
                        }

                        const boxY = ty - (boxHeight / 2);

                        // 3. Draw Box
                        ctx.fillStyle = l.color;
                        ctx.beginPath();
                        ctx.roundRect ? ctx.roundRect(boxX, boxY, boxWidth, boxHeight, 4) : ctx.rect(boxX, boxY, boxWidth, boxHeight);
                        ctx.fill();

                        // 4. Draw Text
                        const contrast = getContrastYIQ(l.color);
                        ctx.fillStyle = contrast === 'white' ? '#ffffff' : '#000000';
                        // Text usually draws at baseline. Middle baseline is set.
                        // Align text properly within box

                        // If align is right, we told ChartJS to align right. 
                        // But we want to center text in the box?
                        // Actually, let's explicit draw text at center of box
                        ctx.textAlign = 'center'; // Center text relative to the X coord we pass
                        const centerX = boxX + (boxWidth / 2);

                        // Draw with bold font
                        ctx.fillText(l.text, centerX, ty);
                    });
                }

                drawStacked(leftLabels, 'right');
                drawStacked(rightLabels, 'left');
            }
        };

        // --- Chart Generation ---
        Chart.defaults.color = '#ffffff';
        Chart.defaults.font.family = 'Outfit, sans-serif';

        // Total drivers for dynamic height
        const totalDrivers = datasets.length; // Use 'datasets' which is already defined and sorted

        // Config
        const config = {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true, // Resize with container
                maintainAspectRatio: false, // [FIX] Allow vertical scrolling/stretching
                layout: {
                    padding: {
                        top: 20,
                        right: 160, // [FIX] Reduced padding
                        bottom: 20,
                        left: 160   // [FIX] Reduced padding
                    }
                },
                scales: {
                    y: {
                        reverse: true,
                        beginAtZero: false,
                        min: 1,
                        max: totalDrivers,
                        offset: true,
                        grid: { color: '#333333' },
                        ticks: { stepSize: 1, padding: 20 },
                        title: { display: false }
                    },
                    y2: {
                        position: 'right',
                        reverse: true,
                        beginAtZero: false,
                        min: 1,
                        max: totalDrivers,
                        offset: true,
                        grid: { drawOnChartArea: false, color: '#333333' },
                        ticks: { stepSize: 1, padding: 20 },
                        title: { display: false }
                    },
                    x: {
                        grid: { color: '#333333' },
                        position: 'bottom'
                    },
                    x2: {
                        position: 'top',
                        grid: { drawOnChartArea: false, color: '#333333' }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    intersect: false
                },
                hover: {
                    mode: 'nearest',
                    intersect: false
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        filter: function (tooltipItem) {
                            const idx = tooltipItem.dataIndex;
                            const step = history[idx];
                            if (!step.raceResults) return true;
                            const dataset = tooltipItem.chart.data.datasets[tooltipItem.datasetIndex];
                            const key = dataset.lookupKey;
                            return step.raceResults.hasOwnProperty(key);
                        },
                        itemSort: function (a, b) {
                            const idx = a.dataIndex;
                            const step = history[idx];
                            if (!step.raceResults) {
                                const dsA = a.chart.data.datasets[a.datasetIndex];
                                const dsB = b.chart.data.datasets[b.datasetIndex];
                                const ptA = dsA.points[idx] - (idx > 0 ? dsA.points[idx - 1] : 0);
                                const ptB = dsB.points[idx] - (idx > 0 ? dsB.points[idx - 1] : 0);
                                return ptB - ptA;
                            }
                            // Robust Key Lookup
                            const dsA = a.chart.data.datasets[a.datasetIndex];
                            const dsB = b.chart.data.datasets[b.datasetIndex];

                            // Try stored key, else derive from label (fallback)
                            const keyA = dsA.lookupKey || (dsA.label ? normalizeName(dsA.label.split(' ').slice(1).join(' ')) + '_' + normalizeName(dsA.label.split(' ')[0]) : '');
                            const keyB = dsB.lookupKey || (dsB.label ? normalizeName(dsB.label.split(' ').slice(1).join(' ')) + '_' + normalizeName(dsB.label.split(' ')[0]) : '');

                            const resA = step.raceResults[keyA] || '999';
                            const resB = step.raceResults[keyB] || '999';

                            const getRank = (r) => {
                                if (r === 'DNF') return 1000;
                                if (r === 'DSQ') return 1001;
                                return !isNaN(r) ? parseFloat(r) : 999;
                            };

                            // Ascending: 1 finishes before 2
                            return getRank(resA) - getRank(resB);
                        },
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleFont: { family: 'Outfit, sans-serif', size: 13 },
                        bodyFont: { family: 'Outfit, sans-serif', size: 13, weight: 'normal' },
                        callbacks: {
                            title: function (context) {
                                if (!context || !context.length) return '';
                                if (!context || !context.length) return ''; // Safety check
                                const idx = context[0].dataIndex;
                                const step = history[idx];
                                return `${step.eventName} | ${step.session}\n${step.date} | ${step.location}`;
                            },
                            label: function (context) {
                                // 1. Identify "Active" Driver (Hovered)
                                const activeElements = context.chart.getActiveElements();
                                let isActive = false;
                                if (activeElements && activeElements.length > 0) {
                                    // With mode: 'nearest', activeElements[0] is the hovered item
                                    if (activeElements[0].datasetIndex === context.datasetIndex) {
                                        isActive = true;
                                    }
                                }

                                const idx = context.dataIndex;
                                const step = history[idx];
                                const dataset = context.dataset;
                                // Robust Key Lookup for Label
                                const key = dataset.lookupKey || (dataset.label ? normalizeName(dataset.label.split(' ').slice(1).join(' ')) + '_' + normalizeName(dataset.label.split(' ')[0]) : '');

                                let label = dataset.label || '';
                                let val = '?';

                                // [FIX] Show RACE RESULT to match the sort order (1, 2, 3...)
                                if (step.raceResults && step.raceResults[key]) {
                                    val = step.raceResults[key];
                                }

                                // Format: "Position. Name"
                                let text = `${val}. ${label}`;

                                // If this is the hovered driver, make it "BOLD" using Unicode
                                if (isActive) {
                                    text = toUnicodeBold(text);
                                }

                                return text;
                            }
                        }
                    },
                    title: {
                        display: false
                    }
                }
            },
            plugins: [driverLabelsPlugin]
        };

        chartInstance = new Chart(ctx, config);
    }
});

// Helper: Unicode Bold (Mathematical Sans-Serif Bold)
function toUnicodeBold(text) {
    return text.split('').map(char => {
        const n = char.charCodeAt(0);
        // 0-9
        if (n >= 48 && n <= 57) return String.fromCodePoint(0x1D7EC + (n - 48));
        // A-Z
        if (n >= 65 && n <= 90) return String.fromCodePoint(0x1D5D4 + (n - 65));
        // a-z
        if (n >= 97 && n <= 122) return String.fromCodePoint(0x1D5EE + (n - 97));
        return char;
    }).join('');
}

