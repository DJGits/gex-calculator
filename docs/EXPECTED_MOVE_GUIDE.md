# Expected Move Calculator - User Guide

## Overview

The Expected Move feature calculates the anticipated price range for a stock based on its **implied volatility (IV)**. This is one of the most practical tools for options traders to understand potential price movement and set realistic expectations.

## What is Expected Move?

**Expected Move** is the predicted price range where a stock is likely to trade by expiration, based on the options market's implied volatility.

### Formula

```
Expected Move = Current Price × Implied Volatility × √(Days to Expiry / 365)
```

### Key Concepts

- **1 Standard Deviation (1SD)**: ~68% probability the price stays within this range
- **2 Standard Deviations (2SD)**: ~95% probability the price stays within this range
- **Implied Volatility**: The market's expectation of future volatility

## Using the Standalone Script

### Basic Usage

```bash
# Calculate expected move for SPY (nearest expiration)
python expected_move.py SPY

# Calculate for specific expiration
python expected_move.py SPY 2025-01-17

# Calculate for any stock
python expected_move.py AAPL
python expected_move.py TSLA 2025-02-21
python expected_move.py NVDA
```

### Example Output

```
📊 Expected Move Analysis: SPY
⏰ 2025-01-01 14:30:25
======================================================================
⏳ Fetching options data...
✅ Data retrieved successfully!

📈 Current Market Data:
   Symbol: SPY
   Current Price: $582.45
   Expiration: 2025-01-17
   Days to Expiry: 16
   ATM Strike: $582.00
   ATM Implied Volatility: 12.50%

🎯 EXPECTED MOVE (1 Standard Deviation)
----------------------------------------------------------------------
   Probability: ~68.2% chance price stays within this range
   Expected Move: ±$15.23 (±2.61%)

   📊 Price Range:
      Upper Bound: $597.68 (+2.61%)
      Current:     $582.45
      Lower Bound: $567.22 (-2.61%)

🎯 EXPECTED MOVE (2 Standard Deviations)
----------------------------------------------------------------------
   Probability: ~95.4% chance price stays within this range
   Expected Move: ±$30.46 (±5.23%)

   📊 Price Range:
      Upper Bound: $612.91 (+5.23%)
      Current:     $582.45
      Lower Bound: $551.99 (-5.23%)

💡 TRADING IMPLICATIONS
----------------------------------------------------------------------
   📅 MEDIUM-TERM EXPIRATION (16 days)
      • Moderate expected move
      • Balanced risk/reward for most strategies
      • Consider both directional and neutral strategies

   🎯 Strategy Suggestions:
      Iron Condor: Sell strikes outside 1SD range
         • Sell 598 call / Buy 613 call
         • Sell 567 put / Buy 552 put

      Long Straddle/Strangle: Profit if move exceeds 1SD
         • Breakeven needs move > $15.23
         • Consider if expecting volatility expansion

      Covered Call: Sell calls at upper 1SD
         • Strike: ~$598
         • 68.2% chance of keeping premium

   ⚠️ Risk Assessment:
      🟢 LOW IV (12.5%) - Small expected move
         • Buying options may be attractive
         • Premium selling less profitable
         • Consider volatility expansion

📊 PROBABILITY TABLE
----------------------------------------------------------------------
   Range                          Probability    Price Range
   ──────────────────────────────────────────────────────────────────
   Within 1 SD (±2.6%)            ~68.2%         $567.22 - $597.68
   Within 2 SD (±5.2%)            ~95.4%         $551.99 - $612.91
   Beyond 2 SD                    ~4.6%          <$551.99 or >$612.91

✅ Analysis complete for SPY
```

## Using in Streamlit App

The expected move is automatically calculated and displayed in the analysis section:

### Location
After loading options data, scroll to the **"Expected Move (Based on Implied Volatility)"** section.

### What You'll See

**1 Standard Deviation Box (Blue):**
- Expected move amount and percentage
- Upper and lower price bounds
- 68% probability range

**2 Standard Deviations Box (Yellow):**
- Larger expected move (2x the 1SD move)
- Wider price bounds
- 95% probability range

