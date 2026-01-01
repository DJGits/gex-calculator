// Visualization Engine using Plotly
class VisualizationEngine {
    createGammaExposureChart(gammaExposures, walls, currentPrice, title = 'Gamma Exposure by Strike') {
        const strikes = gammaExposures.map(ge => ge.strike);
        const netGamma = gammaExposures.map(ge => ge.netGamma);
        const callGamma = gammaExposures.map(ge => ge.callGamma);
        const putGamma = gammaExposures.map(ge => ge.putGamma);

        // Create bar colors based on positive/negative
        const colors = netGamma.map(g => g > 0 ? 'rgba(76, 175, 80, 0.7)' : 'rgba(244, 67, 54, 0.7)');

        const traces = [
            {
                x: strikes,
                y: netGamma,
                type: 'bar',
                name: 'Net Gamma',
                marker: {
                    color: colors
                },
                hovertemplate: '<b>Strike:</b> %{x}<br><b>Net Gamma:</b> %{y:,.0f}<extra></extra>'
            }
        ];

        // Add current price line
        traces.push({
            x: [currentPrice, currentPrice],
            y: [Math.min(...netGamma) * 1.1, Math.max(...netGamma) * 1.1],
            type: 'scatter',
            mode: 'lines',
            name: 'Current Price',
            line: {
                color: 'black',
                width: 2,
                dash: 'dash'
            },
            hovertemplate: '<b>Current Price:</b> $%{x:.2f}<extra></extra>'
        });

        // Add call walls
        if (walls.callWalls && walls.callWalls.length > 0) {
            walls.callWalls.forEach((wall, index) => {
                if (index < 3) { // Show top 3
                    traces.push({
                        x: [wall.strike, wall.strike],
                        y: [Math.min(...netGamma) * 1.1, Math.max(...netGamma) * 1.1],
                        type: 'scatter',
                        mode: 'lines',
                        name: `Call Wall #${wall.significanceRank}`,
                        line: {
                            color: 'rgba(244, 67, 54, 0.5)',
                            width: 2
                        },
                        hovertemplate: `<b>Call Wall #${wall.significanceRank}</b><br>Strike: %{x}<extra></extra>`
                    });
                }
            });
        }

        // Add put walls
        if (walls.putWalls && walls.putWalls.length > 0) {
            walls.putWalls.forEach((wall, index) => {
                if (index < 3) { // Show top 3
                    traces.push({
                        x: [wall.strike, wall.strike],
                        y: [Math.min(...netGamma) * 1.1, Math.max(...netGamma) * 1.1],
                        type: 'scatter',
                        mode: 'lines',
                        name: `Put Wall #${wall.significanceRank}`,
                        line: {
                            color: 'rgba(76, 175, 80, 0.5)',
                            width: 2
                        },
                        hovertemplate: `<b>Put Wall #${wall.significanceRank}</b><br>Strike: %{x}<extra></extra>`
                    });
                }
            });
        }

        const layout = {
            title: {
                text: title,
                font: { size: 20 }
            },
            xaxis: {
                title: 'Strike Price',
                gridcolor: '#e0e0e0'
            },
            yaxis: {
                title: 'Gamma Exposure',
                gridcolor: '#e0e0e0',
                tickformat: ',.0f'
            },
            hovermode: 'closest',
            showlegend: true,
            legend: {
                x: 1,
                y: 1,
                xanchor: 'right',
                bgcolor: 'rgba(255, 255, 255, 0.8)'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            margin: { t: 50, r: 50, b: 50, l: 80 }
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
        };

        Plotly.newPlot('gammaChart', traces, layout, config);
    }
}
