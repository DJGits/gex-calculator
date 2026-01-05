# Gamma Exposure Calculator

A comprehensive Streamlit web application for calculating and visualizing gamma exposure metrics for options trading. Now supports **any stock ticker** with options data!

## Features

### 📊 Core Functionality
- **Gamma Exposure Calculations**: Uses Black-Scholes model for accurate gamma calculations
- **Wall Analysis**: Identifies call walls (resistance) and put walls (support) levels
- **Market Metrics**: Comprehensive statistics including net gamma, weighted averages, and ratios
- **Interactive Visualizations**: Multiple chart types with Plotly integration
- **Universal Ticker Support**: Analyze any stock, ETF, or index with options data

### 📁 Data Input
- **Yahoo Finance Integration**: Download live options chain data for **any ticker symbol**
- **Popular Symbols**: Quick access to SPY, QQQ, AAPL, TSLA, NVDA, and more
- **Custom Tickers**: Enter any valid ticker symbol (e.g., AMD, NFLX, DIS, BA)
- **File Upload**: Support for CSV and Excel files with options chain data
- **Sample Data Generation**: Built-in synthetic data generator for testing
- **Data Validation**: Comprehensive validation with user-friendly error messages

### 🌐 Yahoo Finance Features
- **Real-time Data**: Fetch live options chains for any symbol with options
- **Current Prices**: Automatic retrieval of current underlying prices
- **Multiple Expirations**: Support for single or multiple expiration dates
- **Comprehensive Coverage**: Access to calls, puts, strikes, open interest, and implied volatility
- **Symbol Validation**: Automatic checking if ticker has options available

### 📈 Analysis Features
- **Call/Put Breakdown**: Separate analysis of call and put gamma exposures
- **Wall Identification**: Automatic detection of significant support/resistance levels
- **Statistical Metrics**: Mean, standard deviation, percentiles, and concentration measures
- **Real-time Updates**: Dynamic recalculation based on current market price

### 📊 Visualizations
- **Net Gamma Exposure Chart**: Bar chart showing gamma by strike price
- **Call vs Put Breakdown**: Stacked visualization of call and put exposures
- **Comprehensive Analysis**: Combined chart with wall highlights
- **Metrics Dashboard**: Summary statistics and key indicators

### 💾 Export Capabilities
- **CSV Export**: Download gamma exposures, walls, and metrics data
- **Chart Export**: Save visualizations as PNG images
- **Comprehensive Packages**: Complete analysis export with metadata

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd spx-gamma-exposure-calculator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: The app now includes `yfinance` for live data fetching. If you encounter any issues with yfinance installation, you can still use the file upload and sample data features.

3. Run the application:
```bash
streamlit run app.py
```

## Usage

### Quick Start
1. **Launch the app**: Run `streamlit run app.py`
2. **Choose data source**: 
   - **Yahoo Finance**: Select a symbol (SPY, QQQ, etc.) and fetch live data
   - **File Upload**: Upload your CSV/Excel options chain file
   - **Sample Data**: Generate synthetic data for testing
3. **Set parameters**: Adjust current price and risk-free rate in the sidebar
4. **Analyze**: View gamma exposures, walls, and metrics automatically calculated
5. **Visualize**: Explore different chart types and interactive features
6. **Export**: Download results in CSV format or save charts as images

### Yahoo Finance Integration
The app now supports fetching live options data directly from Yahoo Finance for **any ticker symbol**:

**Popular Pre-configured Symbols:**
- **SPY**: SPDR S&P 500 ETF (most liquid SPX proxy)
- **QQQ**: Invesco QQQ Trust (Nasdaq-100)
- **IWM**: iShares Russell 2000 ETF
- **DIA**: Dow Jones Industrial Average ETF
- **SPX**: S&P 500 Index (^SPX)
- **VIX**: CBOE Volatility Index (^VIX)
- **AAPL**: Apple Inc.
- **MSFT**: Microsoft Corporation
- **TSLA**: Tesla Inc.
- **NVDA**: NVIDIA Corporation
- **AMZN**: Amazon.com Inc.
- **GOOGL**: Alphabet Inc.
- **META**: Meta Platforms Inc.

**Custom Ticker Support:**
- Enter **any valid ticker symbol** (e.g., AMD, NFLX, DIS, BA, JPM, etc.)
- Automatic validation checks if options data is available
- Works with stocks, ETFs, and indices
- Supports thousands of optionable securities