**Trading Implications (Expandable):**
- Strategy suggestions based on expected move
- Iron condor strike recommendations
- Covered call and CSP strike suggestions
- IV level assessment (High/Moderate/Low)

## Interpreting the Results

### 1 Standard Deviation (68% Probability)

**What it means:**
- There's approximately a 68% chance the stock will close within this range by expiration
- This is the "most likely" price range
- Use this for setting realistic profit targets

**Trading Applications:**
- **Iron Condors**: Sell strikes just outside this range
- **Covered Calls**: Sell calls at or above upper bound
- **Cash-Secured Puts**: Sell puts at or below lower bound

### 2 Standard Deviations (95% Probability)

**What it means:**
- There's approximately a 95% chance the stock will close within this range
- Moves beyond this are considered "outliers"
- Only ~5% chance of exceeding this range

**Trading Applications:**
- **Risk Management**: Set stop losses beyond 2SD
- **Iron Condor Wings**: Buy protection at 2SD levels
- **Probability Assessment**: Understand tail risk

### Beyond 2 Standard Deviations (~5% Probability)

**What it means:**
- Rare but possible events
- "Black swan" territory
- Requires catalyst (earnings, news, etc.)

## Strategy Applications

### Iron Condors

**Setup:**
- Sell call spread above 1SD upper bound
- Sell put spread below 1SD lower bound
- Buy protection at 2SD levels

**Example (SPY at $582, 1SD = ±$15):**
```
Sell $598 call / Buy $613 call
Sell $567 put / Buy $552 put
```

**Probability of Profit:** ~68% (if price stays within 1SD range)

### Covered Calls

**Setup:**
- Sell calls at or near 1SD upper bound
- Collect premium while limiting upside

**Example (SPY at $582, 1SD upper = $598):**
```
Own 100 shares of SPY at $582
Sell 1 contract of $598 call
```

**Probability of Assignment:** ~16% (half of the 32% above 1SD)

### Cash-Secured Puts

**Setup:**
- Sell puts at or near 1SD lower bound
- Collect premium while willing to buy stock

**Example (SPY at $582, 1SD lower = $567):**
```
Sell 1 contract of $567 put
Reserve $56,700 cash
```

**Probability of Assignment:** ~16% (half of the 32% below 1SD)

### Long Straddles/Strangles

**Setup:**
- Buy ATM call and put (straddle)
- Or buy OTM call and put (strangle)
- Profit if move exceeds expected move

**Breakeven:**
- Need move > 1SD to overcome premium paid
- Best when expecting volatility expansion

**Example (SPY at $582, 1SD = $15):**
```
Buy $582 call + $582 put
Breakeven: $582 ± $15 (approximately)
```

## IV Level Interpretation

### High IV (>40%)

**Characteristics:**
- Large expected move
- Expensive options
- High premium collection

**Best Strategies:**
- Premium selling (covered calls, CSPs, iron condors)
- Avoid buying options (expensive)
- Consider volatility contraction

**Example:**
```
TSLA at $387, IV = 45%, 30 DTE
Expected Move: ±$42 (±10.9%)
Range: $345 - $429
```

### Moderate IV (25-40%)

**Characteristics:**
- Normal expected move
- Balanced option prices
- Standard market conditions

**Best Strategies:**
- Balanced approach
- Both buying and selling viable
- Standard risk management

**Example:**
```
AAPL at $195, IV = 28%, 30 DTE
Expected Move: ±$9.50 (±4.9%)
Range: $185.50 - $204.50
```

### Low IV (<25%)

**Characteristics:**
- Small expected move
- Cheap options
- Low premium collection

**Best Strategies:**
- Buying options (cheap)
- Avoid premium selling (low returns)
- Consider volatility expansion

**Example:**
```
SPY at $582, IV = 12%, 16 DTE
Expected Move: ±$15 (±2.6%)
Range: $567 - $598
```

## Time to Expiration Impact

### Short-Term (1-7 days)

**Expected Move:** Small
- Time factor: √(7/365) = 0.137
- Move is ~14% of annual volatility

**Trading Implications:**
- Good for theta strategies
- Small profit targets
- High gamma risk

**Example:**
```
SPY at $582, IV = 20%, 7 DTE
Expected Move: ±$6.50 (±1.1%)
```

