#!/usr/bin/env python3
"""
Gamma Exposure Calculator - Command Line Interface
Usage: python gamma_cli.py [symbol] [expiration_option]

Examples:
  python gamma_cli.py SPY                    # SPY with nearest expiration
  python gamma_cli.py SPY specific           # SPY with specific expiration selection
  python gamma_cli.py QQQ multiple           # QQQ with multiple expirations
"""

import sys
import argparse
import math
import csv
from datetime import datetime
from typing import Optional

# Import our modules
from data.yfinance_fetcher import YFinanceOptionsFetcher, YFinanceFetchError
from calculations.gamma import GammaCalculator, GammaCalculationError
from analysis.walls import WallAnalyzer, WallAnalysisError
from analysis.metrics import MetricsCalculator, MetricsCalculationError


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n📊 {title}")
    print("-" * 60)


def print_metric(label: str, value: str, description: str = ""):
    """Print formatted metric"""
    if description:
        print(f"{label:.<30} {value} ({description})")
    else:
        print(f"{label:.<30} {value}")


def display_gamma_environment(gamma_env: dict, current_price: float):
    """Display gamma environment analysis (compact)"""
    print_section("Gamma Environment Analysis")
    
    # Environment type
    env_type = gamma_env['environment'].upper()
    if gamma_env['environment'] == 'positive':
        env_icon = "🛡️"
        env_desc = "Stabilizing"
    elif gamma_env['environment'] == 'negative':
        env_icon = "⚡"
        env_desc = "Amplifying"
    else:
        env_icon = "⚖️"
        env_desc = "Balanced"
    
    strength_info = gamma_env['strength_interpretation']
    
    # Compact single-line display
    print(f"{env_icon} {env_type} ({env_desc}) | Strength: {strength_info['level']} {strength_info['color']} | {strength_info['volatility_impact']}")
    
    # Gamma flip level on same line if exists
    if gamma_env['gamma_flip_level']:
        flip_level = gamma_env['gamma_flip_level']
        flip_distance_pct = ((flip_level - current_price) / current_price) * 100
        print(f"🎯 Flip Level: {flip_level:.0f} ({flip_distance_pct:+.1f}%) | Pos: {gamma_env['positive_strikes']} ({gamma_env['positive_strike_percentage']:.0f}%) | Neg: {gamma_env['negative_strikes']} ({gamma_env['negative_strike_percentage']:.0f}%)")
    else:
        print(f"🎯 No Flip Level | Pos: {gamma_env['positive_strikes']} ({gamma_env['positive_strike_percentage']:.0f}%) | Neg: {gamma_env['negative_strikes']} ({gamma_env['negative_strike_percentage']:.0f}%)")


def display_key_metrics(market_metrics, walls: dict):
    """Display key metrics (compact)"""
    print_section("Key Metrics")
    
    total_walls = len(walls['call_walls']) + len(walls['put_walls'])
    
    # Display in two columns
    print(f"{'Net Gamma:':<25} {market_metrics.total_net_gamma:>15,.0f}    {'Call/Put Ratio:':<25} {market_metrics.call_put_gamma_ratio:>10.2f}")
    print(f"{'Weighted Avg Strike:':<25} {market_metrics.gamma_weighted_avg_strike:>15,.0f}    {'Total Walls:':<25} {total_walls:>10}")
    print(f"{'Max Call Exposure:':<25} {market_metrics.max_call_exposure:>15,.0f}    {'Gamma Std Dev:':<25} {market_metrics.gamma_exposure_std:>10,.0f}")
    print(f"{'Max Put Exposure:':<25} {market_metrics.max_put_exposure:>15,.0f}")


