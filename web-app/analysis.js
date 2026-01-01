// Wall Analyzer
class WallAnalyzer {
    constructor(minSignificanceThreshold = 0.05) {
        this.minSignificanceThreshold = minSignificanceThreshold;
    }

    findCallWalls(gammaExposures, currentPrice, maxWalls = 5) {
        const callCandidates = gammaExposures
            .filter(ge => ge.callGamma < 0) // Negative exposure = resistance
            .map(ge => ({
                strike: ge.strike,
                exposure: Math.abs(ge.callGamma),
                rawExposure: ge.callGamma,
                distance: Math.abs(ge.strike - currentPrice)
            }))
            .sort((a, b) => b.exposure - a.exposure);

        if (callCandidates.length === 0) return [];

        const totalCallExposure = callCandidates.reduce((sum, c) => sum + c.exposure, 0);
        const threshold = totalCallExposure * this.minSignificanceThreshold;

        return callCandidates
            .filter(c => c.exposure >= threshold)
            .slice(0, maxWalls)
            .map((c, index) => ({
                strike: c.strike,
                exposureValue: c.rawExposure,
                wallType: 'call_wall',
                distanceFromSpot: c.distance,
                significanceRank: index + 1
            }));
    }

    findPutWalls(gammaExposures, currentPrice, maxWalls = 5) {
        const putCandidates = gammaExposures
            .filter(ge => ge.putGamma > 0) // Positive exposure = support
            .map(ge => ({
                strike: ge.strike,
                exposure: ge.putGamma,
                rawExposure: ge.putGamma,
                distance: Math.abs(ge.strike - currentPrice)
            }))
            .sort((a, b) => b.exposure - a.exposure);

        if (putCandidates.length === 0) return [];

        const totalPutExposure = putCandidates.reduce((sum, c) => sum + c.exposure, 0);
        const threshold = totalPutExposure * this.minSignificanceThreshold;

        return putCandidates
            .filter(c => c.exposure >= threshold)
            .slice(0, maxWalls)
            .map((c, index) => ({
                strike: c.strike,
                exposureValue: c.rawExposure,
                wallType: 'put_wall',
                distanceFromSpot: c.distance,
                significanceRank: index + 1
            }));
    }

    findAllWalls(gammaExposures, currentPrice, maxWallsPerType = 5) {
        return {
            callWalls: this.findCallWalls(gammaExposures, currentPrice, maxWallsPerType),
            putWalls: this.findPutWalls(gammaExposures, currentPrice, maxWallsPerType)
        };
    }
}

// Metrics Calculator
class MetricsCalculator {
    calculateAllMetrics(gammaExposures) {
        const totalNetGamma = gammaExposures.reduce((sum, ge) => sum + ge.netGamma, 0);
        const totalCallGamma = gammaExposures.reduce((sum, ge) => sum + ge.callGamma, 0);
        const totalPutGamma = gammaExposures.reduce((sum, ge) => sum + ge.putGamma, 0);
        
        // Gamma-weighted average strike
        const totalAbsGamma = gammaExposures.reduce((sum, ge) => sum + Math.abs(ge.netGamma), 0);
        const weightedStrike = gammaExposures.reduce((sum, ge) => 
            sum + (ge.strike * Math.abs(ge.netGamma)), 0) / totalAbsGamma;

        // Call/Put ratio
        const callPutRatio = Math.abs(totalCallGamma / totalPutGamma);

        // Max exposures
        const maxCallExposure = Math.min(...gammaExposures.map(ge => ge.callGamma));
        const maxPutExposure = Math.max(...gammaExposures.map(ge => ge.putGamma));

        // Standard deviation
        const mean = totalNetGamma / gammaExposures.length;
        const variance = gammaExposures.reduce((sum, ge) => 
            sum + Math.pow(ge.netGamma - mean, 2), 0) / gammaExposures.length;
        const stdDev = Math.sqrt(variance);

        return {
            totalNetGamma,
            totalCallGamma,
            totalPutGamma,
            gammaWeightedAvgStrike: weightedStrike,
            callPutGammaRatio: callPutRatio,
            maxCallExposure,
            maxPutExposure,
            gammaExposureStd: stdDev
        };
    }

