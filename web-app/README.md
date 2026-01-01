# Gamma Exposure Calculator - Web Application

A fully client-side JavaScript implementation of the Gamma Exposure Calculator that runs entirely in the browser with no backend required.

## Features

- ✅ **100% Client-Side**: All calculations run in the browser
- ✅ **No Backend Required**: Pure HTML/CSS/JavaScript
- ✅ **Real-Time Analysis**: Instant gamma exposure calculations
- ✅ **Interactive Visualizations**: Plotly.js charts with gamma walls
- ✅ **Expected Move Calculator**: IV-based price range predictions
- ✅ **Strategy Recommendations**: Environment-specific trading strategies
- ✅ **Sample Data Generator**: Built-in synthetic data for testing
- ✅ **CSV Upload**: Import your own options data
- ✅ **Responsive Design**: Works on desktop and mobile

## Quick Start

### Option 1: Open Directly in Browser
1. Download all files in the `web-app` folder
2. Open `index.html` in your web browser
3. Click "Generate Sample Data" to start analyzing

### Option 2: Use a Local Server
```bash
# Using Python
cd web-app
python -m http.server 8000

# Using Node.js
npx http-server web-app -p 8000

# Then open http://localhost:8000 in your browser
```

## File Structure

```
web-app/
├── index.html              # Main HTML structure
├── styles.css              # All styling
├── app.js                  # Main application logic
├── calculations.js         # Black-Scholes & gamma calculations
├── analysis.js             # Wall analysis & metrics
├── visualization.js        # Plotly chart generation
├── strategies.js           # Strategy recommendations
└── README.md              # This file
```

## How to Use

### 1. Generate Sample Data
- Click the "Sample Data" tab
- Adjust number of strikes and days to expiry
- Click "Generate Sample Data"
- Analysis runs automatically

### 2. Upload CSV File
- Click the "Upload File" tab
- Select a CSV file with columns:
  - `strike`: Strike price
  - `expiry_date`: Expiration date
  - `option_type`: 'call' or 'put'
  - `open_interest`: Open interest
  - `implied_volatility`: IV (optional)
  - `volume`, `bid`, `ask`, `last_price` (optional)

### 3. Adjust Parameters
- **Current Price**: Set the underlying asset price
- **Risk-Free Rate**: Adjust for calculations (default 5%)

### 4. View Analysis
- **Gamma Environment**: Positive/Negative/Neutral classification
- **Key Metrics**: Net gamma, weighted strike, call/put ratio
- **Expected Move**: IV-based price range predictions (1SD and 2SD)
- **Gamma Walls**: Support and resistance levels
- **Interactive Chart**: Visualize gamma exposure by strike
- **Strategy Recommendations**: Tailored trading strategies

## Technical Details

### Calculations Performed

#### Black-Scholes Gamma
```javascript
Gamma = N'(d1) / (S × σ × √T)
```
Where:
- N'(d1) = Normal probability density function
- S = Spot price
- σ = Implied volatility
- T = Time to expiration

#### Gamma Exposure
```javascript
Gamma Exposure = Gamma × Open Interest × 100 × S²
```

#### Market Maker Perspective
- **Short Calls**: Negative gamma exposure (resistance)
- **Short Puts**: Positive gamma exposure (support)

### Environment Classification

**Positive Gamma**: Total net gamma > 0
- Market makers provide stability
- Mean-reverting price action
- Lower volatility expected

**Negative Gamma**: Total net gamma < 0
- Market makers amplify moves
- Momentum/trending behavior
- Higher volatility expected

**Neutral Gamma**: Total net gamma ≈ 0
- Balanced forces
- Mixed market dynamics

### Strength Calculation
```javascript
Strength = |Total Net Gamma| / (Current Price × Total Open Interest)
```

Levels:
- **Very Strong**: ≥ 0.10
- **Strong**: 0.05 - 0.10
- **Moderate**: 0.02 - 0.05
- **Weak**: 0.01 - 0.02
- **Very Weak**: < 0.01

### Expected Move Calculation
```javascript
Expected Move = Current Price × Implied Volatility × √(Days to Expiry / 365)
```