def display_walls(walls: dict, current_price: float):
    """Display gamma walls in two columns"""
    print_section("Gamma Walls")
    
    call_walls = walls.get('call_walls', [])
    put_walls = walls.get('put_walls', [])
    
    if not call_walls and not put_walls:
        print("No significant gamma walls identified")
        return
    
    # Show top 5 of each
    max_walls = max(len(call_walls[:5]), len(put_walls[:5]))
    
    # Print header
    print(f"{'🔴 Call Walls (Resistance)':<50} {'🟢 Put Walls (Support)':<50}")
    print(f"{'='*48} {'='*48}")
    
    # Print walls side by side
    for i in range(max_walls):
        # Call wall column
        if i < len(call_walls[:5]):
            wall = call_walls[i]
            distance_pct = (wall.distance_from_spot / current_price) * 100
            call_text = f"#{wall.significance_rank}: {wall.strike:.0f} ({distance_pct:+.1f}%) - {wall.exposure_value:,.0f}"
        else:
            call_text = ""
        
        # Put wall column
        if i < len(put_walls[:5]):
            wall = put_walls[i]
            distance_pct = (wall.distance_from_spot / current_price) * 100
            put_text = f"#{wall.significance_rank}: {wall.strike:.0f} ({distance_pct:+.1f}%) - {wall.exposure_value:,.0f}"
        else:
            put_text = ""
        
        # Print both columns
        print(f"{call_text:<50} {put_text:<50}")


def calculate_expected_move(current_price: float, implied_volatility: float, days_to_expiry: int) -> dict:
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


def get_atm_iv_from_contracts(contracts: list, current_price: float) -> tuple:
    """
    Get at-the-money implied volatility from contracts
    Uses average IV of closest 10 contracts to current price (both calls and puts)
    
    Args:
        contracts: List of option contracts
        current_price: Current stock price
    
    Returns:
        Tuple of (atm_iv, days_to_expiry, closest_strike, num_contracts_used)
    """
    if not contracts:
        return None, None, None, 0
    
    # Sort all contracts by distance from current price
    contracts_with_distance = [(c, abs(c.strike - current_price)) for c in contracts]
    contracts_with_distance.sort(key=lambda x: x[1])
    
    # Use ATM IV (average of closest 10 contracts, or all if less than 10)
    atm_contracts = [c for c, _ in contracts_with_distance[:min(10, len(contracts_with_distance))]]
    
    if not atm_contracts:
        return None, None, None, 0
    
    # Calculate average IV from ATM contracts
    avg_iv = sum(c.implied_volatility for c in atm_contracts) / len(atm_contracts)
    
    # Get the closest strike for reference
    closest_strike = atm_contracts[0].strike
    
    # Calculate average days to expiry
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days_to_expiry_list = []
    for c in atm_contracts:
        expiry = c.expiry_date if isinstance(c.expiry_date, datetime) else datetime.fromisoformat(str(c.expiry_date))
        # Normalize expiry to midnight if it has time component
        expiry = expiry.replace(hour=0, minute=0, second=0, microsecond=0)
        dte = max(1, (expiry - today).days)
        days_to_expiry_list.append(dte)
    
    avg_dte = sum(days_to_expiry_list) / len(days_to_expiry_list)
    
    return avg_iv, int(avg_dte), closest_strike, len(atm_contracts)


def display_expected_move(contracts: list, current_price: float):
    """Display expected move analysis"""
    print_section("Expected Move (Based on Implied Volatility)")
    
    # Get ATM IV (now returns 4 values)
    atm_iv, days_to_expiry, closest_strike, num_contracts = get_atm_iv_from_contracts(contracts, current_price)
    
    if atm_iv is None or days_to_expiry is None:
        print("⚠️ Could not calculate expected move - no ATM options data available")
        return
    
    print(f"📊 ATM IV (avg of {num_contracts} closest strikes): {atm_iv * 100:.2f}%")
    print(f"📊 Closest Strike: ${closest_strike:.2f}")
    print(f"📅 Days to Expiry: {days_to_expiry}")
    
    # Calculate expected move
    move = calculate_expected_move(current_price, atm_iv, days_to_expiry)
    
    # Display 1 Standard Deviation (68% probability)
    print(f"\n🎯 1 Standard Deviation (~{move['probability_1sd']:.1f}% probability)")
    print(f"   Expected Move: ±${move['expected_move_1sd']:.2f} (±{move['move_pct_1sd']:.2f}%)")
    print(f"   Price Range: ${move['lower_1sd']:.2f} - ${move['upper_1sd']:.2f}")
    
    # Display 2 Standard Deviations (95% probability)
    print(f"\n🎯 2 Standard Deviations (~{move['probability_2sd']:.1f}% probability)")
    print(f"   Expected Move: ±${move['expected_move_2sd']:.2f} (±{move['move_pct_2sd']:.2f}%)")
    print(f"   Price Range: ${move['lower_2sd']:.2f} - ${move['upper_2sd']:.2f}")
    
    # Compact IV and Time assessment on one line
    if move['iv_percentage'] > 40:
        iv_status = f"🔴 HIGH IV ({move['iv_percentage']:.1f}%)"
    elif move['iv_percentage'] > 25:
        iv_status = f"🟡 MODERATE IV ({move['iv_percentage']:.1f}%)"
    else:
        iv_status = f"🟢 LOW IV ({move['iv_percentage']:.1f}%)"
    
    if days_to_expiry <= 7:
        dte_status = f"⚡ SHORT-TERM ({days_to_expiry}d)"
    elif days_to_expiry <= 30:
        dte_status = f"📅 MEDIUM-TERM ({days_to_expiry}d)"
    else:
        dte_status = f"📆 LONG-TERM ({days_to_expiry}d)"
    
    print(f"\n{iv_status} | {dte_status}")


