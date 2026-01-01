// Strategy Recommendations Engine
class StrategyEngine {
    generateRecommendations(gammaEnv, walls, currentPrice) {
        const { environment, strengthInterpretation } = gammaEnv;
        
        let html = '<div class="strategy-overview">';
        
        // Environment overview
        html += '<div class="metrics-row">';
        html += '<div class="metric large">';
        html += `<span class="metric-label">Environment</span>`;
        html += `<span class="metric-value">${environment.toUpperCase()}</span>`;
        html += '</div>';
        html += '<div class="metric large">';
        html += `<span class="metric-label">Strength</span>`;
        html += `<span class="metric-value">${strengthInterpretation.color} ${strengthInterpretation.level}</span>`;
        html += '</div>';
        html += '<div class="metric large">';
        html += `<span class="metric-label">Confidence</span>`;
        html += `<span class="metric-value">${this.getConfidenceLevel(strengthInterpretation.level)}</span>`;
        html += '</div>';
        html += '</div>';

        html += `<div class="alert alert-info">${gammaEnv.description}</div>`;
        html += '</div>';

        // Strategy tabs
        if (environment === 'positive') {
            html += this.generatePositiveGammaStrategies(walls, currentPrice, strengthInterpretation);
        } else if (environment === 'negative') {
            html += this.generateNegativeGammaStrategies(walls, currentPrice, strengthInterpretation, gammaEnv);
        } else {
            html += this.generateNeutralGammaStrategies(walls, currentPrice, strengthInterpretation);
        }

        return html;
    }

    getConfidenceLevel(strengthLevel) {
        if (['Very Strong', 'Strong'].includes(strengthLevel)) return 'HIGH';
        if (strengthLevel === 'Moderate') return 'MODERATE';
        return 'LOW';
    }

    generatePositiveGammaStrategies(walls, currentPrice, strength) {
        let html = '<div class="strategy-content">';
        
        html += '<h3>🎯 Recommended Strategies for Positive Gamma</h3>';
        html += '<div class="alert alert-success">EXCELLENT ENVIRONMENT for premium collection and mean reversion strategies</div>';

        // Covered Calls
        html += '<div class="strategy-item">';
        html += '<h4>📈 Covered Calls</h4>';
        html += '<div class="rating">⭐⭐⭐⭐⭐ HIGHLY RECOMMENDED</div>';
        html += '<div class="strategy-grid">';
        html += '<div class="strategy-section">';
        html += '<h5>✅ Why It Works:</h5>';
        html += '<ul>';
        html += '<li>Mean-reverting environment limits upside</li>';
        html += '<li>Lower volatility increases time decay</li>';
        html += '<li>Call walls provide natural resistance</li>';
        html += '<li>High probability of calls expiring worthless</li>';
        html += '</ul>';
        html += '</div>';
        html += '<div class="strategy-section">';
        html += '<h5>📊 Risk/Reward:</h5>';
        if (['Very Strong', 'Strong'].includes(strength.level)) {
            html += '<p><strong>Risk:</strong> LOW | <strong>Reward:</strong> MODERATE-HIGH</p>';
            html += '<p>Strike Selection: 1-3% OTM (aggressive)</p>';
        } else {
            html += '<p><strong>Risk:</strong> MODERATE | <strong>Reward:</strong> MODERATE</p>';
            html += '<p>Strike Selection: 2-5% OTM (standard)</p>';
        }
        html += '</div>';
        html += '</div>';

        // Show call walls if available
        if (walls.callWalls && walls.callWalls.length > 0) {
            html += '<div class="strategy-section">';
            html += '<h5>🎯 Suggested Strikes (based on call walls):</h5>';
            html += '<ul>';
            walls.callWalls.slice(0, 3).forEach(wall => {
                const distancePct = ((wall.strike - currentPrice) / currentPrice) * 100;
                if (distancePct > 0 && distancePct <= 5) {
                    html += `<li><strong>${wall.strike.toFixed(0)}</strong> (+${distancePct.toFixed(1)}%) - Strong resistance</li>`;
                }
            });
            html += '</ul>';
            html += '</div>';
        }
        html += '</div>';

        // Cash-Secured Puts
        html += '<div class="strategy-item">';
        html += '<h4>💰 Cash-Secured Puts</h4>';
        html += '<div class="rating">⭐⭐⭐⭐ RECOMMENDED</div>';
        html += '<div class="strategy-grid">';
        html += '<div class="strategy-section">';
        html += '<h5>✅ Why It Works:</h5>';
        html += '<ul>';
        html += '<li>Put walls provide strong support</li>';
        html += '<li>Mean reversion protects downside</li>';
        html += '<li>Good entry strategy for long positions</li>';
        html += '<li>Collect premium while waiting to buy</li>';
        html += '</ul>';
        html += '</div>';
        html += '<div class="strategy-section">';
        html += '<h5>📊 Risk/Reward:</h5>';
        html += '<p><strong>Risk:</strong> MODERATE | <strong>Reward:</strong> MODERATE</p>';
        html += '<p>Strike Selection: At or slightly below put walls</p>';
        html += '</div>';
        html += '</div>';
        html += '</div>';

        // Iron Condors
        html += '<div class="strategy-item">';
        html += '<h4>🦅 Iron Condors</h4>';
        html += '<div class="rating">⭐⭐⭐⭐ RECOMMENDED</div>';
        html += '<p>Sell OTM call spread + OTM put spread to profit from range-bound price action</p>';
        html += '<p><strong>Risk:</strong> MODERATE | <strong>Reward:</strong> MODERATE</p>';
        html += '</div>';

        // Strategies to Avoid
        html += '<div class="strategy-item" style="border-left-color: #f44336;">';
        html += '<h4>❌ Strategies to Avoid</h4>';
        html += '<ul>';
        html += '<li><strong>Long Volatility Plays:</strong> Volatility likely to decrease</li>';
        html += '<li><strong>Momentum/Breakout Trades:</strong> Mean reversion fights momentum</li>';
        html += '</ul>';
        html += '</div>';

        html += '</div>';
        return html;
    }

