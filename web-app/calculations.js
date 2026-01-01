// Black-Scholes Gamma Calculation
class GammaCalculator {
    constructor(riskFreeRate = 0.05) {
        this.riskFreeRate = riskFreeRate;
    }

    // Standard normal probability density function
    normPDF(x) {
        return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
    }

    // Standard normal cumulative distribution function
    normCDF(x) {
        const t = 1 / (1 + 0.2316419 * Math.abs(x));
        const d = 0.3989423 * Math.exp(-x * x / 2);
        const prob = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
        return x > 0 ? 1 - prob : prob;
    }

    // Calculate d1 for Black-Scholes
    calculateD1(spotPrice, strike, timeToExpiry, volatility) {
        const numerator = Math.log(spotPrice / strike) + 
                         (this.riskFreeRate + 0.5 * volatility * volatility) * timeToExpiry;
        const denominator = volatility * Math.sqrt(timeToExpiry);
        return numerator / denominator;
    }

    // Calculate gamma for an option
    calculateGamma(spotPrice, strike, timeToExpiry, volatility) {
        if (timeToExpiry <= 0) return 0;
        
        const d1 = this.calculateD1(spotPrice, strike, timeToExpiry, volatility);
        const gamma = this.normPDF(d1) / (spotPrice * volatility * Math.sqrt(timeToExpiry));
        
        return gamma;
    }

    // Calculate gamma exposure for a contract
    calculateGammaExposure(contract, spotPrice) {
        const timeToExpiry = contract.daysToExpiry / 365;
        const gamma = this.calculateGamma(
            spotPrice,
            contract.strike,
            timeToExpiry,
            contract.impliedVolatility
        );

        // Gamma exposure = Gamma × Open Interest × 100 × Spot Price²
        const gammaExposure = gamma * contract.openInterest * 100 * spotPrice * spotPrice;

        // Market maker perspective: short calls = negative gamma, short puts = positive gamma
        const mmGamma = contract.optionType === 'call' ? -gammaExposure : gammaExposure;

        return {
            strike: contract.strike,
            optionType: contract.optionType,
            gamma: gamma,
            gammaExposure: mmGamma,
            openInterest: contract.openInterest
        };
    }

    // Aggregate gamma by strike
    aggregateByStrike(contracts, spotPrice) {
        const strikeMap = new Map();

        contracts.forEach(contract => {
            const exposure = this.calculateGammaExposure(contract, spotPrice);
            
            if (!strikeMap.has(exposure.strike)) {
                strikeMap.set(exposure.strike, {
                    strike: exposure.strike,
                    callGamma: 0,
                    putGamma: 0,
                    netGamma: 0,
                    totalOI: 0
                });
            }

            const strikeData = strikeMap.get(exposure.strike);
            
            if (exposure.optionType === 'call') {
                strikeData.callGamma += exposure.gammaExposure;
            } else {
                strikeData.putGamma += exposure.gammaExposure;
            }
            
            strikeData.netGamma = strikeData.callGamma + strikeData.putGamma;
            strikeData.totalOI += exposure.openInterest;
        });

        return Array.from(strikeMap.values()).sort((a, b) => a.strike - b.strike);
    }
}

// Sample Data Generator
class DataGenerator {
    generateSampleData(spotPrice, numStrikes, daysToExpiry) {
        const contracts = [];
        const strikeSpacing = spotPrice * 0.02; // 2% spacing
        const startStrike = spotPrice - (numStrikes / 2) * strikeSpacing;

        for (let i = 0; i < numStrikes; i++) {
            const strike = Math.round((startStrike + i * strikeSpacing) / 5) * 5; // Round to nearest 5
            
            if (strike <= 0) continue;

            // Generate call
            contracts.push({
                strike: strike,
                expiryDate: new Date(Date.now() + daysToExpiry * 24 * 60 * 60 * 1000),
                optionType: 'call',
                openInterest: Math.floor(Math.random() * 10000 + 1000),
                volume: Math.floor(Math.random() * 5000),
                bid: Math.random() * 10 + 1,
                ask: Math.random() * 10 + 2,
                lastPrice: Math.random() * 10 + 1.5,
                impliedVolatility: Math.random() * 0.3 + 0.15, // 15-45%
                daysToExpiry: daysToExpiry
            });

            // Generate put
            contracts.push({
                strike: strike,
                expiryDate: new Date(Date.now() + daysToExpiry * 24 * 60 * 1000),
                optionType: 'put',
                openInterest: Math.floor(Math.random() * 10000 + 1000),
                volume: Math.floor(Math.random() * 5000),
                bid: Math.random() * 10 + 1,
                ask: Math.random() * 10 + 2,
                lastPrice: Math.random() * 10 + 1.5,
                impliedVolatility: Math.random() * 0.3 + 0.15,
                daysToExpiry: daysToExpiry
            });
        }

        return contracts;
    }
}

