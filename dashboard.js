document.addEventListener('DOMContentLoaded', function () {
  console.log('[Streak] Initializing dashboard...');

  // 1. PROPERLY DEFINE ALL ELEMENTS
  const dashboard = document.querySelector('.dashboard-page') || document.body;
  const calendarWrapper = document.getElementById('calendar-wrapper');
  const rangeSelector = document.getElementById('streak-range');

  if (!calendarWrapper) {
    console.error('Calendar wrapper element not found');
    return;
  }

  // 2. PARSE DATA
  let heatmapData = {}, platformsData = {};
  try {
    heatmapData = JSON.parse(calendarWrapper.dataset.activityJson || '{}');
    platformsData = JSON.parse(calendarWrapper.dataset.platformsPerDay || '{}');
  } catch (e) {
    console.error('Failed to parse heatmap data:', e);
  }

  // 3. FORMAT DATA
  const formattedData = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  for (const dateStr in heatmapData) {
    const rawCount = heatmapData[dateStr];
    if (rawCount > 0) {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) continue;
      date.setHours(0, 0, 0, 0);

      const sources = platformsData[dateStr] || [];
      const value = sources.includes('LeetCode') ? 1 : rawCount;

      formattedData.push({ date, value });
    }
  }

  // 4. HEATMAP INSTANCE
  let heatmapInstance = null;

  function renderHeatmap(months) {
    if (heatmapInstance) heatmapInstance.destroy();

    const startDate = new Date(today);
    startDate.setMonth(today.getMonth() - months + 1);
    startDate.setDate(1);

    const rangeData = formattedData.filter(item =>
      item.date >= startDate && item.date <= today
    );

    console.log(`Rendering ${months} month(s) from ${startDate.toDateString()} to ${today.toDateString()}`);
    console.log(`Filtered ${rangeData.length} data points`);

    heatmapInstance = new CalHeatmap();
    heatmapInstance.paint({
      itemSelector: calendarWrapper,
      data: { source: rangeData, x: 'date', y: 'value' },
      date: {
        start: startDate,
        end: today,
        timezone: 'Asia/Kolkata',
        locale: { weekStart: 1 }
      },
      range: months,
      domain: {
        type: 'month',
        gutter: 8,
        label: { text: 'MMM', position: 'top', textAlign: 'start' }
      },
      subDomain: { type: 'day', radius: 2, width: 12, height: 12, gutter: 2 },
      scale: {
        color: {
          type: 'threshold',
          range: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'],
          domain: [1, 2, 3, 4]
        }
      }
    });
  }

  // 5. RANGE SELECTOR
  if (rangeSelector) {
    rangeSelector.addEventListener('change', function () {
      const rangeMap = { month: 1, '6months': 6, '1year': 12 };
      renderHeatmap(rangeMap[this.value] || 3);
    });
  }

  // 6. INITIAL RENDER
  if (formattedData.length > 0) {
    renderHeatmap(3);
  } else {
    calendarWrapper.innerHTML =
      '<p class="text-muted">No activity data available</p>';
  }

  // 7. CSS FALLBACK
  const style = document.createElement('style');
  style.textContent = `
    .ch-subdomain[data-value="1"] { fill: #9be9a8 !important; }
    .ch-subdomain[data-value="2"] { fill: #40c463 !important; }
    .ch-subdomain[data-value="3"] { fill: #30a14e !important; }
    .ch-subdomain[data-value="4"] { fill: #216e39 !important; }
    .graph { margin: 0 auto; }
  `;
  document.head.appendChild(style);

  // ---------------------------
  // 📊 Codeforces Rating Chart
  // ---------------------------
  const codeforcesSection = dashboard.querySelector('#codeforces-section');
  const cfJsonString = codeforcesSection?.dataset.platformData || '{}';
  let codeforcesData = {};
  try { codeforcesData = JSON.parse(cfJsonString); }
  catch (e) { console.error("Codeforces JSON error", e); }

  const cfChartDiv = dashboard.querySelector('#cf_rating_chart');
  if (cfChartDiv && codeforcesData.rating_history?.length > 0) {
    const labels = codeforcesData.rating_history.map(e =>
      new Date(e.ratingUpdateTimeSeconds * 1000).toLocaleDateString());
    const data = codeforcesData.rating_history.map(e => e.newRating);
    const canvas = document.createElement('canvas');
    cfChartDiv.innerHTML = ''; cfChartDiv.appendChild(canvas);
    new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Codeforces Rating',
          data,
          borderColor: 'rgb(75,192,192)',
          backgroundColor: 'rgba(75,192,192,0.2)',
          fill: true
        }]
      },
      options: {
        responsive: true,
        plugins: {
          tooltip: {
            callbacks: {
              title: (ctx) => {
                return `Contest ID: ${codeforcesData.rating_history[ctx[0].dataIndex].contestId}`;
              },
              label: (ctx) => {
                const d = codeforcesData.rating_history[ctx.dataIndex];
                return [
                  `Date: ${new Date(d.ratingUpdateTimeSeconds * 1000).toLocaleDateString()}`,
                  `Rating: ${d.newRating}`,
                  `Old: ${d.oldRating}`,
                  `Rank: ${d.rank}`
                ];
              }
            }
          }
        },
        scales: {
          x: { title: { display: true, text: 'Date' } },
          y: { title: { display: true, text: 'Rating' } }
        }
      }
    });
  } else {
    cfChartDiv.innerHTML =
      '<p class="text-center text-muted">No  data available.</p>';
  }

  // ---------------------------
  // 📈 LeetCode / GFG / Codeforces Charts
  // ---------------------------
  const lcGfgSection = dashboard.querySelector('#lc-gfg-section');
  const leetcodeJsonString = lcGfgSection?.dataset.lcTopic || '{}';
  const gfgJsonString = lcGfgSection?.dataset.gfgTopic || '{}';
  let leetcodeData = {}, gfgData = {};
  try { leetcodeData = JSON.parse(leetcodeJsonString); }
  catch (e) { console.error("LeetCode JSON error", e); }
  try { gfgData = JSON.parse(gfgJsonString); }
  catch (e) { console.error("GFG JSON error", e); }

  const lgChartDiv = dashboard.querySelector('#lg_chart');
  const platformSelect = dashboard.querySelector('#platform-select');
  const modeSelect = dashboard.querySelector('#mode-select');
  const lgChartTitle = dashboard.querySelector('#lg-chart-title');
  let problemChart;

  function updateChart() {
    if (problemChart) problemChart.destroy();
    const platform = platformSelect?.value || (
      leetcodeData.solved_total ? 'leetcode' :
        (gfgData.solved_total ? 'gfg' : '')
    );
    const mode = modeSelect?.value || 'level';

    let labels = [], chartData = [], chartType = '', title = '';

    if (mode === 'level') {
      chartType = 'pie';
      labels = ['Easy', 'Medium', 'Hard'];
      const vals = [0, 0, 0];
      if (platform === 'leetcode' || platform === 'both') {
        vals[0] += leetcodeData.solved_easy || 0;
        vals[1] += leetcodeData.solved_medium || 0;
        vals[2] += leetcodeData.solved_hard || 0;
      }
      if (platform === 'gfg' || platform === 'both') {
        vals[0] += gfgData.solved_easy || 0;
        vals[1] += gfgData.solved_medium || 0;
        vals[2] += gfgData.solved_hard || 0;
      }
      chartData = vals;
      title = `Problems by Level (${platform})`;
    } else {
      chartType = 'bar';
      const topicMap = {};

      if (platform === 'leetcode' || platform === 'both') {
        const skillStats = leetcodeData.skill_stats || {};
        const allSkillGroups = [...(skillStats.advanced || []), ...(skillStats.fundamental || [])];
        allSkillGroups.forEach(tag => {
          topicMap[tag.tagName] = (topicMap[tag.tagName] || 0) + tag.problemsSolved;
        });
      }

      if (platform === 'gfg' || platform === 'both') {
        const gfgSkills = gfgData.skill_stats || {};
        for (const topic in gfgSkills) {
          topicMap[topic] = (topicMap[topic] || 0) + gfgSkills[topic];
        }

        if (gfgData.topics_solved_count) {
          for (const name in gfgData.topics_solved_count) {
            topicMap[name] = (topicMap[name] || 0) + gfgData.topics_solved_count[name];
          }
        }
      }

      labels = Object.keys(topicMap);
      chartData = Object.values(topicMap);
      if (labels.length === 0) {
        lgChartTitle.textContent = '';
        lgChartDiv.innerHTML =
          '<p class="text-center text-muted">No topic-wise data available.</p>';
        return;
      }
      title = `Problems by Topic (${platform})`;
    }

    lgChartTitle.textContent = title;
    const canvas = document.createElement('canvas');
    lgChartDiv.innerHTML = ''; lgChartDiv.appendChild(canvas);

    problemChart = new Chart(canvas.getContext('2d'), {
      type: chartType,
      data: {
        labels,
        datasets: [{
          label: 'Solved',
          data: chartData,
          backgroundColor: chartType === 'pie'
            ? ['rgba(40,167,69,0.7)', 'rgba(255,193,7,0.7)', 'rgba(220,53,69,0.7)']
            : 'rgba(0,123,255,0.7)',
          borderColor: chartType === 'pie'
            ? ['rgba(40,167,69,1)', 'rgba(255,193,7,1)', 'rgba(220,53,69,1)']
            : 'rgba(0,123,255,1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: chartType === 'bar' ? { y: { beginAtZero: true } } : {},
        plugins: { legend: { display: true, position: 'top' } }
      }
    });
  }

  if (!platformSelect?.value) {
    if (leetcodeData.solved_total) platformSelect.value = 'leetcode';
    else if (gfgData.solved_total) platformSelect.value = 'gfg';
  }
  platformSelect?.addEventListener('change', updateChart);
  modeSelect?.addEventListener('change', updateChart);

  if (Object.keys(leetcodeData).length > 0 ||
    Object.keys(gfgData).length > 0) {
    updateChart();
  } else {
    lgChartDiv.innerHTML =
      '<p class="text-center text-muted">No LeetCode or GeeksforGeeks data available.</p>';
  }

  // ---------------------------
  // 📅 LeetCode Calendar View
  // ---------------------------
  const data = JSON.parse(document.getElementById("leetcode-year-data").textContent);
  const monthGrid = document.getElementById("monthGrid");
  const calendarGrid = document.getElementById("calendarGrid");
  const calendarTitle = document.getElementById("calendarTitle");
  const calendarContainer = document.getElementById("calendarContainer");
  const monthsSelect = document.getElementById("monthsSelect");

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  function getColorLevel(count) {
    if (count >= 10) return 4;
    if (count >= 5) return 3;
    if (count >= 3) return 2;
    if (count >= 1) return 1;
    return 0;
  }

  function getLocalISODate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function renderMonthBlock(year, monthIndex) {
    const monthBlock = document.createElement("div");
    monthBlock.className = "month-block";

    const title = document.createElement("div");
    title.className = "month-name";
    title.textContent = `${monthNames[monthIndex]} ${year}`;
    monthBlock.appendChild(title);

    const daysGrid = document.createElement("div");
    daysGrid.className = "days-grid";

    const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();

    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, monthIndex, day);
      const iso = date.toISOString().split("T")[0];
      const count = data[iso] || 0;
      const level = getColorLevel(count);

      const cell = document.createElement("div");
      cell.className = `heatmap-cell level-${level}`;
      cell.title = `${iso}: ${count} submissions`;

      daysGrid.appendChild(cell);
    }

    monthBlock.appendChild(daysGrid);
    return monthBlock;
  }

  function renderMonths(range = 12) {
    monthGrid.innerHTML = '';
    const today = new Date();
    for (let i = range - 1; i >= 0; i--) {
      const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
      const block = renderMonthBlock(d.getFullYear(), d.getMonth());
      monthGrid.appendChild(block);
    }
  }

  function renderCalendarMonth() {
    calendarGrid.innerHTML = '';

    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const startDay = new Date(year, month, 1).getDay();

    calendarTitle.textContent = `${monthNames[month]} ${year}`;

    for (let i = 0; i < startDay; i++) {
      const blank = document.createElement("div");
      calendarGrid.appendChild(blank);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const iso = getLocalISODate(date);
      const count = data[iso] || 0;
      const level = getColorLevel(count);

      const cell = document.createElement("div");
      cell.className = `calendar-day level-${level}`;
      cell.textContent = day;
      cell.title = `${iso}: ${count} submissions`;

      calendarGrid.appendChild(cell);
    }
  }

  const cardWrapper = document.querySelector('.card');

  monthsSelect.addEventListener("change", (e) => {
    const value = parseInt(e.target.value);

    if (value === 1) {
      calendarContainer.style.display = "block";
      monthGrid.style.display = "none";
      cardWrapper.classList.remove("compact-mode");
      renderCalendarMonth();
    } else {
      calendarContainer.style.display = "none";
      monthGrid.style.display = "flex";
      cardWrapper.classList.add("compact-mode");
      renderMonths(value);
    }
  });

  renderCalendarMonth();
  calendarContainer.style.display = "block";
  monthGrid.style.display = "none";
});
