# Options Chain Downloader Utility

A simple Python script to download options chain data from Yahoo Finance and save it to CSV format.

## Features

- ✅ Download options data for any symbol
- ✅ Choose specific expiration dates
- ✅ List available expirations
- ✅ Interactive mode for expiration selection
- ✅ Auto-generated or custom filenames
- ✅ Clean, standardized CSV output
- ✅ Summary statistics display

## Installation

Requires Python 3.6+ and yfinance:

```bash
pip install yfinance pandas
```

## Usage

### Basic Usage

```bash
# Download nearest expiration for SPY
python download_options.py SPY

# Download specific expiration
python download_options.py SPY 2025-01-17

# Download for any stock
python download_options.py AAPL
python download_options.py TSLA 2025-02-21
python download_options.py NVDA
```

### List Available Expirations

```bash
# List all available expiration dates
python download_options.py SPY --list
python download_options.py AAPL -l
```

Output:
```
📅 Available expiration dates for SPY:
--------------------------------------------------
 1. 2025-01-03
 2. 2025-01-06
 3. 2025-01-08
 4. 2025-01-10
 5. 2025-01-13
...
```

### Interactive Mode

```bash
# Interactive expiration selection
python download_options.py SPY --interactive
python download_options.py AAPL -i
```

The script will:
1. Show all available expirations
2. Prompt you to select one
3. Download the selected expiration

### Custom Output Filename

```bash
# Specify output filename
python download_options.py SPY 2025-01-17 --output spy_jan_options.csv
python download_options.py AAPL -o aapl_options.csv
```

### Help

```bash
python download_options.py --help
```

## Output Format

The script generates a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| `symbol` | Stock symbol (e.g., SPY) |
| `strike` | Strike price |
| `expiry_date` | Expiration date (YYYY-MM-DD) |
| `option_type` | 'call' or 'put' |
| `last_price` | Last traded price |
| `bid` | Bid price |
| `ask` | Ask price |
| `volume` | Trading volume |
| `open_interest` | Open interest |
| `implied_volatility` | Implied volatility (decimal) |

### Example Output

```csv
symbol,strike,expiry_date,option_type,last_price,bid,ask,volume,open_interest,implied_volatility
SPY,450.0,2025-01-17,call,8.25,8.20,8.30,1250,15420,0.185
SPY,450.0,2025-01-17,put,2.15,2.10,2.20,890,12350,0.172
SPY,455.0,2025-01-17,call,5.50,5.45,5.55,2100,18900,0.178
SPY,455.0,2025-01-17,put,3.25,3.20,3.30,1450,14200,0.165
...
```

## Output Filename

If no output filename is specified, the script auto-generates one:

```
{SYMBOL}_{EXPIRATION}_{TIMESTAMP}.csv
```

Example: `SPY_2025-01-17_20250101_143052.csv`

## Example Sessions

### Example 1: Quick Download

```bash
$ python download_options.py SPY

📊 Downloading options chain for SPY...
📅 Using nearest expiration: 2025-01-03
⏳ Fetching options data...

✅ Successfully downloaded options chain!
📁 Saved to: SPY_2025-01-03_20250101_143052.csv

📊 Summary:
   Symbol: SPY
   Current Price: $582.45
   Expiration: 2025-01-03
   Total Contracts: 1,248
   Calls: 624
   Puts: 624
   Unique Strikes: 312
   Total Open Interest: 1,245,680
   Strike Range: 450 - 650

📋 Sample Data (first 5 rows):
symbol  strike  expiry_date  option_type  last_price   bid   ask  volume  open_interest  implied_volatility
   SPY   450.0   2025-01-03         call       132.5  132.0  133.0      10            125              0.1850
   SPY   450.0   2025-01-03          put         0.01  0.00  0.01       5             50              0.2100
   SPY   455.0   2025-01-03         call       127.5  127.0  128.0      15            180              0.1820
   SPY   455.0   2025-01-03          put         0.02  0.01  0.02       8             75              0.2050
   SPY   460.0   2025-01-03         call       122.5  122.0  123.0      20            220              0.1790
```

### Example 2: Interactive Selection

```bash
$ python download_options.py AAPL --interactive

📅 Available expiration dates for AAPL:
--------------------------------------------------
 1. 2025-01-03
 2. 2025-01-10
 3. 2025-01-17
 4. 2025-01-24
 5. 2025-01-31
 6. 2025-02-07
 7. 2025-02-14
 8. 2025-02-21
--------------------------------------------------

Select expiration (1-8) or press Enter for nearest: 3

📊 Downloading options chain for AAPL...
⏳ Fetching options data...

✅ Successfully downloaded options chain!
📁 Saved to: AAPL_2025-01-17_20250101_143215.csv
...
```

### Example 3: Specific Expiration with Custom Filename

