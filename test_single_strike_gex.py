#!/usr/bin/env python3
"""
Test Script: Calculate GEX for a Single Strike
Prints all variables used in the calculation

Usage:
  python test_single_strike_gex.py SPY 2026-01-17 685 call
  python test_single_strike_gex.py SPY 2026-01-17 680 put
  python test_single_strike_gex.py QQQ 2026-01-31 500 call
"""

import sys
import argparse
from datetime import datetime
import numpy as np
from scipy.stats import norm

# Import our modules
from data.yfinance_fetcher import YFinanceOptionsFetcher, YFinanceFetchError
from calculations.gamma import GammaCalculator
from app_config import SPX_CONTRACT_MULTIPLIER, DEFAULT_RISK_FREE_RATE


def print_separator(char="=", length=80):
    """Print a separator line"""
    print(char * length)


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")


def calculate_and_print_gex(symbol: str, expiry_date: str, strike: float, option_type: str):
    """
    Calculate and print all GEX variables for a specific strike
    
    Args:
        symbol: Stock symbol (e.g., 'SPY')
        expiry_date: Expiration date (YYYY-MM-DD)
        strike: Strike price
        option_type: 'call' or 'put'
    """
    
    print_section(f"GEX Calculation Test: {symbol} {strike} {option_type.upper()}")
    print(f"Expiration: {expiry_date}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize fetcher
        fetcher = YFinanceOptionsFetcher()
        
        # Get current price
        print_section("Step 1: Fetch Current Price")
        current_price = fetcher.get_current_price(symbol)
        print(f"Current {symbol} Price: ${current_price:.2f}")
        
        # Fetch options data
        print_section("Step 2: Fetch Options Chain Data")
        print(f"Fetching options for expiration: {expiry_date}")
        
        options_df = fetcher.fetch_options_chain(
            symbol=symbol,
            expiration_date=expiry_date,
            include_all_expirations=False
        )
        
        print(f"Total contracts fetched: {len(options_df)}")
        
        # Check column names
        print(f"DataFrame columns: {list(options_df.columns)}")
        
        # Filter for specific strike and type
        # The column might be 'option_type' instead of 'type'
        type_column = 'option_type' if 'option_type' in options_df.columns else 'type'
        
        filtered_df = options_df[
            (options_df['strike'] == strike) & 
            (options_df[type_column] == option_type)
        ]
        
        if filtered_df.empty:
            print(f"\n❌ ERROR: No {option_type} contract found at strike {strike}")
            print(f"\nAvailable strikes for {option_type}s:")
            available = options_df[options_df[type_column] == option_type]['strike'].unique()
            available_sorted = sorted(available)
            for i, s in enumerate(available_sorted[:20], 1):
                print(f"  {i:2d}. {s:.2f}")
            if len(available_sorted) > 20:
                print(f"  ... and {len(available_sorted) - 20} more")
            return 1
        
        print(f"✅ Found {option_type} contract at strike {strike}")
        
        # Convert to contract object
        contracts = fetcher.convert_to_contracts(filtered_df)
        
        if not contracts:
            print(f"❌ ERROR: Could not convert contract data")
            return 1
        
        contract = contracts[0]
        
        # Display contract details
        print_section("Step 3: Contract Details")
        print(f"{'Symbol:':<30} {contract.symbol}")
        print(f"{'Strike:':<30} ${contract.strike:.2f}")
        print(f"{'Option Type:':<30} {contract.option_type.upper()}")
        print(f"{'Expiry Date:':<30} {contract.expiry_date}")
        print(f"{'Open Interest:':<30} {contract.open_interest:,}")
        print(f"{'Implied Volatility (raw):':<30} {contract.implied_volatility:.6f} ({contract.implied_volatility*100:.2f}%)")
        print(f"{'Last Price:':<30} ${contract.last_price:.2f}")
        print(f"{'Bid:':<30} ${contract.bid:.2f}")
        print(f"{'Ask:':<30} ${contract.ask:.2f}")
        print(f"{'Volume:':<30} {contract.volume:,}")
        
        # Calculate time to expiry
        print_section("Step 4: Calculate Time to Expiry")
        today = datetime.now()
        expiry_dt = contract.expiry_date if isinstance(contract.expiry_date, datetime) else datetime.fromisoformat(str(contract.expiry_date))
        
        print(f"{'Current Date/Time:':<30} {today}")
        print(f"{'Expiry Date/Time:':<30} {expiry_dt}")
        
        time_diff_seconds = (expiry_dt - today).total_seconds()
        time_diff_days = time_diff_seconds / (24 * 3600)
        time_to_expiry_years = time_diff_seconds / (365.25 * 24 * 3600)
        
        print(f"{'Time Difference:':<30} {time_diff_seconds:,.0f} seconds")
        print(f"{'Time Difference:':<30} {time_diff_days:.2f} days")
        print(f"{'Time to Expiry (years):':<30} {time_to_expiry_years:.6f}")
        
        # Apply bounds
        from app_config import MIN_TIME_TO_EXPIRY, MAX_TIME_TO_EXPIRY
        time_to_expiry_bounded = max(MIN_TIME_TO_EXPIRY, min(MAX_TIME_TO_EXPIRY, time_to_expiry_years))
        
        print(f"{'Min Time to Expiry:':<30} {MIN_TIME_TO_EXPIRY:.6f} years ({MIN_TIME_TO_EXPIRY*365.25:.1f} days)")
        print(f"{'Max Time to Expiry:':<30} {MAX_TIME_TO_EXPIRY:.6f} years ({MAX_TIME_TO_EXPIRY*365.25:.1f} days)")
        print(f"{'Time to Expiry (bounded):':<30} {time_to_expiry_bounded:.6f} years ({time_to_expiry_bounded*365.25:.1f} days)")
        
        # Volatility bounds
        print_section("Step 5: Volatility Bounds Check")
        from app_config import MIN_VOLATILITY, MAX_VOLATILITY, DEFAULT_VOLATILITY
        
        volatility_raw = contract.implied_volatility
        volatility_used = volatility_raw if volatility_raw > 0 else DEFAULT_VOLATILITY
        volatility_bounded = max(MIN_VOLATILITY, min(MAX_VOLATILITY, volatility_used))
        
        print(f"{'Raw IV from market:':<30} {volatility_raw:.6f} ({volatility_raw*100:.2f}%)")
        print(f"{'Default IV (fallback):':<30} {DEFAULT_VOLATILITY:.6f} ({DEFAULT_VOLATILITY*100:.2f}%)")
        print(f"{'IV after zero check:':<30} {volatility_used:.6f} ({volatility_used*100:.2f}%)")
        print(f"{'Min IV allowed:':<30} {MIN_VOLATILITY:.6f} ({MIN_VOLATILITY*100:.2f}%)")
        print(f"{'Max IV allowed:':<30} {MAX_VOLATILITY:.6f} ({MAX_VOLATILITY*100:.2f}%)")
        print(f"{'IV used in calculation:':<30} {volatility_bounded:.6f} ({volatility_bounded*100:.2f}%)")
        
        # Black-Scholes calculation
        print_section("Step 6: Black-Scholes Gamma Calculation")
        
        risk_free_rate = DEFAULT_RISK_FREE_RATE
        
        print(f"{'Current Price (S):':<30} ${current_price:.2f}")
        print(f"{'Strike Price (K):':<30} ${strike:.2f}")
        print(f"{'Time to Expiry (T):':<30} {time_to_expiry_bounded:.6f} years")
        print(f"{'Volatility (σ):':<30} {volatility_bounded:.6f}")
        print(f"{'Risk-Free Rate (r):':<30} {risk_free_rate:.6f} ({risk_free_rate*100:.2f}%)")
        
        # Calculate d1
        print("\n--- Calculating d1 ---")
        
        ln_s_k = np.log(current_price / strike)
        print(f"{'ln(S/K):':<30} ln({current_price:.2f}/{strike:.2f}) = {ln_s_k:.8f}")
        
        vol_squared = volatility_bounded ** 2
        print(f"{'σ²:':<30} {volatility_bounded:.6f}² = {vol_squared:.8f}")
        
        r_plus_half_vol_sq = risk_free_rate + 0.5 * vol_squared
        print(f"{'r + 0.5σ²:':<30} {risk_free_rate:.6f} + 0.5×{vol_squared:.8f} = {r_plus_half_vol_sq:.8f}")
        
        r_plus_half_vol_sq_times_t = r_plus_half_vol_sq * time_to_expiry_bounded
        print(f"{'(r + 0.5σ²)×T:':<30} {r_plus_half_vol_sq:.8f} × {time_to_expiry_bounded:.6f} = {r_plus_half_vol_sq_times_t:.8f}")
        
        numerator = ln_s_k + r_plus_half_vol_sq_times_t
        print(f"{'Numerator:':<30} {ln_s_k:.8f} + {r_plus_half_vol_sq_times_t:.8f} = {numerator:.8f}")
        
        sqrt_t = np.sqrt(time_to_expiry_bounded)
        print(f"{'√T:':<30} √{time_to_expiry_bounded:.6f} = {sqrt_t:.8f}")
        
        vol_times_sqrt_t = volatility_bounded * sqrt_t
        print(f"{'σ×√T:':<30} {volatility_bounded:.6f} × {sqrt_t:.8f} = {vol_times_sqrt_t:.8f}")
        
        d1 = numerator / vol_times_sqrt_t
        print(f"{'d1:':<30} {numerator:.8f} / {vol_times_sqrt_t:.8f} = {d1:.8f}")
        
        # Calculate N'(d1) - standard normal PDF
        print("\n--- Calculating N'(d1) (Standard Normal PDF) ---")
        
        norm_pdf_d1 = norm.pdf(d1)
        print(f"{'N\'(d1):':<30} norm.pdf({d1:.8f}) = {norm_pdf_d1:.10f}")
        
        # Manual calculation for verification
        manual_pdf = (1 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * d1**2)
        print(f"{'Manual verification:':<30} (1/√(2π)) × e^(-0.5×d1²) = {manual_pdf:.10f}")
        
        # Calculate Gamma
        print("\n--- Calculating Gamma ---")
        
        s_times_vol_times_sqrt_t = current_price * vol_times_sqrt_t
        print(f"{'S × σ × √T:':<30} {current_price:.2f} × {vol_times_sqrt_t:.8f} = {s_times_vol_times_sqrt_t:.8f}")
        
        gamma = norm_pdf_d1 / s_times_vol_times_sqrt_t
        print(f"{'Gamma:':<30} {norm_pdf_d1:.10f} / {s_times_vol_times_sqrt_t:.8f} = {gamma:.10f}")
        
        print(f"\n{'GAMMA VALUE:':<30} {gamma:.10f}")
        
        # Calculate Exposure
        print_section("Step 7: Calculate Gamma Exposure")
        
        contract_multiplier = SPX_CONTRACT_MULTIPLIER
        
        print(f"{'Gamma:':<30} {gamma:.10f}")
        print(f"{'Open Interest:':<30} {contract.open_interest:,}")
        print(f"{'Contract Multiplier:':<30} {contract_multiplier:,}")
        print(f"{'Current Price (S):':<30} ${current_price:.2f}")
        
        raw_exposure = gamma * contract.open_interest * contract_multiplier * current_price
        print(f"\n{'Raw Exposure:':<30} {gamma:.10f} × {contract.open_interest:,} × {contract_multiplier:,} × {current_price:.2f}")
        print(f"{'Raw Exposure:':<30} {raw_exposure:,.2f}")
        
        # Apply sign convention
        print("\n--- Applying Sign Convention ---")
        
        if option_type == 'call':
            sign = -1
            sign_explanation = "Negative (Market makers short calls → negative gamma → resistance)"
            final_exposure = -raw_exposure
        else:
            sign = +1
            sign_explanation = "Positive (Market makers short puts → positive gamma → support)"
            final_exposure = raw_exposure
        
        print(f"{'Option Type:':<30} {option_type.upper()}")
        print(f"{'Sign Convention:':<30} {sign:+d}")
        print(f"{'Explanation:':<30} {sign_explanation}")
        print(f"{'Final Exposure:':<30} {sign:+d} × {raw_exposure:,.2f} = {final_exposure:,.2f}")
        
        # Summary
        print_section("Step 8: Summary")
        
        print(f"{'Symbol:':<30} {symbol}")
        print(f"{'Strike:':<30} ${strike:.2f}")
        print(f"{'Option Type:':<30} {option_type.upper()}")
        print(f"{'Expiration:':<30} {expiry_date}")
        print(f"{'Current Price:':<30} ${current_price:.2f}")
        print(f"{'Open Interest:':<30} {contract.open_interest:,}")
        print(f"{'Implied Volatility:':<30} {volatility_bounded*100:.2f}%")
        print(f"{'Days to Expiry:':<30} {time_to_expiry_bounded*365.25:.1f}")
        print(f"{'Gamma:':<30} {gamma:.10f}")
        print(f"{'Raw Exposure:':<30} {raw_exposure:,.2f}")
        print(f"{'Sign Convention:':<30} {sign:+d} ({option_type})")
        print(f"\n{'FINAL GAMMA EXPOSURE:':<30} {final_exposure:,.2f}")
        
        # Interpretation
        print_section("Step 9: Interpretation")
        
        if option_type == 'call':
            if final_exposure < 0:
                magnitude = abs(final_exposure)
                print(f"✅ This call option creates NEGATIVE gamma exposure of {magnitude:,.2f}")
                print(f"   • Market makers are short this call")
                print(f"   • They have negative gamma (need to buy as price rises)")
                print(f"   • This creates RESISTANCE at strike ${strike:.2f}")
                print(f"   • More negative = stronger resistance")
                
                distance = strike - current_price
                distance_pct = (distance / current_price) * 100
                
                if distance > 0:
                    print(f"\n   Strike is ${distance:.2f} ({distance_pct:.2f}%) ABOVE current price")
                    print(f"   • This is an OTM call")
                    print(f"   • Acts as resistance if price moves up")
                else:
                    print(f"\n   Strike is ${abs(distance):.2f} ({abs(distance_pct):.2f}%) BELOW current price")
                    print(f"   • This is an ITM call")
                    print(f"   • Already providing resistance")
            else:
                print(f"⚠️ Unusual: Call has positive exposure (typically calls are negative)")
        else:  # put
            if final_exposure > 0:
                magnitude = final_exposure
                print(f"✅ This put option creates POSITIVE gamma exposure of {magnitude:,.2f}")
                print(f"   • Market makers are short this put")
                print(f"   • They have positive gamma (need to sell as price falls)")
                print(f"   • This creates SUPPORT at strike ${strike:.2f}")
                print(f"   • More positive = stronger support")
                
                distance = current_price - strike
                distance_pct = (distance / current_price) * 100
                
                if distance > 0:
                    print(f"\n   Strike is ${distance:.2f} ({distance_pct:.2f}%) BELOW current price")
                    print(f"   • This is an OTM put")
                    print(f"   • Acts as support if price moves down")
                else:
                    print(f"\n   Strike is ${abs(distance):.2f} ({abs(distance_pct):.2f}%) ABOVE current price")
                    print(f"   • This is an ITM put")
                    print(f"   • Already providing support")
            else:
                print(f"⚠️ Unusual: Put has negative exposure (typically puts are positive)")
        
        # Formula reference
        print_section("Formula Reference")
        print("""
Black-Scholes Gamma Formula:
    d1 = [ln(S/K) + (r + 0.5σ²)T] / (σ√T)
    Gamma = N'(d1) / (S × σ × √T)
    
    Where:
    - S = Current price (spot)
    - K = Strike price
    - r = Risk-free rate
    - σ = Implied volatility
    - T = Time to expiry (years)
    - N'(d1) = Standard normal PDF at d1 = (1/√(2π)) × e^(-0.5×d1²)

Gamma Exposure Formula:
    Exposure = Gamma × Open Interest × Multiplier × S × Sign
    
    Where:
    - Sign = -1 for calls (resistance)
    - Sign = +1 for puts (support)
        """)
        
        print_separator()
        print("✅ Calculation complete!")
        print_separator()
        
        return 0
        
    except YFinanceFetchError as e:
        print(f"\n❌ ERROR fetching data: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Calculate GEX for a single strike and print all variables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_single_strike_gex.py SPY 2026-01-17 685 call
  python test_single_strike_gex.py SPY 2026-01-17 680 put
  python test_single_strike_gex.py QQQ 2026-01-31 500 call
  python test_single_strike_gex.py AAPL 2026-02-20 230 put
        """
    )
    
    parser.add_argument('symbol', help='Stock symbol (e.g., SPY, QQQ, AAPL)')
    parser.add_argument('expiry', help='Expiration date (YYYY-MM-DD)')
    parser.add_argument('strike', type=float, help='Strike price')
    parser.add_argument('type', choices=['call', 'put'], help='Option type (call or put)')
    
    args = parser.parse_args()
    
    return calculate_and_print_gex(
        symbol=args.symbol.upper(),
        expiry_date=args.expiry,
        strike=args.strike,
        option_type=args.type.lower()
    )


if __name__ == "__main__":
    sys.exit(main())
