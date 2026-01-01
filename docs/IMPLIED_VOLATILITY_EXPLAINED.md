# Implied Volatility in Expected Move Calculation

## Overview

This document explains how **Implied Volatility (IV)** is sourced and used in the Expected Move calculations for the Gamma Exposure Calculator.

## Quick Answer

**Yes, IV is taken directly from the options chain data**, not calculated by our application. We use the IV values that are already provided by:
- Yahoo Finance API
- User-uploaded CSV files
- Sample data generator (random for demo)

## Detailed Explanation

### What is Implied Volatility?

**Implied Volatility (IV)** is the market's forecast of a stock's future volatility, derived from option prices using the Black-Scholes model (or similar). It represents:

- **Market expectation** of future price movement
- **Supply and demand** for options
- **Fear/greed** in the market
- **Upcoming events** (earnings, Fed meetings, etc.)

### Where IV Comes From

#### 1. Yahoo Finance (Live Data)

When fetching from Yahoo Finance:
```python
# Yahoo Finance provides IV for each contract
options_chain = ticker.option_chain(expiration)
calls = options_chain.calls  # Has 'impliedVolatility' column
puts = options_chain.puts    # Has 'impliedVolatility' column
```

**Source:** Yahoo Finance gets IV from:
- Market makers
- Options exchanges (CBOE, etc.)
- Real-time option pricing models

**Example:**
```
SPY $580 Call, 30 DTE
Last Price: $5.50
Implied Volatility: 0.125 (12.5%)
```

#### 2. CSV Upload

When uploading a CSV file:
```csv
strike,expiry_date,option_type,open_interest,implied_volatility
580,2025-01-17,call,15000,0.125
580,2025-01-17,put,12000,0.130
```

**Source:** User provides IV values from:
- Their broker's platform
- Options data providers (CBOE, IVolatility, etc.)
- Historical data exports

**Default:** If IV column is missing, defaults to 0.2 (20%)

#### 3. Sample Data Generator

When generating sample data:
```python
implied_volatility: Math.random() * 0.3 + 0.15  # 15-45%
```

**Source:** Randomly generated for demonstration
- Not real market data
- Used for testing and learning

## How We Use IV in Expected Move

### Current Implementation (Improved)

We now use **ATM (At-The-Money) IV** for more accurate calculations:

```python
# 1. Find contracts closest to current price
contracts_with_distance = []
for c in contracts:
    distance = abs(c.strike - current_price)
    contracts_with_distance.append((c, distance))

# 2. Sort by distance
contracts_with_distance.sort(key=lambda x: x[1])

# 3. Use ATM IV (average of closest 10 contracts)
atm_contracts = contracts_with_distance[:10]
atm_iv = sum(c.implied_volatility for c in atm_contracts) / len(atm_contracts)

# 4. Calculate expected move
expected_move = current_price × atm_iv × √(days_to_expiry / 365)
```

### Why ATM IV?

**ATM options are most liquid and representative:**

| Strike Type | IV Characteristic | Use for Expected Move? |
|-------------|-------------------|------------------------|
| **ATM** | Most liquid, fair value | ✅ **YES** (Best) |
| **OTM** | Higher IV (skew) | ⚠️ Less accurate |
| **ITM** | Lower IV, less liquid | ❌ Not recommended |

**Example:**
```
Current Price: $580

Strike  Type  IV     Distance  Use?
$575    Call  13.2%  $5        ✅ ATM
$580    Call  12.5%  $0        ✅ ATM (closest)
$585    Call  12.8%  $5        ✅ ATM
$590    Call  14.1%  $10       ✅ ATM
$600    Call  16.5%  $20       ❌ Too far OTM
$550    Put   15.2%  $30       ❌ Too far OTM

ATM IV = Average of closest 10 = 12.8%
```

### Previous Implementation (Simple Average)

**Old approach:**
```python
# Average ALL contracts (not ideal)
avg_iv = sum(c.implied_volatility for c in all_contracts) / len(all_contracts)
```