### Medium-Term (8-45 days)

**Expected Move:** Moderate
- Time factor: √(30/365) = 0.287
- Move is ~29% of annual volatility

**Trading Implications:**
- Balanced strategies
- Reasonable profit targets
- Moderate gamma risk

**Example:**
```
SPY at $582, IV = 20%, 30 DTE
Expected Move: ±$13.70 (±2.4%)
```

### Long-Term (46+ days)

**Expected Move:** Large
- Time factor: √(90/365) = 0.496
- Move is ~50% of annual volatility

**Trading Implications:**
- Better for directional plays
- Larger profit targets
- Lower gamma risk

**Example:**
```
SPY at $582, IV = 20%, 90 DTE
Expected Move: ±$23.80 (±4.1%)
```

## Practical Examples

### Example 1: Earnings Play

**Scenario:** NVDA before earnings
```
Current Price: $495
IV: 65% (elevated due to earnings)
DTE: 3 days
```

**Expected Move:**
```
1SD: ±$28.50 (±5.8%)
Range: $466.50 - $523.50
```

**Strategy:**
- High IV suggests selling premium
- But earnings can cause >2SD moves
- Consider iron condor with wide wings
- Or stay out (binary event)

### Example 2: Low Volatility Environment

**Scenario:** SPY in calm market
```
Current Price: $582
IV: 10% (very low)
DTE: 30 days
```

**Expected Move:**
```
1SD: ±$10.00 (±1.7%)
Range: $572 - $592
```

**Strategy:**
- Low IV suggests buying options
- Small expected move limits profit
- Consider longer-dated options
- Or wait for IV expansion

### Example 3: Standard Setup

**Scenario:** AAPL normal conditions
```
Current Price: $195
IV: 25% (moderate)
DTE: 45 days
```

**Expected Move:**
```
1SD: ±$11.50 (±5.9%)
Range: $183.50 - $206.50
```

**Strategy:**
- Balanced environment
- Iron condor: Sell $207/$183 strikes
- Or covered call at $207
- Or CSP at $183

## Limitations and Considerations

### 1. IV Can Change
- Expected move assumes constant IV
- IV often decreases after events
- Monitor IV changes

### 2. Not a Prediction
- Shows probability range, not direction
- Market can exceed expected move
- Use with other analysis

### 3. Assumes Normal Distribution
- Real markets have "fat tails"
- Extreme moves more common than model suggests
- Black swan events happen

### 4. ATM IV Used
- Different strikes have different IVs (skew)
- ATM IV is representative but not exact
- Consider IV skew for precision

## Tips for Success

### 1. Compare to Historical Moves
```bash
# Check if expected move is realistic
# Compare to recent price action
```

### 2. Consider Catalysts
- Earnings: Expect larger moves
- Fed meetings: Increased volatility
- Product launches: Stock-specific moves

### 3. Use with Technical Analysis
- Expected move + support/resistance
- Expected move + trend lines
- Expected move + chart patterns

### 4. Monitor IV Rank/Percentile
- High IV rank: Good for selling
- Low IV rank: Good for buying
- Compare current IV to historical

### 5. Adjust for Market Conditions
- Bull market: Bias toward upper bound
- Bear market: Bias toward lower bound
- Sideways: Stay within range

## Integration with Gamma Analysis

### Combined Analysis

**Expected Move + Gamma Walls:**
- If gamma walls align with expected move bounds: Strong levels
- If walls are inside expected move: May not hold
- If walls are outside expected move: Extra strong levels

**Example:**
```
SPY at $582
Expected Move 1SD: $567 - $598
Put Wall: $565 (just below 1SD)
Call Wall: $600 (just above 1SD)

Interpretation: Walls reinforce expected move range
Strategy: High confidence iron condor
```

## Conclusion

Expected move is a powerful tool for:
- Setting realistic profit targets
- Choosing appropriate strikes
- Understanding probability
- Managing risk effectively

Use it alongside:
- Gamma exposure analysis
- Technical analysis
- Fundamental analysis
- Market sentiment

Remember: It's a probability tool, not a guarantee. Always use proper risk management and position sizing.
