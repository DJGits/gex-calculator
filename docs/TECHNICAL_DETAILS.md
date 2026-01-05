# Technical Details and Implementation Notes

## Overview

This document consolidates technical implementation details, formulas, and processing logic for the Gamma Exposure Calculator.

## Table of Contents
1. [Gamma Calculation Formula](#gamma-calculation-formula)
2. [Implied Volatility Processing](#implied-volatility-processing)
3. [Time to Expiry Calculations](#time-to-expiry-calculations)
4. [Expiry Time Handling](#expiry-time-handling)

---

## Gamma Calculation Formula

### Black-Scholes Gamma Formula

#### Step 1: Calculate d1
```
d1 = [ln(S/K) + (r + 0.5*σ²)*T] / (σ*√T)
```

Where:
- **S** = Current underlying price (spot price)
- **K** = Strike price
- **r** = Risk-free interest rate (default: 0.05 or 5%)
- **σ** = Implied volatility (as decimal, e.g., 0.25 for 25%)
- **T** = Time to expiry in years
- **ln** = Natural logarithm

#### Step 2: Calculate Gamma
```
Gamma = N'(d1) / (S * σ * √T)
```

Where:
- **N'(d1)** = Standard normal probability density function (PDF) at d1
- **N'(d1) = (1/√(2π)) * e^(-d1²/2)**

**Important:** Gamma is the same for both calls and puts with the same strike and expiry.

#### Step 3: Calculate Gamma Exposure
```
Exposure_Base = Gamma × Open_Interest × Contract_Multiplier × S
```

Where:
- **Gamma** = Calculated gamma value from Step 2
- **Open_Interest** = Number of contracts outstanding
- **Contract_Multiplier** = 100 (for standard equity options)
- **S** = Current underlying price

#### Step 4: Apply Sign Convention (Dealer Perspective)

The exposure is calculated from the **market maker/dealer perspective**, who are typically **short options**:

**For CALL Options:**
```
Call_Gamma_Exposure = -Exposure_Base
```
- **Negative** because dealers are short calls
- Creates **RESISTANCE** above current price
- When price rises, dealers must **buy** to hedge (negative gamma)

**For PUT Options:**
```
Put_Gamma_Exposure = +Exposure_Base
```
- **Positive** because dealers are short puts
- Creates **SUPPORT** below current price
- When price falls, dealers must **sell** to hedge (positive gamma)


### Example Calculation

**Given:**
- Current Price (S) = $683.17
- Strike (K) = $685.00
- Time to Expiry (T) = 2 days = 0.005476 years
- Implied Volatility (σ) = 0.068 (6.8%)
- Risk-Free Rate (r) = 0.05 (5%)
- Open Interest = 10,000 contracts
- Contract Multiplier = 100
- Option Type = CALL

**Step-by-Step:**

1. **Calculate d1:**
   ```
   d1 = [ln(683.17/685) + (0.05 + 0.5*0.068²)*0.005476] / (0.068*√0.005476)
   d1 = -0.474
   ```

2. **Calculate N'(d1):**
   ```
   N'(-0.474) = 0.3566
   ```

3. **Calculate Gamma:**
   ```
   Gamma = 0.3566 / (683.17 * 0.068 * 0.074)
   Gamma = 0.1037
   ```

4. **Calculate Exposure Base:**
   ```
   Exposure_Base = 0.1037 * 10,000 * 100 * 683.17
   Exposure_Base = 708,409,290
   ```

5. **Apply Sign Convention (CALL):**
   ```
   Call_Gamma_Exposure = -708,409,290
   ```
   (Negative = Resistance)

---

## Implied Volatility Processing

### IV Retrieval from Yahoo Finance

Yahoo Finance provides the `impliedVolatility` field directly in the options chain data. This is the **raw IV** calculated by Yahoo Finance using their own pricing models.

### IV Processing Pipeline

```
Data Source (Yahoo Finance / CSV Upload / Breeze API)
        ↓
[1] Missing column? → Use 0.2 (20%)
        ↓
[2] NaN value? → Fill with 0 (yfinance) or 0.2 (processor)
        ↓
[3] Negative? → Take absolute value
        ↓
[4] Below 0.01? → Set to 0.01 (1%)
        ↓
[5] **IV > 10? → Divide by 100 (percentage normalization)**
        ↓
[6] Zero or negative? → Use 0.2 (20%)
        ↓
[7] Below 0.01? → Clamp to 0.01 (1%)
[7] Above 2.0? → Clamp to 2.0 (200%)
        ↓
Final IV used in Black-Scholes
```

### Important: Percentage Normalization

**Location:** `data/processor.py`

This is a **critical** alteration that handles different IV formats:

```python
# Decision logic:
# - If IV > 10: Definitely a percentage, divide by 100
# - If IV <= 10: Already in decimal format, use as-is

mask = df['implied_volatility'] > 10.0
if mask.any():
    print(f"Normalizing {mask.sum()} IV values from percentage to decimal")
    df.loc[mask, 'implied_volatility'] = df.loc[mask, 'implied_volatility'] / 100.0
```

**Examples:**
- IV = 25 → Detected as percentage → Converted to 0.25 (25%)
- IV = 0.25 → Already decimal → Used as-is (25%)
- IV = 150 → Detected as percentage → Converted to 1.50 (150%)
- IV = 1.5 → Already decimal → Used as-is (150%)

### Configuration Values

```python
DEFAULT_VOLATILITY = 0.20    # 20% - used when IV is missing or zero
MIN_VOLATILITY = 0.01        # 1% - minimum allowed IV
MAX_VOLATILITY = 2.0         # 200% - maximum allowed IV
```


---

## Time to Expiry Calculations

### Current Implementation

```python
def calculate_time_to_expiry(self, expiry_date: datetime, current_date: Optional[datetime] = None) -> float:
    """
    Calculate time to expiry in years with intraday precision.
    
    Note:
        - Uses 365.25 days per year to account for leap years
        - Expired options are clamped to MIN_TIME_TO_EXPIRY (1 day)
        - Very long-dated options are clamped to MAX_TIME_TO_EXPIRY (5 years)
        - Provides intraday precision using total_seconds()
    """
    if current_date is None:
        current_date = datetime.now()
    
    # Calculate precise time difference in years
    time_diff = (expiry_date - current_date).total_seconds() / (365.25 * 24 * 3600)
    
    # Apply bounds to prevent extreme values
    time_to_expiry = max(MIN_TIME_TO_EXPIRY, min(MAX_TIME_TO_EXPIRY, time_diff))
    
    return time_to_expiry
```

### Constants

```python
MIN_TIME_TO_EXPIRY = 1/365.25  # 1 day minimum (accounts for leap years)
MAX_TIME_TO_EXPIRY = 5.0       # 5 years maximum
```

### Why 1/365.25?

- **More Accurate**: Better represents one calendar day
- **Consistent**: Matches the 365.25 used in time calculations
- **Industry Standard**: Common in financial calculations
- **Leap Year Aware**: Properly accounts for leap years

**Numerical value:** 0.002737850787132 years = exactly 1.0 days

### Edge Cases Handled

#### 1. Expired Options
```python
# expiry_date = 2026-01-01, current_date = 2026-01-05
time_diff = -4 days = -0.01095 years
time_to_expiry = max(1/365.25, -0.01095) = 1/365.25 = 0.00274 years
```
Result: Clamped to minimum (1 day)

#### 2. Very Long-Dated Options
```python
# expiry_date = 2035-01-01, current_date = 2026-01-05
time_diff = 9 years
time_to_expiry = min(5.0, 9.0) = 5.0 years
```
Result: Clamped to maximum (5 years)

#### 3. Intraday Precision
```python
# expiry_date = 2026-01-16 00:00:00, current_date = 2026-01-03 14:30:00
time_diff = 12.396 days = 0.03393 years
time_to_expiry = 0.03393 years (no clamping needed)
```
Result: Precise calculation including hours/minutes

---

## Expiry Time Handling

### Change Summary

Modified options chain retrieval to set expiry dates to **4:00 PM ET** (16:00) instead of midnight (00:00), reflecting the actual market close time when options expire.

### Implementation

```python
# Convert expiry_date to datetime and set to 4 PM ET (market close)
df['expiry_date'] = pd.to_datetime(df['expiry_date'])

# Set expiry time to 4 PM (16:00) - options expire at market close
df['expiry_date'] = df['expiry_date'].apply(
    lambda x: datetime.combine(x.date(), datetime.min.time().replace(hour=16))
)
```

### Impact

**Before:**
```
Expiry Date: 2026-01-16 00:00:00  (midnight)
Time to Expiry: 11.20 days
```

**After:**
```
Expiry Date: 2026-01-16 16:00:00  (4 PM)
Time to Expiry: 11.87 days
```

### Why This Matters

1. **Market Reality**: Options expire at 4 PM, not midnight
2. **Intraday Accuracy**: Critical for same-day or next-day expiries
3. **Theta Decay**: More accurate time = more accurate theta
4. **Trading Decisions**: 2-3% difference is significant

### Market Close Times

- **US Equity Options** (SPY, QQQ): 4:00 PM ET
- **US Index Options** (SPX, VIX): 9:30 AM ET (AM-settled)
- **Regular Trading**: 9:30 AM - 4:00 PM ET

**Note:** Current implementation uses 4 PM for all options. Future enhancement could detect AM vs PM settlement.

---

## CSV Export Fields

When using `--export-csv`, the following fields are included:

| Field | Description |
|-------|-------------|
| Strike | Strike price |
| Type | CALL or PUT |
| Expiry_Date | Option expiration date |
| Days_To_Expiry | Days until expiration |
| Time_To_Expiry_Years | Time to expiry in years (T) |
| Open_Interest | Number of contracts |
| Implied_Volatility | IV as decimal (σ) |
| IV_Percent | IV as percentage |
| Current_Price | Current underlying price (S) |
| Distance_From_Spot | K - S (dollars) |
| Distance_Percent | (K - S) / S * 100 |
| Moneyness | ATM, ITM, or OTM |
| d1 | Calculated d1 value |
| norm_pdf_d1 | N'(d1) value |
| Gamma | Calculated gamma |
| Contract_Multiplier | Multiplier (100) |
| Exposure_Base | Gamma × OI × Multiplier × S |
| Gamma_Exposure | Final exposure with sign |
| Sign_Convention | Positive (Support) or Negative (Resistance) |
| Risk_Free_Rate | Risk-free rate used (r) |

---

## References

- Black, F., & Scholes, M. (1973). "The Pricing of Options and Corporate Liabilities"
- Hull, J. C. (2018). "Options, Futures, and Other Derivatives"
- Market maker gamma hedging dynamics and their impact on volatility