**Features:**
- Real-time current prices
- Multiple expiration date selection
- Automatic data validation and cleaning
- Live open interest and implied volatility data
- Symbol validation before fetching

### Data Format
Your options chain data should include these columns:
- `strike`: Strike price of the option
- `expiry_date`: Expiration date
- `option_type`: 'call' or 'put'
- `open_interest`: Number of open contracts
- `implied_volatility`: Implied volatility (optional, defaults to 20%)

Optional columns:
- `symbol`: Option symbol (defaults to 'SPX')
- `volume`: Trading volume
- `bid`, `ask`, `last_price`: Price information

### Key Metrics Explained

#### Gamma Exposure
- **Positive values**: Indicate support levels (put walls)
- **Negative values**: Indicate resistance levels (call walls)
- **Magnitude**: Shows the strength of the support/resistance

#### Walls
- **Call Walls**: Strikes with large negative gamma exposure (resistance)
- **Put Walls**: Strikes with large positive gamma exposure (support)
- **Significance Rank**: Ordered by exposure magnitude

#### Market Metrics
- **Total Net Gamma**: Sum of all gamma exposures
- **Gamma Weighted Average Strike**: Average strike weighted by gamma exposure
- **Call/Put Ratio**: Ratio of call to put gamma exposures

## Technical Details

### Architecture
- **Data Layer**: Handles options data processing and validation
- **Calculation Engine**: Black-Scholes gamma calculations
- **Analysis Module**: Wall identification and metrics computation
- **Visualization Layer**: Interactive Plotly charts
- **Export Module**: CSV and image export functionality

### Key Components
- `OptionsDataProcessor`: Data loading and validation
- `GammaCalculator`: Black-Scholes gamma calculations
- `WallAnalyzer`: Support/resistance level identification
- `MetricsCalculator`: Statistical analysis and metrics
- `VisualizationEngine`: Interactive chart generation
- `ExportManager`: Data export functionality

### Error Handling
- Comprehensive validation of input data
- User-friendly error messages
- Graceful degradation for edge cases
- Detailed logging for debugging

## Configuration

### Default Settings
- Risk-free rate: 5%
- Contract multiplier: 100 (SPX standard)
- Default volatility: 20% (when not provided)
- Chart dimensions: 1000x600 pixels

### Customization
Modify `config.py` to adjust:
- Chart colors and styling
- Calculation parameters
- File size limits
- Supported file types

## Performance

- **Processing Speed**: Handles 25+ strikes in <5ms
- **Memory Efficient**: Optimized for large options chains
- **Real-time Updates**: Instant recalculation on parameter changes
- **Scalable**: Tested with 100+ strike prices

## Troubleshooting

### Common Issues
1. **File Upload Errors**: Ensure CSV/Excel format with required columns
2. **Calculation Errors**: Check that strike prices and dates are valid
3. **Visualization Issues**: Verify data contains non-zero gamma exposures
4. **Export Problems**: Ensure sufficient disk space for large datasets

### Data Quality
- Remove expired options before analysis
- Ensure positive strike prices and open interest
- Verify expiration dates are in the future
- Check implied volatility values are reasonable (0.01-2.0)

## Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[CLI Usage Guide](docs/CLI_USAGE.md)** - Command-line tools and usage examples
- **[Gamma Exposure Guide](docs/GAMMA_EXPOSURE_GUIDE.md)** - Understanding gamma exposure and market dynamics
- **[Expected Move Guide](docs/EXPECTED_MOVE_GUIDE.md)** - Expected move calculations and trading implications
- **[Debug and Testing](docs/DEBUG_AND_TESTING.md)** - Debug modes, test scripts, and troubleshooting
- **[Technical Details](docs/TECHNICAL_DETAILS.md)** - Formulas, IV processing, and implementation notes
- **[Download Options Usage](docs/DOWNLOAD_OPTIONS_USAGE.md)** - Options chain downloader utility
- **[Implied Volatility Explained](docs/IMPLIED_VOLATILITY_EXPLAINED.md)** - IV sourcing and processing
- **[Strategy Recommendations](docs/STRATEGY_RECOMMENDATIONS_FEATURE.md)** - Trading strategies based on gamma environment
- **[Ticker Support Update](docs/TICKER_SUPPORT_UPDATE.md)** - Universal ticker support documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes only. It should not be used as the sole basis for trading decisions. Options trading involves significant risk and may not be suitable for all investors.