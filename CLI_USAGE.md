# SPX Gamma Exposure Calculator - Command Line Tools

Three powerful CLI tools to analyze gamma exposure without the Streamlit interface:

## 🔍 Quick Analysis (`quick_gamma.py`)

**Fast gamma check for a single symbol**

```bash
# Quick SPY analysis (nearest expiration)
python quick_gamma.py SPY

# SPY with specific expiration date
python quick_gamma.py SPY 2025-01-17

# QQQ with multiple expirations
python quick_gamma.py QQQ multiple
```

**Output:**
```
🔍 Quick Gamma Analysis: SPY
📅 Expiration: 2025-01-17
⏰ 13:43:59
----------------------------------------
💰 Price: $685.57
📊 Contracts: 477
⚡ Environment: NEGATIVE (Very Weak)
🎯 Net Gamma: -11,460,918
📈 Weighted Strike: 686
🔄 Flip Level: 686 (-0)
🔴 Top Call Wall: 687 (+0.2%)
🟢 Top Put Wall: 685 (-0.1%)

💡 Quick Take:
   📈 Momentum/trend following
   ⚠️ Low confidence - consider other factors
```

## 📊 Comprehensive Analysis (`gamma_cli.py`)

**Full detailed analysis with all metrics**

```bash
# Full SPY analysis with nearest expiration
python gamma_cli.py SPY

# SPY with specific expiration date
python gamma_cli.py SPY 2025-01-17

# SPY with interactive expiration selection
python gamma_cli.py SPY specific

# QQQ with multiple expirations
python gamma_cli.py QQQ multiple

# List available symbols
python gamma_cli.py --list-symbols

# List available expirations for a symbol
python gamma_cli.py --list-expirations SPY

# Custom risk-free rate
python gamma_cli.py SPY 2025-01-17 --risk-free-rate 0.045
```

**Features:**
- Complete gamma environment analysis
- Environment strength interpretation
- Gamma flip level analysis with trading implications
- Top 5 call and put walls
- Detailed trading strategy recommendations
- Direct expiration date specification
- Interactive expiration selection

## 🔄 Batch Analysis (`batch_gamma.py`)

**Compare multiple symbols at once**

```bash
# Analyze SPY, QQQ, IWM with nearest expiration (default)
python batch_gamma.py

# Custom symbol list with nearest expiration
python batch_gamma.py SPY QQQ IWM TSLA AAPL

# All symbols with specific expiration date
python batch_gamma.py SPY QQQ IWM --exp 2025-01-17

# All symbols with multiple expirations
python batch_gamma.py SPY QQQ --exp multiple
```

**Output:**
```
📊 GAMMA ANALYSIS SUMMARY
================================================================================
Symbol Price    Environment  Strength     Net Gamma    Flip   Walls 
--------------------------------------------------------------------------------
SPY    $686     ⚡NEG         Strong       -88.2M       686    5C/5P 
QQQ    $512     🛡️POS         Moderate     +45.1M       515    3C/4P
IWM    $231     ⚖️NEU         Weak         -2.3M        N/A    2C/2P

📋 DETAILED ANALYSIS
================================================================================
🎯 SPY: ⚡ NEGATIVE (Strong) - Momentum/trend following (High confidence)
🎯 QQQ: 🛡️ POSITIVE (Moderate) - Buy dips, sell rallies (Moderate confidence)  
🎯 IWM: ⚖️ NEUTRAL (Weak) - Mixed signals (Low confidence)
```

## 📅 Expiration Parameter Options

### **Direct Date Specification**
```bash
# Use specific expiration date (YYYY-MM-DD format)
python gamma_cli.py SPY 2025-01-17
python quick_gamma.py QQQ 2025-02-21
python batch_gamma.py SPY QQQ --exp 2025-03-21
```

### **Selection Modes**
```bash
# Nearest expiration (default)
python gamma_cli.py SPY nearest
python gamma_cli.py SPY  # same as above

# Interactive selection
python gamma_cli.py SPY specific

# Multiple expirations (first 5)
python gamma_cli.py SPY multiple
```

### **List Available Expirations**
```bash
# See all available expiration dates for a symbol
python gamma_cli.py --list-expirations SPY
python gamma_cli.py --list-expirations QQQ
```

## 📋 Command Reference

### Environment Types
- **🛡️ POSITIVE**: Market makers provide support (buy dips, sell rallies)
- **⚡ NEGATIVE**: Market makers amplify moves (momentum/trend following)
- **⚖️ NEUTRAL**: Balanced gamma forces (mixed signals)

### Strength Levels
- **🔴 Very Strong (≥0.10)**: Extremely powerful gamma forces
- **🟠 Strong (0.05-0.10)**: Significant market maker impact
- **🟡 Moderate (0.02-0.05)**: Noticeable influence
- **🟢 Weak (0.01-0.02)**: Limited impact
- **⚪ Very Weak (<0.01)**: Minimal influence

### Wall Types
- **🔴 Call Walls**: Resistance levels (negative gamma exposure)
- **🟢 Put Walls**: Support levels (positive gamma exposure)

### Flip Level Interpretation
- **Distance from current price** indicates breakout/breakdown potential
- **Above flip in positive env**: Breakout acceleration potential
- **Below flip in positive env**: Breakdown risk
- **Above flip in negative env**: Stabilization resistance
- **Below flip in negative env**: Support level

## 🚀 Usage Examples

### Morning Market Check
```bash
# Quick check of major ETFs with nearest expiration
python batch_gamma.py SPY QQQ IWM

# Check specific expiration (e.g., weekly options)
python batch_gamma.py SPY QQQ IWM --exp 2025-01-03
```

### Options Expiration Analysis
```bash
# Compare different expirations for SPY
python gamma_cli.py SPY 2025-01-17  # Monthly
python gamma_cli.py SPY 2025-01-03  # Weekly

# Check multiple expirations at once
python gamma_cli.py SPY multiple
```

### Individual Stock Analysis
```bash
# Quick check with specific expiration
python quick_gamma.py TSLA 2025-01-17

# Full analysis for options trading
python gamma_cli.py AAPL 2025-02-21

# List available expirations first
python gamma_cli.py --list-expirations AAPL
```

### Earnings Week Analysis
```bash
# Check earnings week expiration
python gamma_cli.py TSLA 2025-01-24  # If earnings on 1/23

# Compare pre/post earnings expirations
python quick_gamma.py AAPL 2025-01-17  # Before earnings
python quick_gamma.py AAPL 2025-01-31  # After earnings
```

## 💡 Pro Tips

1. **Use specific dates** for precise expiration analysis
2. **List expirations first** to see available dates: `--list-expirations SYMBOL`
3. **Weekly vs Monthly**: Weekly options often have different gamma profiles
4. **Earnings analysis**: Compare expirations before/after earnings dates
5. **OPEX weeks**: Use multiple expirations during options expiration weeks
6. **Higher strength = higher confidence** in gamma effects
7. **Watch flip levels closely** - they're key inflection points

## 🔧 Requirements

All CLI tools use the same dependencies as the Streamlit app:
```bash
pip install -r requirements.txt
```

Set PYTHONPATH for proper imports:
```bash
export PYTHONPATH=.
# or
PYTHONPATH=. python gamma_cli.py SPY 2025-01-17
```