**IV Method (Improved):**
- Uses **ATM (At-The-Money) IV** for accuracy
- Averages IV from 10 contracts closest to current price
- Excludes far OTM options with inflated IV (skew)
- Professional standard used by real traders

Provides:
- **1 Standard Deviation**: ~68% probability range
- **2 Standard Deviations**: ~95% probability range
- **ATM IV vs Overall IV**: Comparison for transparency
- **Strategy Suggestions**: Based on expected price movement
- **IV Assessment**: High/Moderate/Low classification

## Limitations

### Yahoo Finance Integration
Due to browser CORS (Cross-Origin Resource Sharing) restrictions, direct Yahoo Finance API calls are not possible from client-side JavaScript. To fetch live data, you would need:

1. **Backend Proxy**: Set up a server to proxy Yahoo Finance requests
2. **CORS Proxy Service**: Use a third-party CORS proxy (not recommended for production)
3. **Browser Extension**: Install a CORS-disabling extension (development only)

For demonstration purposes, use the **Sample Data** generator or **CSV Upload** features.

### Alternative: Add Backend Support

To enable Yahoo Finance integration, create a simple backend:

**Python Flask Example:**
```python
from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf

app = Flask(__name__)
CORS(app)

@app.route('/api/options/<symbol>')
def get_options(symbol):
    ticker = yf.Ticker(symbol)
    # ... fetch and return options data
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=5000)
```

Then update `app.js` to call `http://localhost:5000/api/options/SPY`

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

Requires:
- ES6+ JavaScript support
- Plotly.js (loaded from CDN)

## Performance

- **Sample Data Generation**: < 100ms for 50 strikes
- **Gamma Calculations**: < 200ms for 1000 contracts
- **Chart Rendering**: < 500ms
- **Total Analysis Time**: < 1 second

## Customization

### Modify Sample Data
Edit `calculations.js` → `DataGenerator.generateSampleData()`:
```javascript
// Adjust strike spacing
const strikeSpacing = spotPrice * 0.02; // 2% spacing

// Adjust open interest range
openInterest: Math.floor(Math.random() * 10000 + 1000)

// Adjust IV range
impliedVolatility: Math.random() * 0.3 + 0.15 // 15-45%
```

### Customize Strategies
Edit `strategies.js` → `StrategyEngine` methods to add/modify recommendations.

### Change Chart Appearance
Edit `visualization.js` → `createGammaExposureChart()` layout options.

## Deployment

### GitHub Pages
1. Push the `web-app` folder to a GitHub repository
2. Enable GitHub Pages in repository settings
3. Set source to the `web-app` folder
4. Access at `https://yourusername.github.io/repo-name/`

### Netlify/Vercel
1. Drag and drop the `web-app` folder
2. Instant deployment with custom domain support

### Static Hosting
Upload all files to any static hosting service:
- AWS S3 + CloudFront
- Google Cloud Storage
- Azure Static Web Apps
- Cloudflare Pages

## Comparison with Python Version

| Feature | Python (Streamlit) | JavaScript (Web) |
|---------|-------------------|------------------|
| **Backend Required** | Yes (Python) | No |
| **Yahoo Finance** | ✅ Direct | ❌ Needs proxy |
| **Calculations** | NumPy/SciPy | Pure JavaScript |
| **Charts** | Plotly Python | Plotly.js |
| **Deployment** | Server required | Static hosting |
| **Performance** | Faster (NumPy) | Fast enough |
| **Offline Use** | No | Yes (after load) |
| **Mobile** | Limited | Responsive |

## Future Enhancements

Potential additions:
- [ ] IndexedDB for data persistence
- [ ] Web Workers for heavy calculations
- [ ] PWA support for offline use
- [ ] Export to PDF/Excel
- [ ] Multiple symbol comparison
- [ ] Historical analysis
- [ ] Real-time updates (with WebSocket backend)
- [ ] Advanced charting options

## License

Same as parent project.

## Support

For issues or questions:
1. Check browser console for errors
2. Verify CSV file format
3. Try sample data first
4. Ensure JavaScript is enabled

## Credits

- **Plotly.js**: Interactive charting library
- **Black-Scholes Model**: Options pricing mathematics
- **Original Python Version**: Feature parity maintained