// Expected Move Calculator
class ExpectedMoveCalculator {
    /**
     * Calculate expected move based on implied volatility
     * @param {number} currentPrice - Current stock price
     * @param {number} impliedVolatility - IV as decimal (e.g., 0.25 for 25%)
     * @param {number} daysToExpiry - Days until expiration
     * @returns {Object} Expected move calculations
     */
    calculateExpectedMove(currentPrice, impliedVolatility, daysToExpiry) {
        // Expected move = Price × IV × √(DTE / 365)
        const timeFactor = Math.sqrt(daysToExpiry / 365);
        const expectedMove1SD = currentPrice * impliedVolatility * timeFactor;
        
        // 2 standard deviations (≈95% probability)
        const expectedMove2SD = expectedMove1SD * 2;
        
        // Calculate price ranges
        const upper1SD = currentPrice + expectedMove1SD;
        const lower1SD = currentPrice - expectedMove1SD;
        
        const upper2SD = currentPrice + expectedMove2SD;
        const lower2SD = currentPrice - expectedMove2SD;
        
        // Percentage moves
        const movePct1SD = (expectedMove1SD / currentPrice) * 100;
        const movePct2SD = (expectedMove2SD / currentPrice) * 100;
        
        return {
            currentPrice,
            impliedVolatility,
            ivPercentage: impliedVolatility * 100,
            daysToExpiry,
            expectedMove1SD,
            expectedMove2SD,
            movePct1SD,
            movePct2SD,
            upper1SD,
            lower1SD,
            upper2SD,
            lower2SD,
            probability1SD: 68.2,
            probability2SD: 95.4
        };
    }

    /**
     * Calculate average IV from contracts
     * Now uses ATM (At-The-Money) IV for more accurate expected move
     * @param {Array} contracts - Array of option contracts
     * @returns {Object} ATM IV, overall average IV, and average DTE
     */
    getAverageIVAndDTE(contracts) {
        if (!contracts || contracts.length === 0) {
            return { atmIV: 0, overallAvgIV: 0, avgDTE: 0 };
        }

        // Calculate overall average IV (for comparison)
        const totalIV = contracts.reduce((sum, c) => sum + c.impliedVolatility, 0);
        const overallAvgIV = totalIV / contracts.length;

        // Find ATM IV - use contracts closest to current price
        // This is more accurate than averaging all strikes
        const contractsWithDistance = contracts.map(c => ({
            contract: c,
            distance: Math.abs(c.strike - (window.currentPrice || 450))
        }));

        // Sort by distance from current price
        contractsWithDistance.sort((a, b) => a.distance - b.distance);

        // Use top 10 closest contracts (or all if less than 10)
        const numATMContracts = Math.min(10, contractsWithDistance.length);
        const atmContracts = contractsWithDistance.slice(0, numATMContracts);
        
        const atmIVSum = atmContracts.reduce((sum, item) => sum + item.contract.impliedVolatility, 0);
        const atmIV = atmIVSum / atmContracts.length;

        // Calculate average DTE
        const totalDTE = contracts.reduce((sum, c) => sum + c.daysToExpiry, 0);
        const avgDTE = totalDTE / contracts.length;

        // Debug logging
        console.log('IV Calculation Debug:', {
            totalContracts: contracts.length,
            atmContractsUsed: atmContracts.length,
            currentPrice: window.currentPrice || 450,
            atmContracts: atmContracts.map(item => ({
                strike: item.contract.strike,
                type: item.contract.optionType,
                distance: item.distance.toFixed(2),
                iv: item.contract.impliedVolatility,
                ivPct: (item.contract.impliedVolatility * 100).toFixed(2) + '%'
            })),
            atmIV: atmIV,
            atmIVPercent: (atmIV * 100).toFixed(2) + '%',
            overallAvgIV: overallAvgIV,
            overallAvgIVPercent: (overallAvgIV * 100).toFixed(2) + '%',
            sampleIVs: contracts.slice(0, 5).map(c => ({
                strike: c.strike,
                type: c.optionType,
                iv: c.impliedVolatility,
                ivPct: (c.impliedVolatility * 100).toFixed(2) + '%'
            }))
        });

        return {
            atmIV,           // ATM IV (used for calculation)
            overallAvgIV,    // Overall average (for comparison)
            avgDTE
        };
    }

