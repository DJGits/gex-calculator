// Global state
let optionsData = [];
let gammaExposures = [];
let walls = {};
let gammaEnvironment = {};
let currentPrice = 450;
let riskFreeRate = 0.05;

// Initialize calculators
const gammaCalc = new GammaCalculator();
const wallAnalyzer = new WallAnalyzer();
const metricsCalc = new MetricsCalculator();
const vizEngine = new VisualizationEngine();
const strategyEngine = new StrategyEngine();
const dataGenerator = new DataGenerator();
const csvParser = new CSVParser();
const expectedMoveCalc = new ExpectedMoveCalculator();

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    updateFooterPrice();
});

function initializeEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });

    // Symbol method radio buttons
    document.querySelectorAll('input[name="symbolMethod"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            document.getElementById('popularSymbols').style.display = 
                e.target.value === 'popular' ? 'block' : 'none';
            document.getElementById('customSymbol').style.display = 
                e.target.value === 'custom' ? 'block' : 'none';
        });
    });

    // Current price input
    document.getElementById('currentPrice').addEventListener('input', (e) => {
        currentPrice = parseFloat(e.target.value);
        updateFooterPrice();
        if (optionsData.length > 0) {
            runAnalysis();
        }
    });

    // Risk-free rate slider
    document.getElementById('riskFreeRate').addEventListener('input', (e) => {
        riskFreeRate = parseFloat(e.target.value) / 100;
        document.getElementById('riskFreeRateValue').textContent = e.target.value + '%';
        gammaCalc.riskFreeRate = riskFreeRate;
        if (optionsData.length > 0) {
            runAnalysis();
        }
    });

    // Sample data sliders
    document.getElementById('numStrikes').addEventListener('input', (e) => {
        document.getElementById('numStrikesValue').textContent = e.target.value;
    });

    document.getElementById('daysToExpiry').addEventListener('input', (e) => {
        document.getElementById('daysToExpiryValue').textContent = e.target.value;
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

function updateFooterPrice() {
    document.getElementById('footerPrice').textContent = 
        `Current Price: $${currentPrice.toFixed(2)}`;
}

function generateSampleData() {
    const numStrikes = parseInt(document.getElementById('numStrikes').value);
    const daysToExpiry = parseInt(document.getElementById('daysToExpiry').value);
    
    optionsData = dataGenerator.generateSampleData(currentPrice, numStrikes, daysToExpiry);
    
    displayDataPreview();
    runAnalysis();
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const csvText = e.target.result;
            optionsData = csvParser.parse(csvText);
            
            if (optionsData.length === 0) {
                alert('No valid options data found in file');
                return;
            }

            // Auto-detect current price from the data
            // Method 1: Find strikes with lowest IV (typically ATM)
            const sortedByIV = [...optionsData].sort((a, b) => a.impliedVolatility - b.impliedVolatility);
            const atmStrike = sortedByIV[0].strike;
            
            // Method 2: Use middle of strike range as fallback
            const strikes = optionsData.map(c => c.strike);
            const minStrike = Math.min(...strikes);
            const maxStrike = Math.max(...strikes);
            const midStrike = (minStrike + maxStrike) / 2;
            
            // Use ATM strike if it's reasonable, otherwise use mid-range
            const estimatedPrice = (atmStrike > minStrike * 1.2 && atmStrike < maxStrike * 0.8) ? atmStrike : midStrike;
            
            // Update current price input and global variable
            currentPrice = estimatedPrice;
            document.getElementById('currentPrice').value = currentPrice.toFixed(2);
            updateFooterPrice();
            
            console.log(`Auto-detected current price: $${currentPrice.toFixed(2)}`);
            console.log(`  - Strike range: ${minStrike} - ${maxStrike}`);
            console.log(`  - Lowest IV strike: ${atmStrike}`);
            console.log(`  - Method used: ${estimatedPrice === atmStrike ? 'ATM strike' : 'Mid-range'}`);

            displayDataPreview();
            runAnalysis();
        } catch (error) {
            alert('Error parsing CSV file: ' + error.message);
        }
    };
    reader.readAsText(file);
}

