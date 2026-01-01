#!/usr/bin/env python3
"""
Expected Move Calculator - Calculate expected price move based on implied volatility
Usage: python expected_move.py SYMBOL [EXPIRATION]
"""

import sys
import argparse
from datetime import datetime
import yfinance as yf
import pandas as pd
import math


def calculate_expected_move(current_price, implied_volatility, days_to_expiry):
    """
    Calculate expected move based on implied volatility
    
    Args:
        current_price: Current stock price
        implied_volatility: Implied volatility (as decimal, e.g., 0.25 for 25%)
        days_to_expiry: Days until expiration
    
    Returns:
        Dictionary with expected move calculations
    """
    # Expected move = Price × IV × √(DTE / 365)
    time_factor = math.sqrt(days_to_expiry / 365)
    expected_move_1sd = current_price * implied_volatility * time_factor
    
    # 2 standard deviations (≈95% probability)
    expected_move_2sd = expected_move_1sd * 2
    
    # Calculate price ranges
    upper_1sd = current_price + expected_move_1sd
    lower_1sd = current_price - expected_move_1sd
    
    upper_2sd = current_price + expected_move_2sd
    lower_2sd = current_price - expected_move_2sd
    
    # Percentage moves
    move_pct_1sd = (expected_move_1sd / current_price) * 100
    move_pct_2sd = (expected_move_2sd / current_price) * 100
    
    return {
        'current_price': current_price,
        'implied_volatility': implied_volatility,
        'iv_percentage': implied_volatility * 100,
        'days_to_expiry': days_to_expiry,
        'expected_move_1sd': expected_move_1sd,
        'expected_move_2sd': expected_move_2sd,
        'move_pct_1sd': move_pct_1sd,
        'move_pct_2sd': move_pct_2sd,
        'upper_1sd': upper_1sd,
        'lower_1sd': lower_1sd,
        'upper_2sd': upper_2sd,
        'lower_2sd': lower_2sd,
        'probability_1sd': 68.2,
        'probability_2sd': 95.4
    }