def display_trading_implications(gamma_env: dict, walls: dict, current_price: float):
    """Display trading implications (compact)"""
    print_section("Trading Implications")
    
    # Compact single-line implications
    if gamma_env['environment'] == 'positive':
        print("🛡️ Positive Gamma: Stabilizing force | Buy dips, sell rallies | Lower volatility | Mean-reverting")
    elif gamma_env['environment'] == 'negative':
        print("⚡ Negative Gamma: Amplifying force | Momentum/trend following | Higher volatility | Trending")
    else:
        print("⚖️ Neutral Gamma: Balanced forces | Mixed influence | Moderate volatility")
    
    # Get strength info from gamma_env
    strength_info = gamma_env['strength_interpretation']
    
    # Strength implications
    print(f"\n💪 Strength Implications ({strength_info['level']}):")
    if strength_info['level'] in ['Very Strong', 'Strong']:
        print("   • High confidence in gamma effects")
        print("   • Strong support/resistance at walls")
        print("   • Gamma analysis is primary factor")
    elif strength_info['level'] == 'Moderate':
        print("   • Moderate confidence in gamma effects")
        print("   • Consider gamma alongside other factors")
        print("   • Noticeable but not dominant influence")
    else:
        print("   • Low confidence in gamma effects")
        print("   • Other factors likely more important")
        print("   • Gamma analysis is secondary")
    
    # Flip level implications
    if gamma_env['gamma_flip_level']:
        flip_level = gamma_env['gamma_flip_level']
        flip_distance = flip_level - current_price
        
        print(f"\n🎯 Key Level to Watch: {flip_level:.0f}")
        if abs(flip_distance) / current_price < 0.05:  # Within 5%
            print(f"   ⚠️ CRITICAL: Only {abs(flip_distance):.0f} points away!")
            print("   • Environment could flip with small move")
            print("   • High probability of volatility change")