**Problems:**
- Includes far OTM options with inflated IV (skew)
- Includes far ITM options with deflated IV
- Less accurate for expected move

**Why we changed:** ATM IV is more representative of actual expected volatility.

## IV Skew Explained

### What is IV Skew?

**IV Skew** (or volatility smile/smirk) means IV varies by strike:

```
IV
│
│     ╱╲
│    ╱  ╲
│   ╱    ╲
│  ╱  ATM ╲
│ ╱        ╲
│╱          ╲___
└─────────────────> Strike
OTM Put  ATM  OTM Call
```

**Typical Pattern (SPY/SPX):**
- **OTM Puts**: Higher IV (crash protection demand)
- **ATM**: Moderate IV (most liquid)
- **OTM Calls**: Slightly higher IV (upside speculation)

**Example:**
```
SPY at $580:

Strike  Type  IV     Reason
$550    Put   18%    Crash protection (high demand)
$560    Put   15%    Still protective
$570    Put   13%    Getting closer to ATM
$580    Call  12%    ATM (fair value)
$590    Call  13%    Slight upside premium
$600    Call  15%    Speculation
$620    Call  20%    Lottery tickets
```

### Why Skew Matters

**For Expected Move:**
- Using far OTM IV → Overestimates expected move
- Using far ITM IV → Underestimates expected move
- Using ATM IV → Most accurate estimate

**For Trading:**
- High OTM put IV → Expensive protection
- High OTM call IV → Expensive speculation
- ATM IV → Fair value for most strategies

## Comparison: ATM vs Average IV

### Example Calculation

**Scenario:** SPY at $580, 30 DTE

**Option Chain:**
```
Strike  Type  OI     IV
$550    Put   5000   18.0%
$560    Put   8000   15.5%
$570    Put   12000  13.2%
$575    Call  15000  12.8%
$580    Call  20000  12.5%  ← ATM
$585    Call  15000  12.7%
$590    Call  12000  13.5%
$600    Call  8000   16.0%
$620    Call  3000   20.0%
```

**Method 1: Simple Average (Old)**
```
Average IV = (18.0 + 15.5 + 13.2 + 12.8 + 12.5 + 12.7 + 13.5 + 16.0 + 20.0) / 9
           = 14.9%

Expected Move = $580 × 0.149 × √(30/365)
              = $580 × 0.149 × 0.287
              = $24.80 (±4.3%)
```

**Method 2: ATM IV (New)**
```
ATM IV = Average of 10 closest strikes
       = (13.2 + 12.8 + 12.5 + 12.7 + 13.5) / 5
       = 12.9%

Expected Move = $580 × 0.129 × √(30/365)
              = $580 × 0.129 × 0.287
              = $21.50 (±3.7%)
```

**Difference:** $3.30 or 0.6% of stock price

**Which is more accurate?** ATM IV (12.9%) because:
- Excludes far OTM puts with crash premium
- Excludes far OTM calls with speculation premium
- Focuses on liquid, fairly-priced options

## Display in Application

### Streamlit App

The app now shows both IVs:

```
📏 Expected Move (Based on Implied Volatility)

┌─────────────────────────────────────┐
│ 1 Standard Deviation (~68%)         │
│ Expected Move: ±$21.50 (±3.7%)      │
│ Based on 12.9% ATM IV and 30 days   │
└─────────────────────────────────────┘

💡 Trading Implications & IV Details

Implied Volatility Analysis:
  ATM IV (used): 12.9%
  Overall Avg IV: 14.9%

Strategy Suggestions...
```

### Why Show Both?

**ATM IV (used for calculation):**
- Most accurate for expected move
- Represents fair value volatility
- Used by professional traders

**Overall Average IV:**
- Shows market-wide volatility
- Useful for understanding skew
- Comparison reference

## IV Sources by Data Type

### Yahoo Finance