```bash
$ python download_options.py TSLA 2025-02-21 --output tesla_feb_options.csv

📊 Downloading options chain for TSLA...
⏳ Fetching options data...

✅ Successfully downloaded options chain!
📁 Saved to: tesla_feb_options.csv

📊 Summary:
   Symbol: TSLA
   Current Price: $387.25
   Expiration: 2025-02-21
   Total Contracts: 2,156
   Calls: 1,078
   Puts: 1,078
   Unique Strikes: 539
   Total Open Interest: 2,458,920
   Strike Range: 200 - 600
...
```

## Use Cases

### 1. Data Collection for Analysis
Download options data to analyze with the Gamma Exposure Calculator:

```bash
python download_options.py SPY 2025-01-17
# Upload the CSV to the web app or Streamlit app
```

### 2. Historical Data Archiving
Download and archive options data regularly:

```bash
# Daily download script
python download_options.py SPY --output data/spy_$(date +%Y%m%d).csv
python download_options.py QQQ --output data/qqq_$(date +%Y%m%d).csv
```

### 3. Multiple Expirations
Download several expirations for comparison:

```bash
python download_options.py SPY 2025-01-17 -o spy_jan17.csv
python download_options.py SPY 2025-02-21 -o spy_feb21.csv
python download_options.py SPY 2025-03-21 -o spy_mar21.csv
```

### 4. Batch Processing
Create a script to download multiple symbols:

```bash
#!/bin/bash
for symbol in SPY QQQ IWM DIA AAPL MSFT TSLA NVDA; do
    python download_options.py $symbol
done
```

## Integration with Gamma Calculator

### Streamlit App
1. Download options data: `python download_options.py SPY`
2. Run Streamlit app: `streamlit run app.py`
3. Upload the CSV file in the "Upload File" tab

### Web App
1. Download options data: `python download_options.py AAPL`
2. Open `web-app/index.html` in browser
3. Click "Upload File" tab and select the CSV

## Error Handling

The script handles common errors gracefully:

```bash
# Invalid symbol
$ python download_options.py INVALID
❌ No options available for INVALID

# Invalid expiration
$ python download_options.py SPY 2025-99-99
❌ Expiration 2025-99-99 not available
Available expirations: 2025-01-03, 2025-01-06, 2025-01-08...

# Network error
$ python download_options.py SPY
❌ Error downloading options chain: HTTPError...
```

## Tips

### 1. Check Available Expirations First
```bash
python download_options.py SPY --list
```

### 2. Use Interactive Mode for Exploration
```bash
python download_options.py AAPL -i
```

### 3. Organize Downloaded Files
```bash
mkdir -p options_data
python download_options.py SPY -o options_data/spy_latest.csv
```

### 4. Automate with Cron (Linux/Mac)
```bash
# Download SPY options daily at 4:30 PM
30 16 * * 1-5 cd /path/to/project && python download_options.py SPY
```

### 5. Automate with Task Scheduler (Windows)
Create a batch file:
```batch
@echo off
cd C:\path\to\project
python download_options.py SPY
```

Schedule it to run daily after market close.

## Troubleshooting

### Issue: "No module named 'yfinance'"
**Solution**: Install yfinance
```bash
pip install yfinance
```

### Issue: "No options available"
**Solution**: 
- Check if the symbol is correct
- Verify the symbol has options (not all stocks do)
- Try a different symbol like SPY or AAPL

### Issue: Empty or incomplete data
**Solution**:
- Yahoo Finance may be experiencing issues
- Try again in a few minutes
- Check your internet connection

### Issue: Slow download
**Solution**:
- Normal for symbols with many strikes
- Yahoo Finance API can be slow during market hours
- Consider downloading after market close

## Advanced Usage

### Python Script Integration

```python
from download_options import download_options_chain

# Download programmatically
csv_file = download_options_chain('SPY', '2025-01-17', 'spy_options.csv')

if csv_file:
    print(f"Downloaded to {csv_file}")
    # Process the CSV file
    import pandas as pd
    df = pd.read_csv(csv_file)
    # ... your analysis code
```

### Batch Download Script

```python
#!/usr/bin/env python3
import sys
from download_options import download_options_chain

symbols = ['SPY', 'QQQ', 'IWM', 'DIA', 'AAPL', 'MSFT', 'TSLA', 'NVDA']

for symbol in symbols:
    print(f"\nDownloading {symbol}...")
    download_options_chain(symbol)
    
print("\n✅ All downloads complete!")
```

## Limitations

- **Data Source**: Yahoo Finance (free but may have delays)
- **Rate Limiting**: Yahoo may throttle requests if too frequent
- **Data Quality**: Occasional missing or stale data
- **Historical Data**: Only current options chain, not historical

## License

Same as parent project.

## Support

For issues:
1. Verify yfinance is installed: `pip show yfinance`
2. Test with a known symbol: `python download_options.py SPY --list`
3. Check Yahoo Finance website to verify options exist
4. Try a different symbol or expiration

## Related Tools

- **Gamma Exposure Calculator** (Streamlit): Full analysis app
- **Gamma Exposure Calculator** (Web): Browser-based analysis
- **gamma_cli.py**: Command-line gamma analysis
- **quick_gamma.py**: Fast gamma checks
- **covered_call_analyzer.py**: Covered call strategy analysis