function displayDataPreview() {
    const preview = document.getElementById('dataPreview');
    preview.style.display = 'block';

    // Calculate metrics
    const totalContracts = optionsData.length;
    const uniqueStrikes = new Set(optionsData.map(c => c.strike)).size;
    const totalOI = optionsData.reduce((sum, c) => sum + c.openInterest, 0);

    document.getElementById('totalContracts').textContent = totalContracts.toLocaleString();
    document.getElementById('uniqueStrikes').textContent = uniqueStrikes;
    document.getElementById('totalOI').textContent = totalOI.toLocaleString();

    // Show 15 strikes closest to spot
    const sortedData = optionsData
        .map(c => ({...c, distance: Math.abs(c.strike - currentPrice)}))
        .sort((a, b) => a.distance - b.distance);

    const closestStrikes = [...new Set(sortedData.slice(0, 30).map(c => c.strike))].slice(0, 15);
    const previewData = optionsData
        .filter(c => closestStrikes.includes(c.strike))
        .sort((a, b) => a.strike - b.strike || a.optionType.localeCompare(b.optionType));

    // Create table
    let tableHTML = '<table><thead><tr>';
    tableHTML += '<th>Strike</th><th>Type</th><th>OI</th><th>Volume</th>';
    tableHTML += '<th>Bid</th><th>Ask</th><th>IV</th><th>DTE</th>';
    tableHTML += '</tr></thead><tbody>';

    previewData.slice(0, 30).forEach(contract => {
        tableHTML += '<tr>';
        tableHTML += `<td>${contract.strike.toFixed(2)}</td>`;
        tableHTML += `<td>${contract.optionType.toUpperCase()}</td>`;
        tableHTML += `<td>${contract.openInterest.toLocaleString()}</td>`;
        tableHTML += `<td>${contract.volume.toLocaleString()}</td>`;
        tableHTML += `<td>$${contract.bid.toFixed(2)}</td>`;
        tableHTML += `<td>$${contract.ask.toFixed(2)}</td>`;
        tableHTML += `<td>${(contract.impliedVolatility * 100).toFixed(1)}%</td>`;
        tableHTML += `<td>${contract.daysToExpiry}</td>`;
        tableHTML += '</tr>';
    });

    tableHTML += '</tbody></table>';
    document.getElementById('previewTable').innerHTML = tableHTML;
}

function runAnalysis() {
    if (optionsData.length === 0) return;

    // Calculate gamma exposures
    gammaExposures = gammaCalc.aggregateByStrike(optionsData, currentPrice);

    // Find walls
    walls = wallAnalyzer.findAllWalls(gammaExposures, currentPrice);

    // Calculate metrics
    const metrics = metricsCalc.calculateAllMetrics(gammaExposures);
    gammaEnvironment = metricsCalc.calculateGammaEnvironment(gammaExposures, currentPrice);

    // Display results
    displayAnalysis(metrics);
    displayVisualization();
    displayStrategies();

    // Show sections
    document.getElementById('analysisSection').style.display = 'block';
    document.getElementById('strategySection').style.display = 'block';
}

function displayAnalysis(metrics) {
    // Gamma Environment
    const envType = document.getElementById('envType');
    const envStrength = document.getElementById('envStrength');
    const flipLevel = document.getElementById('flipLevel');
    const envDescription = document.getElementById('envDescription');

    const env = gammaEnvironment.environment;
    const strength = gammaEnvironment.strengthInterpretation;

    envType.textContent = env.toUpperCase();
    envType.className = 'metric-value';
    if (env === 'positive') {
        envType.style.color = '#4caf50';
        envDescription.className = 'alert alert-success';
    } else if (env === 'negative') {
        envType.style.color = '#f44336';
        envDescription.className = 'alert alert-error';
    } else {
        envType.style.color = '#ff9800';
        envDescription.className = 'alert alert-info';
    }

    envStrength.textContent = `${strength.color} ${strength.level}`;
    
    if (gammaEnvironment.gammaFlipLevel) {
        const flipDist = gammaEnvironment.gammaFlipLevel - currentPrice;
        const flipPct = (flipDist / currentPrice) * 100;
        flipLevel.textContent = `${gammaEnvironment.gammaFlipLevel.toFixed(0)} (${flipPct > 0 ? '+' : ''}${flipPct.toFixed(1)}%)`;
    } else {
        flipLevel.textContent = 'N/A';
    }

    envDescription.textContent = gammaEnvironment.description;

    // Key Metrics
    document.getElementById('netGamma').textContent = metrics.totalNetGamma.toLocaleString(undefined, {maximumFractionDigits: 0});
    document.getElementById('avgStrike').textContent = metrics.gammaWeightedAvgStrike.toFixed(0);
    document.getElementById('cpRatio').textContent = metrics.callPutGammaRatio.toFixed(2);
    document.getElementById('totalWalls').textContent = (walls.callWalls.length + walls.putWalls.length);

    // Expected Move
    displayExpectedMove();

    // Gamma Walls
    displayWalls();
}