def get_atm_iv(symbol, expiration=None):
    """
    Get at-the-money implied volatility for a symbol
    
    Args:
        symbol: Stock symbol
        expiration: Expiration date or None for nearest
    
    Returns:
        Tuple of (current_price, atm_iv, days_to_expiry, expiration_date)
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Get current price
        info = ticker.info
        current_price = info.get('regularMarketPrice') or info.get('previousClose')
        if current_price is None:
            hist = ticker.history(period='1d')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
        
        if current_price is None:
            raise ValueError("Could not fetch current price")
        
        # Get expirations
        expirations = ticker.options
        if not expirations:
            raise ValueError(f"No options available for {symbol}")
        
        # Select expiration
        if expiration and expiration in expirations:
            selected_exp = expiration
        else:
            selected_exp = expirations[0]
        
        # Get options chain
        chain = ticker.option_chain(selected_exp)
        
        # Find ATM strike (closest to current price)
        calls = chain.calls
        calls['distance'] = abs(calls['strike'] - current_price)
        atm_call = calls.loc[calls['distance'].idxmin()]
        
        atm_iv = atm_call['impliedVolatility']
        atm_strike = atm_call['strike']
        
        # Calculate days to expiry
        exp_date = datetime.strptime(selected_exp, '%Y-%m-%d')
        today = datetime.now()
        days_to_expiry = max(1, (exp_date - today).days)
        
        return current_price, atm_iv, days_to_expiry, selected_exp, atm_strike
        
    except Exception as e:
        raise ValueError(f"Error fetching data: {str(e)}")


def display_expected_move(symbol, expiration=None):
    """Display expected move analysis for a symbol"""
    try:
        print(f"\n📊 Expected Move Analysis: {symbol}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Get ATM IV
        print(f"⏳ Fetching options data...")
        current_price, atm_iv, days_to_expiry, exp_date, atm_strike = get_atm_iv(symbol, expiration)
        
        print(f"✅ Data retrieved successfully!")
        print(f"\n📈 Current Market Data:")
        print(f"   Symbol: {symbol}")
        print(f"   Current Price: ${current_price:.2f}")
        print(f"   Expiration: {exp_date}")
        print(f"   Days to Expiry: {days_to_expiry}")
        print(f"   ATM Strike: ${atm_strike:.2f}")
        print(f"   ATM Implied Volatility: {atm_iv * 100:.2f}%")
        
        # Calculate expected move
        move = calculate_expected_move(current_price, atm_iv, days_to_expiry)
        
        # Display 1 Standard Deviation (68% probability)
        print(f"\n🎯 EXPECTED MOVE (1 Standard Deviation)")
        print("-" * 70)
        print(f"   Probability: ~{move['probability_1sd']:.1f}% chance price stays within this range")
        print(f"   Expected Move: ±${move['expected_move_1sd']:.2f} (±{move['move_pct_1sd']:.2f}%)")
        print(f"")
        print(f"   📊 Price Range:")
        print(f"      Upper Bound: ${move['upper_1sd']:.2f} (+{move['move_pct_1sd']:.2f}%)")
        print(f"      Current:     ${move['current_price']:.2f}")
        print(f"      Lower Bound: ${move['lower_1sd']:.2f} (-{move['move_pct_1sd']:.2f}%)")
        
        # Display 2 Standard Deviations (95% probability)
        print(f"\n🎯 EXPECTED MOVE (2 Standard Deviations)")
        print("-" * 70)
        print(f"   Probability: ~{move['probability_2sd']:.1f}% chance price stays within this range")
        print(f"   Expected Move: ±${move['expected_move_2sd']:.2f} (±{move['move_pct_2sd']:.2f}%)")
        print(f"")
        print(f"   📊 Price Range:")
        print(f"      Upper Bound: ${move['upper_2sd']:.2f} (+{move['move_pct_2sd']:.2f}%)")
        print(f"      Current:     ${move['current_price']:.2f}")
        print(f"      Lower Bound: ${move['lower_2sd']:.2f} (-{move['move_pct_2sd']:.2f}%)")
        
        # Trading implications
        print(f"\n💡 TRADING IMPLICATIONS")
        print("-" * 70)
        
        if days_to_expiry <= 7:
            print(f"   ⚡ SHORT-TERM EXPIRATION ({days_to_expiry} days)")
            print(f"      • Smaller expected move due to time decay")
            print(f"      • Good for theta strategies (selling premium)")
            print(f"      • Higher gamma risk near expiration")
        elif days_to_expiry <= 30:
            print(f"   📅 MEDIUM-TERM EXPIRATION ({days_to_expiry} days)")
            print(f"      • Moderate expected move")
            print(f"      • Balanced risk/reward for most strategies")
            print(f"      • Consider both directional and neutral strategies")
        else:
            print(f"   📆 LONG-TERM EXPIRATION ({days_to_expiry} days)")
            print(f"      • Larger expected move due to more time")
            print(f"      • Better for directional plays")
            print(f"      • Lower theta decay per day")
        
        print(f"\n   🎯 Strategy Suggestions:")
        
        # Iron Condor suggestion
        print(f"      Iron Condor: Sell strikes outside 1SD range")
        print(f"         • Sell {move['upper_1sd']:.0f} call / Buy {move['upper_2sd']:.0f} call")
        print(f"         • Sell {move['lower_1sd']:.0f} put / Buy {move['lower_2sd']:.0f} put")
        
        # Straddle/Strangle suggestion
        print(f"\n      Long Straddle/Strangle: Profit if move exceeds 1SD")
        print(f"         • Breakeven needs move > ${move['expected_move_1sd']:.2f}")
        print(f"         • Consider if expecting volatility expansion")
        
        # Covered Call suggestion
        print(f"\n      Covered Call: Sell calls at upper 1SD")
        print(f"         • Strike: ~${move['upper_1sd']:.0f}")
        print(f"         • {move['probability_1sd']:.1f}% chance of keeping premium")
        
        # Risk Assessment
        print(f"\n   ⚠️ Risk Assessment:")
        if move['iv_percentage'] > 40:
            print(f"      🔴 HIGH IV ({move['iv_percentage']:.1f}%) - Large expected move")
            print(f"         • Premium selling may be attractive")
            print(f"         • Buying options is expensive")
            print(f"         • Consider volatility contraction")
        elif move['iv_percentage'] > 25:
            print(f"      🟡 MODERATE IV ({move['iv_percentage']:.1f}%) - Normal expected move")
            print(f"         • Balanced environment for most strategies")
            print(f"         • Standard risk management applies")
        else:
            print(f"      🟢 LOW IV ({move['iv_percentage']:.1f}%) - Small expected move")
            print(f"         • Buying options may be attractive")
            print(f"         • Premium selling less profitable")
            print(f"         • Consider volatility expansion")
        
        # Probability table
        print(f"\n📊 PROBABILITY TABLE")
        print("-" * 70)
        print(f"   Range                          Probability    Price Range")
        print(f"   {'─' * 70}")
        print(f"   Within 1 SD (±{move['move_pct_1sd']:.1f}%)         ~68.2%         ${move['lower_1sd']:.2f} - ${move['upper_1sd']:.2f}")
        print(f"   Within 2 SD (±{move['move_pct_2sd']:.1f}%)         ~95.4%         ${move['lower_2sd']:.2f} - ${move['upper_2sd']:.2f}")
        print(f"   Beyond 2 SD                    ~4.6%          <${move['lower_2sd']:.2f} or >${move['upper_2sd']:.2f}")
        
        print(f"\n✅ Analysis complete for {symbol}")
        return move
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Calculate expected move based on implied volatility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate expected move for SPY (nearest expiration)
  python expected_move.py SPY
  
  # Calculate for specific expiration
  python expected_move.py SPY 2025-01-17
  
  # Calculate for any stock
  python expected_move.py AAPL
  python expected_move.py TSLA 2025-02-21
  
  # Compare multiple symbols
  python expected_move.py SPY && python expected_move.py QQQ
        """
    )
    
    parser.add_argument('symbol', help='Stock symbol (e.g., SPY, AAPL, TSLA)')
    parser.add_argument('expiration', nargs='?', help='Expiration date (YYYY-MM-DD) or omit for nearest')
    
    args = parser.parse_args()
    
    symbol = args.symbol.upper()
    expiration = args.expiration
    
    result = display_expected_move(symbol, expiration)
    
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