    calculateGammaEnvironment(gammaExposures, currentPrice) {
        const metrics = this.calculateAllMetrics(gammaExposures);
        
        // Determine environment type
        const environment = metrics.totalNetGamma > 0 ? 'positive' : 
                          metrics.totalNetGamma < 0 ? 'negative' : 'neutral';

        // Calculate environment strength
        const totalOI = gammaExposures.reduce((sum, ge) => sum + ge.totalOI, 0);
        const strength = Math.abs(metrics.totalNetGamma) / (currentPrice * totalOI);

        // Strength interpretation
        let strengthLevel, strengthColor, volatilityImpact, description;
        
        if (strength >= 0.10) {
            strengthLevel = 'Very Strong';
            strengthColor = '🔴';
            volatilityImpact = 'Extreme impact expected';
            description = 'Dominant market maker forces with very high confidence in gamma effects';
        } else if (strength >= 0.05) {
            strengthLevel = 'Strong';
            strengthColor = '🟠';
            volatilityImpact = 'Significant impact expected';
            description = 'Strong gamma forces create meaningful price dynamics';
        } else if (strength >= 0.02) {
            strengthLevel = 'Moderate';
            strengthColor = '🟡';
            volatilityImpact = 'Noticeable impact';
            description = 'Moderate gamma influence alongside other market factors';
        } else if (strength >= 0.01) {
            strengthLevel = 'Weak';
            strengthColor = '🟢';
            volatilityImpact = 'Limited impact';
            description = 'Weak gamma forces, other factors likely more important';
        } else {
            strengthLevel = 'Very Weak';
            strengthColor = '⚪';
            volatilityImpact = 'Minimal impact';
            description = 'Minimal gamma influence on price action';
        }

        // Find gamma flip level
        let gammaFlipLevel = null;
        for (let i = 0; i < gammaExposures.length - 1; i++) {
            const current = gammaExposures[i];
            const next = gammaExposures[i + 1];
            
            if ((current.netGamma > 0 && next.netGamma < 0) ||
                (current.netGamma < 0 && next.netGamma > 0)) {
                gammaFlipLevel = (current.strike + next.strike) / 2;
                break;
            }
        }

        // Strike distribution
        const positiveStrikes = gammaExposures.filter(ge => ge.netGamma > 0).length;
        const negativeStrikes = gammaExposures.filter(ge => ge.netGamma < 0).length;
        const neutralStrikes = gammaExposures.filter(ge => ge.netGamma === 0).length;
        const totalStrikes = gammaExposures.length;

        // Environment description
        let envDescription;
        if (environment === 'positive') {
            envDescription = 'Market makers are net long gamma, providing price stability through mean-reverting hedging flows. Expect lower volatility and range-bound trading.';
        } else if (environment === 'negative') {
            envDescription = 'Market makers are net short gamma, amplifying price moves through momentum-reinforcing hedging flows. Expect higher volatility and trending behavior.';
        } else {
            envDescription = 'Balanced gamma exposure with mixed market maker positioning. Moderate volatility expected with no clear directional bias.';
        }

        return {
            environment,
            environmentStrength: strength,
            strengthInterpretation: {
                level: strengthLevel,
                color: strengthColor,
                volatilityImpact,
                description
            },
            gammaFlipLevel,
            description: envDescription,
            positiveStrikes,
            negativeStrikes,
            neutralStrikes,
            positiveStrikePercentage: (positiveStrikes / totalStrikes) * 100,
            negativeStrikePercentage: (negativeStrikes / totalStrikes) * 100
        };
    }
}