function displayExpectedMove() {
    if (!optionsData || optionsData.length === 0) return;

    // Calculate ATM IV and DTE
    const { atmIV, overallAvgIV, avgDTE } = expectedMoveCalc.getAverageIVAndDTE(optionsData);
    
    // Calculate expected move using ATM IV
    const move = expectedMoveCalc.calculateExpectedMove(currentPrice, atmIV, avgDTE);
    
    // Display 1SD
    document.getElementById('move1SD').textContent = 
        `±$${move.expectedMove1SD.toFixed(2)} (±${move.movePct1SD.toFixed(2)}%)`;
    document.getElementById('upper1SD').textContent = `$${move.upper1SD.toFixed(2)}`;
    document.getElementById('lower1SD').textContent = `$${move.lower1SD.toFixed(2)}`;
    document.getElementById('ivInfo').textContent = 
        `Based on ${(atmIV * 100).toFixed(1)}% ATM IV and ${avgDTE.toFixed(0)} days to expiry`;
    
    // Display 2SD
    document.getElementById('move2SD').textContent = 
        `±$${move.expectedMove2SD.toFixed(2)} (±${move.movePct2SD.toFixed(2)}%)`;
    document.getElementById('upper2SD').textContent = `$${move.upper2SD.toFixed(2)}`;
    document.getElementById('lower2SD').textContent = `$${move.lower2SD.toFixed(2)}`;
    
    // Strategy suggestions
    const strategiesHTML = `
        <li>• <strong>Iron Condor:</strong> Sell strikes outside 1SD range ($${move.lower1SD.toFixed(0)} - $${move.upper1SD.toFixed(0)})</li>
        <li>• <strong>Covered Calls:</strong> Consider strikes near upper 1SD (~$${move.upper1SD.toFixed(0)})</li>
        <li>• <strong>Cash-Secured Puts:</strong> Consider strikes near lower 1SD (~$${move.lower1SD.toFixed(0)})</li>
        <li>• <strong>Long Straddle/Strangle:</strong> Profitable if move exceeds $${move.expectedMove1SD.toFixed(2)}</li>
        <li style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e0e0e0;"><strong>📊 IV Analysis:</strong></li>
        <li>• <strong>ATM IV (used):</strong> ${(atmIV * 100).toFixed(2)}% - IV of options closest to current price</li>
        <li>• <strong>Overall Avg IV:</strong> ${(overallAvgIV * 100).toFixed(2)}% - Average across all strikes</li>
        <li style="font-size: 12px; color: #666; margin-top: 5px;">ATM IV is more accurate for expected move as it excludes far OTM skew effects</li>
    `;
    document.getElementById('expectedMoveStrategies').innerHTML = strategiesHTML;
    
    // IV Assessment
    const ivLevel = expectedMoveCalc.getIVLevel(atmIV);
    const assessmentDiv = document.getElementById('ivAssessment');
    assessmentDiv.className = `alert ${ivLevel.class}`;
    assessmentDiv.innerHTML = `<strong>${ivLevel.color} ${ivLevel.level} IV (${(atmIV * 100).toFixed(1)}%)</strong><br>${ivLevel.description}`;
}

function displayWalls() {
    // Call Walls
    const callWallsDiv = document.getElementById('callWalls');
    if (walls.callWalls.length > 0) {
        let html = '';
        walls.callWalls.slice(0, 5).forEach(wall => {
            const distPct = ((wall.strike - currentPrice) / currentPrice) * 100;
            html += `<div class="wall-item">`;
            html += `<strong>#${wall.significanceRank}: ${wall.strike.toFixed(0)}</strong> `;
            html += `(${distPct > 0 ? '+' : ''}${distPct.toFixed(1)}%) - `;
            html += `${wall.exposureValue.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
            html += `</div>`;
        });
        callWallsDiv.innerHTML = html;
    } else {
        callWallsDiv.innerHTML = '<p>No significant call walls identified</p>';
    }

    // Put Walls
    const putWallsDiv = document.getElementById('putWalls');
    if (walls.putWalls.length > 0) {
        let html = '';
        walls.putWalls.slice(0, 5).forEach(wall => {
            const distPct = ((wall.strike - currentPrice) / currentPrice) * 100;
            html += `<div class="wall-item">`;
            html += `<strong>#${wall.significanceRank}: ${wall.strike.toFixed(0)}</strong> `;
            html += `(${distPct > 0 ? '+' : ''}${distPct.toFixed(1)}%) - `;
            html += `${wall.exposureValue.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
            html += `</div>`;
        });
        putWallsDiv.innerHTML = html;
    } else {
        putWallsDiv.innerHTML = '<p>No significant put walls identified</p>';
    }
}

function displayVisualization() {
    vizEngine.createGammaExposureChart(gammaExposures, walls, currentPrice);
}

function displayStrategies() {
    const strategyContent = document.getElementById('strategyContent');
    strategyContent.innerHTML = strategyEngine.generateRecommendations(
        gammaEnvironment,
        walls,
        currentPrice
    );
}

// Placeholder for Yahoo Finance (requires backend/proxy)
function fetchYahooData() {
    alert('Yahoo Finance data fetching requires a backend server due to CORS restrictions. Please use the Sample Data tab for demonstration.');
}