def export_gamma_details_to_csv(contracts: list, current_price: float, gamma_calc, filename: str = None):
    """
    Export detailed gamma calculations to CSV for debugging
    
    Args:
        contracts: List of option contracts
        current_price: Current underlying price
        gamma_calc: GammaCalculator instance
        filename: Output filename (default: gamma_details_SYMBOL_TIMESTAMP.csv)
    """
    if not contracts:
        print("⚠️ No contracts to export")
        return
    
    # Generate filename if not provided
    if filename is None:
        symbol = contracts[0].symbol if hasattr(contracts[0], 'symbol') else 'OPTIONS'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"gamma_details_{symbol}_{timestamp}.csv"
    
    print(f"\n📊 Exporting detailed gamma calculations to: {filename}")
    
    # Prepare data for export
    rows = []
    
    for contract in contracts:
        try:
            # Calculate time to expiry
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            expiry = contract.expiry_date if isinstance(contract.expiry_date, datetime) else datetime.fromisoformat(str(contract.expiry_date))
            expiry = expiry.replace(hour=0, minute=0, second=0, microsecond=0)
            days_to_expiry = max(1, (expiry - today).days)
            time_to_expiry = days_to_expiry / 365.25
            
            # Get volatility
            volatility = contract.implied_volatility if contract.implied_volatility > 0 else 0.20
            
            # Apply same bounds as gamma calculator
            from app_config import MIN_VOLATILITY, MAX_VOLATILITY
            volatility = max(MIN_VOLATILITY, min(MAX_VOLATILITY, volatility))
            
            # Calculate d1 for Black-Scholes
            import numpy as np
            from scipy.stats import norm
            
            d1 = (np.log(current_price / contract.strike) + 
                  (gamma_calc.risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / \
                 (volatility * np.sqrt(time_to_expiry))
            
            # Calculate gamma (same for calls and puts)
            gamma = norm.pdf(d1) / (current_price * volatility * np.sqrt(time_to_expiry))
            
            # Calculate exposure
            exposure_base = gamma * contract.open_interest * gamma_calc.contract_multiplier * current_price
            
            # Apply sign convention
            if contract.option_type == 'call':
                gamma_exposure = -exposure_base  # Negative for calls (resistance)
            else:
                gamma_exposure = exposure_base   # Positive for puts (support)
            
            # Distance from current price
            distance = contract.strike - current_price
            distance_pct = (distance / current_price) * 100
            
            # Moneyness
            if abs(distance_pct) < 2:
                moneyness = "ATM"
            elif contract.option_type == 'call' and distance > 0:
                moneyness = "OTM"
            elif contract.option_type == 'call' and distance < 0:
                moneyness = "ITM"
            elif contract.option_type == 'put' and distance < 0:
                moneyness = "OTM"
            else:
                moneyness = "ITM"
            
            row = {
                'Strike': contract.strike,
                'Type': contract.option_type.upper(),
                'Expiry_Date': contract.expiry_date.strftime('%Y-%m-%d'),
                'Days_To_Expiry': days_to_expiry,
                'Time_To_Expiry_Years': f"{time_to_expiry:.6f}",
                'Open_Interest': contract.open_interest,
                'Implied_Volatility': f"{volatility:.4f}",
                'IV_Percent': f"{volatility*100:.2f}%",
                'Current_Price': current_price,
                'Distance_From_Spot': f"{distance:.2f}",
                'Distance_Percent': f"{distance_pct:.2f}%",
                'Moneyness': moneyness,
                'd1': f"{d1:.6f}",
                'norm_pdf_d1': f"{norm.pdf(d1):.8f}",
                'Gamma': f"{gamma:.8f}",
                'Contract_Multiplier': gamma_calc.contract_multiplier,
                'Exposure_Base': f"{exposure_base:.2f}",
                'Gamma_Exposure': f"{gamma_exposure:.2f}",
                'Sign_Convention': 'Negative (Resistance)' if contract.option_type == 'call' else 'Positive (Support)',
                'Risk_Free_Rate': gamma_calc.risk_free_rate
            }
            
            rows.append(row)
            
        except Exception as e:
            print(f"Warning: Could not process contract {contract.strike} {contract.option_type}: {e}")
            continue
    
    # Write to CSV
    if rows:
        fieldnames = [
            'Strike', 'Type', 'Expiry_Date', 'Days_To_Expiry', 'Time_To_Expiry_Years',
            'Open_Interest', 'Implied_Volatility', 'IV_Percent', 'Current_Price',
            'Distance_From_Spot', 'Distance_Percent', 'Moneyness',
            'd1', 'norm_pdf_d1', 'Gamma', 'Contract_Multiplier',
            'Exposure_Base', 'Gamma_Exposure', 'Sign_Convention', 'Risk_Free_Rate'
        ]
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"✅ Exported {len(rows)} contracts to {filename}")
        print(f"\n📋 Formula Summary:")
        print(f"   d1 = [ln(S/K) + (r + 0.5*σ²)*T] / (σ*√T)")
        print(f"   Gamma = N'(d1) / (S * σ * √T)")
        print(f"   Exposure = Gamma × OI × Multiplier × S")
        print(f"   Call Exposure = -Exposure (negative/resistance)")
        print(f"   Put Exposure = +Exposure (positive/support)")
        print(f"\n   Where:")
        print(f"   S = Current Price (${current_price:.2f})")
        print(f"   K = Strike Price")
        print(f"   r = Risk-Free Rate ({gamma_calc.risk_free_rate})")
        print(f"   σ = Implied Volatility")
        print(f"   T = Time to Expiry (years)")
        print(f"   N'(d1) = Standard normal PDF at d1")
        print(f"   OI = Open Interest")
        print(f"   Multiplier = {gamma_calc.contract_multiplier}")
    else:
        print("❌ No data to export")


def display_gamma_flip_debug(gamma_exposures: list, current_price: float, gamma_environment: dict):
    """
    Display detailed gamma flip level calculation walkthrough
    
    Args:
        gamma_exposures: List of GammaExposure objects
        current_price: Current underlying price
        gamma_environment: Gamma environment dictionary with flip level
    """
    print_section("Gamma Flip Level - Debug Walkthrough")
    
    flip_level = gamma_environment.get('gamma_flip_level')
    
    if not flip_level:
        print("⚠️ No gamma flip level detected")
        return
    
    # Sort exposures by strike
    sorted_exposures = sorted(gamma_exposures, key=lambda x: x.strike)
    
    # Find strikes around current price (±$20 range)
    price_range = 20
    relevant_strikes = [ge for ge in sorted_exposures 
                       if abs(ge.strike - current_price) <= price_range]
    
    if not relevant_strikes:
        print("⚠️ No strikes found near current price")
        return
    
    print(f"\n📊 Current Price: ${current_price:.2f}")
    print(f"🎯 Detected Flip Level: ${flip_level:.0f}")
    print(f"📏 Distance: ${flip_level - current_price:+.2f} ({((flip_level - current_price)/current_price)*100:+.2f}%)")
    
    print(f"\n{'='*80}")
    print(f"{'Strike':<8} | {'Net Gamma':>18} | {'Sign':<6} | {'Analysis':<30}")
    print(f"{'='*80}")
    
    # Track sign changes
    sign_changes = []
    
    for i, ge in enumerate(relevant_strikes):
        strike = ge.strike
        net_gamma = ge.net_gamma_exposure
        sign = '+' if net_gamma > 0 else '-'
        
        # Determine analysis text
        analysis = ""
        
        # Check if this is near current price
        if abs(strike - current_price) < 1:
            analysis = "← Current Price"
        
        # Check for sign change with next strike
        if i < len(relevant_strikes) - 1:
            next_ge = relevant_strikes[i + 1]
            next_gamma = next_ge.net_gamma_exposure
            
            # Detect sign change
            if (net_gamma > 0 and next_gamma < 0) or (net_gamma < 0 and next_gamma > 0):
                flip_magnitude = abs(net_gamma) + abs(next_gamma)
                interpolated_flip = (strike + next_ge.strike) / 2
                
                sign_changes.append({
                    'strike1': strike,
                    'strike2': next_ge.strike,
                    'gamma1': net_gamma,
                    'gamma2': next_gamma,
                    'magnitude': flip_magnitude,
                    'flip_level': interpolated_flip
                })
                
                if net_gamma > 0:
                    analysis = "← Last Positive"
                else:
                    analysis = "← Last Negative"
        
        # Check if next strike is a flip
        if i > 0:
            prev_ge = relevant_strikes[i - 1]
            prev_gamma = prev_ge.net_gamma_exposure
            
            if (prev_gamma > 0 and net_gamma < 0) or (prev_gamma < 0 and net_gamma > 0):
                if prev_gamma > 0:
                    analysis = "← First Negative ⚠️ FLIP!"
                else:
                    analysis = "← First Positive ⚠️ FLIP!"
        
        # Color coding for display
        if net_gamma > 0:
            gamma_str = f"+{net_gamma:>17,.0f}"
        else:
            gamma_str = f"{net_gamma:>18,.0f}"
        
        print(f"{strike:<8.0f} | {gamma_str} | {sign:<6} | {analysis:<30}")
    
    # Display detected sign changes
    if sign_changes:
        print(f"\n{'='*80}")
        print("🔍 Sign Changes Detected:")
        print(f"{'='*80}")
        
        for idx, change in enumerate(sign_changes, 1):
            print(f"\n{idx}. Between Strike {change['strike1']:.0f} and {change['strike2']:.0f}:")
            print(f"   Strike {change['strike1']:.0f}: {change['gamma1']:>+18,.0f} ({'positive' if change['gamma1'] > 0 else 'negative'})")
            print(f"   Strike {change['strike2']:.0f}: {change['gamma2']:>+18,.0f} ({'positive' if change['gamma2'] > 0 else 'negative'})")
            print(f"   Flip Magnitude: {change['magnitude']:>18,.0f}")
            print(f"   Interpolated Flip Level: ${change['flip_level']:.2f}")
            
            # Mark the winner
            if abs(change['flip_level'] - flip_level) < 1:
                print(f"   ⭐ SELECTED (Largest Magnitude)")
    
    # Interpretation
    print(f"\n{'='*80}")
    print("📖 Interpretation:")
    print(f"{'='*80}")
    
    if current_price < flip_level:
        distance = flip_level - current_price
        distance_pct = (distance / current_price) * 100
        
        print(f"\n✅ Current Position: BELOW flip level")
        print(f"   • You are in POSITIVE gamma territory")
        print(f"   • Market makers provide SUPPORT (buy dips, sell rallies)")
        print(f"   • Stabilizing force on price")
        print(f"   • Distance to flip: ${distance:.2f} ({distance_pct:.2f}%)")
        
        if distance_pct < 1:
            print(f"\n   ⚠️ CRITICAL: Only {distance_pct:.2f}% away from flip!")
            print(f"   • Small move could change environment")
            print(f"   • Watch for breakout above ${flip_level:.0f}")
        
        print(f"\n   If price rises above ${flip_level:.0f}:")
        print(f"   • Environment flips to NEGATIVE gamma")
        print(f"   • Market makers AMPLIFY moves (momentum)")
        print(f"   • Potential for acceleration/breakout")
    else:
        distance = current_price - flip_level
        distance_pct = (distance / current_price) * 100
        
        print(f"\n⚠️ Current Position: ABOVE flip level")
        print(f"   • You are in NEGATIVE gamma territory")
        print(f"   • Market makers AMPLIFY moves (sell dips, buy rallies)")
        print(f"   • Momentum/trending environment")
        print(f"   • Distance from flip: ${distance:.2f} ({distance_pct:.2f}%)")
        
        if distance_pct < 1:
            print(f"\n   ⚠️ CRITICAL: Only {distance_pct:.2f}% above flip!")
            print(f"   • Small move could change environment")
            print(f"   • Watch for breakdown below ${flip_level:.0f}")
        
        print(f"\n   If price falls below ${flip_level:.0f}:")
        print(f"   • Environment flips to POSITIVE gamma")
        print(f"   • Market makers provide SUPPORT")
        print(f"   • Potential for stabilization")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Gamma Exposure Calculator - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gamma_cli.py SPY                           # SPY with nearest expiration
  python gamma_cli.py SPY 2025-01-17               # SPY with specific date
  python gamma_cli.py SPY specific                  # SPY with interactive selection
  python gamma_cli.py QQQ multiple                  # QQQ with multiple expirations
  python gamma_cli.py --list-symbols                # Show available symbols
  python gamma_cli.py --list-expirations SPY       # Show SPY expirations
  python gamma_cli.py SPY --export-csv              # Export detailed calculations to CSV
  python gamma_cli.py SPY --export-csv --csv-filename my_analysis.csv  # Custom filename
  python gamma_cli.py SPY --debug-flip              # Show gamma flip level walkthrough
  python gamma_cli.py SPY --debug                   # Enable debug mode (print all variables)
        """
    )
    
    parser.add_argument('symbol', nargs='?', default='SPY', 
                       help='Symbol to analyze (default: SPY)')
    parser.add_argument('expiration', nargs='?', default='nearest',
                       help='Expiration date (YYYY-MM-DD) or selection mode (nearest/specific/multiple)')
    parser.add_argument('--list-symbols', action='store_true',
                       help='List available symbols and exit')
    parser.add_argument('--list-expirations', metavar='SYMBOL',
                       help='List available expirations for a symbol and exit')
    parser.add_argument('--risk-free-rate', type=float, default=0.05,
                       help='Risk-free rate (default: 0.05)')
    parser.add_argument('--export-csv', action='store_true',
                       help='Export detailed gamma calculations to CSV file')
    parser.add_argument('--csv-filename', type=str, default=None,
                       help='Custom filename for CSV export')
    parser.add_argument('--debug-flip', action='store_true',
                       help='Show detailed gamma flip level calculation walkthrough')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode to print all calculation variables')
    
    args = parser.parse_args()
    
    try:
        # Initialize fetcher
        fetcher = YFinanceOptionsFetcher()
        
        # List symbols if requested
        if args.list_symbols:
            print("Available symbols:")
            for symbol, yf_symbol in fetcher.get_available_symbols().items():
                print(f"  {symbol}: {yf_symbol}")
            return
        
        # List expirations if requested
        if args.list_expirations:
            symbol = args.list_expirations.upper()
            print(f"Available expirations for {symbol}:")
            try:
                expirations = fetcher.get_expiration_dates(symbol)
                for i, exp_date in enumerate(expirations, 1):
                    print(f"  {i:2d}. {exp_date}")
            except YFinanceFetchError as e:
                print(f"Error: {e}")
            return
        
        symbol = args.symbol.upper()
        
        print_header(f"Gamma Exposure Analysis - {symbol}")
        #print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get current price
        #print("\n📈 Fetching current price...")
        try:
            current_price = fetcher.get_current_price(symbol)
            print(f"Current {symbol} Price: ${current_price:.2f}")
        except YFinanceFetchError as e:
            print(f"Warning: Could not fetch current price: {e}")
            current_price = 4500.0  # Default fallback
        
        # Get expiration dates
        #print("\n📅 Fetching expiration dates...")
        expirations = fetcher.get_expiration_dates(symbol)
        #print(f"Available expirations: {len(expirations)}")
        
        # Determine expiration to use
        selected_expiration = None
        include_all = False
        
        # Check if expiration is a date (YYYY-MM-DD format)
        if args.expiration and len(args.expiration) == 10 and args.expiration.count('-') == 2:
            # Direct date specified
            if args.expiration in expirations:
                selected_expiration = args.expiration
                print(f"Using specified expiration: {selected_expiration}")
            else:
                print(f"Warning: Expiration {args.expiration} not available")
                print("Available expirations:")
                for i, exp_date in enumerate(expirations[:10], 1):
                    print(f"  {i}. {exp_date}")
                print("Using nearest expiration instead")
        elif args.expiration == 'specific' and len(expirations) > 1:
            print("\nAvailable expiration dates:")
            for i, exp_date in enumerate(expirations[:10], 1):
                print(f"  {i}. {exp_date}")
            
            try:
                choice = input(f"\nSelect expiration (1-{min(10, len(expirations))}): ")
                idx = int(choice) - 1
                if 0 <= idx < len(expirations):
                    selected_expiration = expirations[idx]
                else:
                    print("Invalid choice, using nearest expiration")
            except (ValueError, KeyboardInterrupt):
                print("Using nearest expiration")
        elif args.expiration == 'multiple':
            include_all = True
            print("Using multiple expirations (first 5)")
        # else: use nearest (default)
        
        # Fetch options data
        #print(f"\n📊 Fetching options chain data...")
        options_df = fetcher.fetch_options_chain(
            symbol=symbol,
            expiration_date=selected_expiration,
            include_all_expirations=include_all
        )
        
        contracts = fetcher.convert_to_contracts(options_df)
        #print(f"Loaded {len(contracts)} option contracts")
        
        if not contracts:
            print("❌ No valid options data found")
            return 1
        
        # Calculate gamma exposures
        #print("\n⚡ Calculating gamma exposures...")
        calculator = GammaCalculator(risk_free_rate=args.risk_free_rate, debug=args.debug)
        gamma_exposures = calculator.aggregate_by_strike(contracts, current_price)
        #print(f"Calculated gamma exposure for {len(gamma_exposures)} strikes")
        
        # Analyze walls
        #print("\n🧱 Analyzing gamma walls...")
        wall_analyzer = WallAnalyzer()
        walls = wall_analyzer.find_all_walls(gamma_exposures, current_price)
        
        # Calculate metrics
        #print("\n📊 Computing market metrics...")
        metrics_calc = MetricsCalculator(debug=args.debug)
        market_metrics = metrics_calc.calculate_all_metrics(gamma_exposures)
        gamma_environment = metrics_calc.calculate_gamma_environment(gamma_exposures, current_price)
        
        # Display results
        display_gamma_environment(gamma_environment, current_price)
        display_key_metrics(market_metrics, walls)
        display_walls(walls, current_price)
        display_expected_move(contracts, current_price)
        display_trading_implications(gamma_environment, walls, current_price)
        
        # Display gamma flip debug if requested
        if args.debug_flip:
            display_gamma_flip_debug(gamma_exposures, current_price, gamma_environment)
        
        # Export to CSV if requested
        if args.export_csv:
            export_gamma_details_to_csv(contracts, current_price, calculator, args.csv_filename)
        
        #print_header("Analysis Complete")
        #print(f"✅ {symbol} gamma exposure analysis completed successfully!")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n❌ Analysis interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())