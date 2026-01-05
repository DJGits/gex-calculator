# Debug Mode and Testing Guide

## Overview

This guide covers all debugging and testing features available in the Gamma Exposure Calculator, including debug modes, test scripts, and troubleshooting tools.

## Table of Contents
1. [Debug Mode](#debug-mode)
2. [Gamma Flip Debug](#gamma-flip-debug)
3. [Single Strike Test Script](#single-strike-test-script)
4. [Quick Reference](#quick-reference)

---

## Debug Mode

### Enabling Debug Mode

Add the `--debug` flag to any gamma_cli.py command:

```bash
python gamma_cli.py SPY --debug
```

### What Debug Mode Shows

#### 1. Gamma Calculation Details

For each option contract, debug mode prints:

```
================================================================================
DEBUG: calculate_contract_gamma_exposure()
================================================================================
  Contract: SPY 590.0 CALL
  Expiry Date: 2026-01-16 00:00:00
  Time to Expiry: 0.032877 years (12.0 days)
  Implied Volatility: 0.1234 (raw)
  Volatility Used: 0.1234 (after bounds check)
  Open Interest: 5,432
  Spot Price: 595.50
  Strike Price: 590.00
  Risk-Free Rate: 0.0500
  Calculated Gamma: 0.0123456789

  DEBUG: calculate_exposure() for CALL at strike 590.0
    gamma                =         0.0123456789
    open_interest        =                5,432
    contract_multiplier  =                  100
    spot                 =               595.50
    raw_exposure         =          400,123.45
    sign_convention      = -1 (call = negative)
    final_exposure       =         -400,123.45
================================================================================
```

**Key Variables Explained:**

- **gamma**: The Black-Scholes gamma value (second derivative of option price)
- **open_interest**: Number of outstanding contracts
- **contract_multiplier**: 100 for standard equity options
- **spot**: Current underlying price
- **raw_exposure**: gamma × OI × multiplier × spot (before sign convention)
- **sign_convention**: -1 for calls (resistance), +1 for puts (support)
- **final_exposure**: The final gamma exposure value

#### 2. Max Call Exposure Calculation

Debug mode shows the complete breakdown:

```
================================================================================
DEBUG: calculate_max_exposures()
================================================================================
Total strikes analyzed: 150

All Call Gamma Exposures:
--------------------------------------------------------------------------------
  Strike   580.00: call_gamma_exposure =          -1,234,567.89
  Strike   585.00: call_gamma_exposure =          -2,345,678.90
  Strike   590.00: call_gamma_exposure =          -3,456,789.01  ← Most negative
  Strike   595.00: call_gamma_exposure =          -2,234,567.89

MAX CALL EXPOSURE (most negative):           -3,456,789.01
Strike with max call exposure:                      590.00
```

### Understanding the Output

#### Why Calls are Negative

Market makers are typically **short options**. When they're short calls:
- They have **negative gamma**
- As price rises, they need to **buy** the underlying to hedge
- This creates **resistance** (selling pressure from hedging)
- Hence: **negative exposure values**

#### Why Puts are Positive

When market makers are short puts:
- They have **positive gamma**
- As price falls, they need to **sell** the underlying to hedge
- This creates **support** (buying pressure from hedging)
- Hence: **positive exposure values**

### Usage Examples

```bash
# Basic debug mode
python gamma_cli.py SPY --debug

# Debug with CSV export
python gamma_cli.py SPY --debug --export-csv

# Debug with flip level analysis
python gamma_cli.py SPY --debug --debug-flip

# Debug specific expiry
python gamma_cli.py SPY 2026-01-17 --debug
```

### Performance Note

Debug mode generates extensive output:
- ~100-200 lines per contract
- 10,000+ lines for full SPY analysis
- Slower execution due to printing

**Recommendation**: Use for specific analysis or troubleshooting, not routine runs.

---

## Gamma Flip Debug

### Overview

The `--debug-flip` flag provides a detailed visual walkthrough of how the gamma flip level is calculated.

### Usage

```bash
# Basic usage with debug
python gamma_cli.py SPY --debug-flip

# With specific expiration
python gamma_cli.py SPY 2026-01-16 --debug-flip

# Combine with CSV export
python gamma_cli.py SPY --debug-flip --export-csv
```

### Output Sections

#### 1. Header Information
```
📊 Current Price: $683.17
🎯 Detected Flip Level: $686
📏 Distance: $+2.83 (+0.41%)
```

#### 2. Strike Table
```
================================================================================
Strike   |          Net Gamma | Sign   | Analysis                      
================================================================================
683      | +          191,722 | +      | ← Current Price               
684      | +          290,501 | +      | ← Last Positive               
685      |         -9,710,984 | -      | ← First Negative ⚠️ FLIP!     
686      | +        1,706,233 | +      | ← First Positive ⚠️ FLIP!     
```

#### 3. Sign Changes Detected
```
1. Between Strike 684 and 685:
   Strike 684:           +290,501 (positive)
   Strike 685:         -9,710,984 (negative)
   Flip Magnitude:         10,001,485
   Interpolated Flip Level: $684.50

2. Between Strike 685 and 686:
   Strike 685:         -9,710,984 (negative)
   Strike 686:         +1,706,233 (positive)
   Flip Magnitude:         11,417,216
   Interpolated Flip Level: $685.50
   ⭐ SELECTED (Largest Magnitude)
```

#### 4. Interpretation
```
✅ Current Position: BELOW flip level
   • You are in POSITIVE gamma territory
   • Market makers provide SUPPORT (buy dips, sell rallies)
   • Distance to flip: $2.33 (0.34%)

   ⚠️ CRITICAL: Only 0.34% away from flip!
   • Watch for breakout above $686
```

---

## Single Strike Test Script

### Overview

`test_single_strike_gex.py` calculates gamma exposure for a **single specific strike** and prints **every variable** used in the calculation.

### Usage

```bash
python test_single_strike_gex.py <SYMBOL> <EXPIRY> <STRIKE> <TYPE>
```

### Examples

```bash
# Call option
python test_single_strike_gex.py SPY 2026-01-16 685 call

# Put option
python test_single_strike_gex.py SPY 2026-01-16 680 put
```

### Output Steps

The script breaks down the calculation into 9 steps:

1. **Fetch Current Price** - Get spot price from yfinance
2. **Fetch Options Chain** - Get options data for specified expiry
3. **Contract Details** - Display all contract information
4. **Time to Expiry** - Calculate and show time calculations
5. **Volatility Bounds** - Show IV bounds checking
6. **Black-Scholes Gamma** - Complete gamma calculation breakdown
7. **Gamma Exposure** - Calculate exposure with sign convention
8. **Summary** - Consolidated results
9. **Interpretation** - Explain what the numbers mean

### Example Output

```
================================================================================
  Step 8: Summary
================================================================================
Symbol:                        SPY
Strike:                        $685.00
Option Type:                   CALL
Current Price:                 $683.17
Open Interest:                 22,476
Implied Volatility:            12.86%
Days to Expiry:                11.2
Gamma:                         0.0258781584

FINAL GAMMA EXPOSURE:          -39,735,728.35

✅ This call option creates NEGATIVE gamma exposure
   • Creates RESISTANCE at strike $685.00
   • Strike is $1.83 (0.27%) ABOVE current price
```

### Use Cases

1. **Learning Black-Scholes**: See every step of the gamma calculation
2. **Debugging Calculations**: Verify specific strike calculations
3. **Understanding Gamma Exposure**: See how OI, IV, and time affect exposure
4. **Teaching Tool**: Show students/colleagues how GEX is calculated

---

## Quick Reference

### Common Commands

```bash
# Find available expirations
python gamma_cli.py --list-expirations SPY

# Basic debug
python gamma_cli.py SPY --debug

# Debug + CSV export
python gamma_cli.py SPY --debug --export-csv

# Gamma flip analysis
python gamma_cli.py SPY --debug-flip

# Single strike test
python test_single_strike_gex.py SPY 2026-01-16 685 call

# Save debug output
python gamma_cli.py SPY --debug > debug.txt 2>&1

# View debug output page by page
python gamma_cli.py SPY --debug 2>&1 | less

# Search debug output
python gamma_cli.py SPY --debug 2>&1 | grep "MAX CALL"
```

### Comparison Table

| Feature | test_single_strike_gex.py | gamma_cli.py --debug | gamma_cli.py --export-csv |
|---------|---------------------------|----------------------|---------------------------|
| **Scope** | Single strike | All strikes | All strikes |
| **Detail Level** | Maximum | High | Medium |
| **Output Size** | ~150 lines | 10,000+ lines | CSV file |
| **Interpretation** | Included | Minimal | None |
| **Speed** | Fast | Slower | Fast |
| **Best For** | Learning/debugging | Full analysis | Spreadsheet analysis |

### Troubleshooting

#### Issue: Too much output
**Solution**: Pipe to `less` or save to file

#### Issue: Can't find specific strike
**Solution**: Use grep
```bash
python gamma_cli.py SPY --debug 2>&1 | grep "Strike   685"
```

#### Issue: Want only max exposure
**Solution**: Use grep
```bash
python gamma_cli.py SPY --debug 2>&1 | grep "MAX"
```

#### Issue: Need spreadsheet format
**Solution**: Use CSV export instead
```bash
python gamma_cli.py SPY --export-csv
```

## Related Documentation

- `GAMMA_CALCULATION_FORMULA.md` - Detailed formula documentation
- `CLI_USAGE.md` - Command line tools guide
- `README.md` - Main project documentation