    /**
     * Get IV level classification
     * @param {number} iv - Implied volatility as decimal
     * @returns {Object} Classification info
     */
    getIVLevel(iv) {
        const ivPct = iv * 100;
        
        if (ivPct > 40) {
            return {
                level: 'HIGH',
                color: '🔴',
                description: 'Large expected move. Premium selling may be attractive.',
                class: 'alert-error'
            };
        } else if (ivPct > 25) {
            return {
                level: 'MODERATE',
                color: '🟡',
                description: 'Normal expected move. Balanced strategies recommended.',
                class: 'alert-warning'
            };
        } else {
            return {
                level: 'LOW',
                color: '🟢',
                description: 'Small expected move. Buying options may be attractive.',
                class: 'alert-success'
            };
        }
    }
}

// CSV Parser
class CSVParser {
    parse(csvText) {
        const lines = csvText.trim().split('\n');
        const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
        
        const contracts = [];
        
        for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',');
            const row = {};
            
            headers.forEach((header, index) => {
                row[header] = values[index]?.trim();
            });

            // Map to contract format
            let rawIV = parseFloat(row.implied_volatility || row.iv || 0.2);
            
            // IV Normalization Strategy:
            // Yahoo Finance returns IV as decimal (0.25 = 25%, 1.5 = 150%)
            // Some sources may return as percentage (25 = 25%, 150 = 150%)
            // 
            // Decision logic:
            // - If IV > 10: Definitely a percentage, divide by 100 (e.g., 25 → 0.25, 150 → 1.50)
            // - If IV <= 10: Already in decimal format, use as-is (e.g., 0.25, 1.5, 2.0)
            //
            // Rationale: IV rarely exceeds 1000%, so any value > 10 must be a percentage
            // Values 0-10 are treated as decimals since they represent 0-1000% IV range
            
            if (rawIV > 10.0) {
                // Clearly a percentage value like 25, 150, etc.
                rawIV = rawIV / 100.0;
                console.log(`Normalized IV from percentage: ${rawIV * 100} → ${rawIV}`);
            }
            
            // Sanity check: IV should typically be between 0.01 (1%) and 10.0 (1000%)
            if (rawIV < 0.01) {
                console.warn(`Very low IV detected: ${rawIV}, setting to 0.05 (5%)`);
                rawIV = 0.05;
            } else if (rawIV > 10.0) {
                console.warn(`Extremely high IV detected: ${rawIV}, capping at 10.0 (1000%)`);
                rawIV = 10.0;
            }
            
            const contract = {
                strike: parseFloat(row.strike),
                expiryDate: new Date(row.expiry_date || row.expiration),
                optionType: (row.option_type || row.type).toLowerCase(),
                openInterest: parseInt(row.open_interest || row.openinterest || 0),
                volume: parseInt(row.volume || 0),
                bid: parseFloat(row.bid || 0),
                ask: parseFloat(row.ask || 0),
                lastPrice: parseFloat(row.last_price || row.lastprice || row.last || 0),
                impliedVolatility: rawIV
            };
            
            // Debug: Log first few contracts to verify IV normalization
            if (i <= 3) {
                console.log(`Contract ${i}: Strike=${contract.strike}, Type=${contract.optionType}, Raw IV=${parseFloat(row.implied_volatility || row.iv || 0.2)}, Normalized IV=${rawIV}, IV%=${(rawIV * 100).toFixed(2)}%`);
            }

            // Calculate days to expiry
            const today = new Date();
            const expiry = new Date(contract.expiryDate);
            contract.daysToExpiry = Math.max(1, Math.ceil((expiry - today) / (1000 * 60 * 60 * 24)));

            if (!isNaN(contract.strike) && contract.strike > 0) {
                contracts.push(contract);
            }
        }

        return contracts;
    }
}