**How Yahoo calculates IV:**
1. Takes current option price
2. Uses Black-Scholes model (or similar)
3. Solves for volatility that matches price
4. Updates in real-time

**Reliability:** ✅ High
- Professional-grade calculations
- Real-time market data
- Used by millions of traders

### CSV Upload

**User responsibility:**
- Must provide accurate IV values
- Should come from reliable source
- Check for data quality

**Common sources:**
- Broker platforms (TD Ameritrade, Interactive Brokers)
- Data providers (CBOE, IVolatility, OptionMetrics)
- Historical databases

**Reliability:** Depends on source

### Sample Data

**Random generation:**
```python
IV = random(15%, 45%)
```

**Reliability:** ❌ Not real
- For demonstration only
- Don't use for actual trading
- Good for learning the tool

## Best Practices

### For Accurate Expected Move

1. **Use Real Data**
   - Yahoo Finance (live)
   - Recent CSV export from broker
   - Not sample data

2. **Check IV Levels**
   - Compare to historical IV
   - Check IV rank/percentile
   - Understand if IV is elevated

3. **Consider Time Frame**
   - Shorter DTE = smaller expected move
   - Longer DTE = larger expected move
   - Adjust strategies accordingly

4. **Understand Skew**
   - OTM puts usually have higher IV
   - Don't be surprised by differences
   - ATM IV is most representative

### For Trading Decisions

1. **High IV (>40%)**
   - Large expected move
   - Premium selling attractive
   - Buying options expensive

2. **Moderate IV (25-40%)**
   - Normal expected move
   - Balanced strategies
   - Standard risk management

3. **Low IV (<25%)**
   - Small expected move
   - Buying options attractive
   - Premium selling less profitable

## Technical Details

### IV in OptionsContract Model

```python
@dataclass
class OptionsContract:
    symbol: str
    strike: float
    expiry_date: datetime
    option_type: str
    open_interest: int
    volume: int
    bid: float
    ask: float
    last_price: float
    implied_volatility: float  # ← Stored as decimal (0.125 = 12.5%)
```

### IV Validation

```python
if self.implied_volatility < 0:
    raise ValueError("IV cannot be negative")

# Typical range: 0.05 (5%) to 2.0 (200%)
# Most stocks: 0.15 (15%) to 0.60 (60%)
```

### IV in Calculations

```python
# Always use as decimal
iv_decimal = 0.125  # 12.5%

# Display as percentage
iv_percentage = iv_decimal * 100  # 12.5

# In formula
expected_move = price * iv_decimal * sqrt(dte/365)
```

## FAQ

**Q: Do you calculate IV from option prices?**
A: No, we use IV values provided by Yahoo Finance or user data.

**Q: Why not calculate IV ourselves?**
A: IV calculation requires solving Black-Scholes backwards (numerical methods). Yahoo Finance already does this accurately.

**Q: Is ATM IV always the best?**
A: For expected move, yes. For specific strategies, you might want IV at your target strike.

**Q: What if IV is missing in CSV?**
A: Defaults to 0.2 (20%), but you should provide real IV for accuracy.

**Q: Can I use historical volatility instead?**
A: No, expected move should use implied volatility (forward-looking), not historical volatility (backward-looking).

**Q: Why is IV different for calls vs puts?**
A: IV skew - market prices in different risks for upside vs downside.

**Q: Should I use call IV or put IV?**
A: We average both for ATM strikes. They're usually similar at-the-money.

## Conclusion

**Key Takeaways:**

1. ✅ **IV comes from options chain data** (Yahoo Finance, CSV, etc.)
2. ✅ **We use ATM IV** for most accurate expected move
3. ✅ **ATM IV excludes skew effects** from far OTM options
4. ✅ **Both ATM and average IV are displayed** for transparency
5. ✅ **Real data is essential** for accurate trading decisions

The Expected Move feature provides a realistic estimate of price movement based on what the options market is actually pricing in, not theoretical calculations.