    generateNegativeGammaStrategies(walls, currentPrice, strength, gammaEnv) {
        let html = '<div class="strategy-content">';
        
        html += '<h3>⚡ Recommended Strategies for Negative Gamma</h3>';
        html += '<div class="alert alert-warning">HIGH VOLATILITY ENVIRONMENT - Focus on momentum and protection</div>';

        // Breakout Trading
        html += '<div class="strategy-item">';
        html += '<h4>🚀 Breakout Trading</h4>';
        html += '<div class="rating">⭐⭐⭐⭐⭐ HIGHLY RECOMMENDED</div>';
        html += '<div class="strategy-grid">';
        html += '<div class="strategy-section">';
        html += '<h5>✅ Why It Works:</h5>';
        html += '<ul>';
        html += '<li>Market makers amplify moves</li>';
        html += '<li>Momentum accelerates on breaks</li>';
        html += '<li>Trending environment expected</li>';
        html += '<li>Follow the flow, don\'t fight it</li>';
        html += '</ul>';
        html += '</div>';
        html += '<div class="strategy-section">';
        html += '<h5>📊 Risk/Reward:</h5>';
        if (['Very Strong', 'Strong'].includes(strength.level)) {
            html += '<p><strong>Risk:</strong> MODERATE | <strong>Reward:</strong> HIGH</p>';
        } else {
            html += '<p><strong>Risk:</strong> MODERATE-HIGH | <strong>Reward:</strong> MODERATE-HIGH</p>';
        }
        html += '</div>';
        html += '</div>';

        if (gammaEnv.gammaFlipLevel) {
            const flipDistance = gammaEnv.gammaFlipLevel - currentPrice;
            html += '<div class="strategy-section">';
            html += `<h5>🎯 Key Level to Watch: ${gammaEnv.gammaFlipLevel.toFixed(0)}</h5>`;
            if (flipDistance > 0) {
                html += `<p>Breakout above ${gammaEnv.gammaFlipLevel.toFixed(0)} could accelerate upward momentum</p>`;
            } else {
                html += `<p>Breakdown below ${gammaEnv.gammaFlipLevel.toFixed(0)} could accelerate downward momentum</p>`;
            }
            html += '</div>';
        }
        html += '</div>';

        // Long Straddles/Strangles
        html += '<div class="strategy-item">';
        html += '<h4>🌪️ Long Straddles/Strangles</h4>';
        html += '<div class="rating">⭐⭐⭐⭐ RECOMMENDED</div>';
        html += '<p>Buy ATM call + ATM put to profit from volatility expansion</p>';
        html += '<p><strong>Risk:</strong> MODERATE (premium paid) | <strong>Reward:</strong> HIGH</p>';
        html += '</div>';

        // Protective Puts
        html += '<div class="strategy-item" style="border-left-color: #f44336;">';
        html += '<h4>🛡️ Protective Puts - ESSENTIAL</h4>';
        html += '<div class="rating">⭐⭐⭐⭐⭐ CRITICAL</div>';
        html += '<p><strong>High risk of sharp moves - protection is mandatory</strong></p>';
        html += '<ul>';
        html += '<li>Strike: 5-10% OTM</li>';
        html += '<li>Consider this essential insurance</li>';
        html += '<li>Downside can accelerate quickly</li>';
        html += '</ul>';
        html += '</div>';

        // Strategies to Avoid
        html += '<div class="strategy-item" style="border-left-color: #f44336;">';
        html += '<h4>❌ Strategies to Avoid</h4>';
        html += '<ul>';
        html += '<li><strong>Covered Calls:</strong> High assignment risk in momentum environment</li>';
        html += '<li><strong>Short Premium:</strong> Volatility expansion works against you</li>';
        html += '<li><strong>Mean Reversion:</strong> Trends can persist longer than expected</li>';
        html += '</ul>';
        html += '</div>';

        html += '</div>';
        return html;
    }

    generateNeutralGammaStrategies(walls, currentPrice, strength) {
        let html = '<div class="strategy-content">';
        
        html += '<h3>⚖️ Recommended Strategies for Neutral Gamma</h3>';
        html += '<div class="alert alert-info">BALANCED APPROACH - Use standard strategies with normal risk management</div>';

        html += '<div class="strategy-item">';
        html += '<h4>🎯 Diversified Options Portfolio</h4>';
        html += '<div class="rating">⭐⭐⭐⭐ RECOMMENDED</div>';
        html += '<div class="strategy-section">';
        html += '<h5>Recommended Mix:</h5>';
        html += '<ul>';
        html += '<li>40% Premium selling (covered calls, CSPs)</li>';
        html += '<li>30% Directional (calls/puts)</li>';
        html += '<li>20% Spreads (verticals, iron condors)</li>';
        html += '<li>10% Protection (hedges)</li>';
        html += '</ul>';
        html += '</div>';
        html += '</div>';

        html += '<div class="strategy-item">';
        html += '<h4>⚠️ Risk Management Focus</h4>';
        html += '<ul>';
        html += '<li>Monitor gamma shifts daily</li>';
        html += '<li>Use smaller position sizes</li>';
        html += '<li>Maintain higher cash reserves</li>';
        html += '<li>Be ready to pivot quickly</li>';
        html += '</ul>';
        html += '</div>';

        html += '</div>';
        return html;
    }
}
