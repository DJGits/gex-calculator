#!/usr/bin/env python3
"""
SPX Gamma Exposure Calculator - Command Line Interface
Usage: python gamma_cli.py [symbol] [expiration_option]

Examples:
  python gamma_cli.py SPY                    # SPY with nearest expiration
  python gamma_cli.py SPY specific           # SPY with specific expiration selection
  python gamma_cli.py QQQ multiple           # QQQ with multiple expirations
"""

import sys
import argparse
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
    """Display gamma environment analysis"""
    print_section("Gamma Environment Analysis")
    
    # Environment type
    env_type = gamma_env['environment'].upper()
    if gamma_env['environment'] == 'positive':
        env_icon = "🛡️"
        env_desc = "Stabilizing Force"
    elif gamma_env['environment'] == 'negative':
        env_icon = "⚡"
        env_desc = "Amplifying Force"
    else:
        env_icon = "⚖️"
        env_desc = "Balanced"
    
    print(f"{env_icon} Environment Type: {env_type} ({env_desc})")
    print(f"📝 {gamma_env['description']}")
    
    # Environment strength
    strength_info = gamma_env['strength_interpretation']
    print(f"\n💪 Environment Strength:")
    print(f"   {strength_info['color']} Level: {strength_info['level']}")
    print(f"   📊 Raw Value: {gamma_env['environment_strength']:.4f}")
    print(f"   🌪️ Volatility Impact: {strength_info['volatility_impact']}")
    print(f"   📝 {strength_info['description']}")
    
    # Gamma flip level
    if gamma_env['gamma_flip_level']:
        flip_level = gamma_env['gamma_flip_level']
        flip_distance = flip_level - current_price
        flip_distance_pct = (flip_distance / current_price) * 100
        
        print(f"\n🎯 Gamma Flip Level: {flip_level:.0f}")
        print(f"   📏 Distance: {flip_distance:+.0f} ({flip_distance_pct:+.1f}%)")
        
        # Interpretation
        if gamma_env['environment'] == 'positive' and flip_distance > 0:
            print(f"   🚀 Breakout potential above {flip_level:.0f}")
        elif gamma_env['environment'] == 'positive' and flip_distance < 0:
            print(f"   ⚠️ Breakdown risk below {flip_level:.0f}")
        elif gamma_env['environment'] == 'negative' and flip_distance > 0:
            print(f"   🛡️ Stabilization above {flip_level:.0f}")
        else:
            print(f"   🛡️ Support below {flip_level:.0f}")
    else:
        print(f"\n🎯 Gamma Flip Level: Not identified")
    
    # Strike distribution
    print(f"\n📊 Strike Distribution:")
    print(f"   🟢 Positive Strikes: {gamma_env['positive_strikes']} ({gamma_env['positive_strike_percentage']:.1f}%)")
    print(f"   🔴 Negative Strikes: {gamma_env['negative_strikes']} ({gamma_env['negative_strike_percentage']:.1f}%)")
    print(f"   ⚪ Neutral Strikes: {gamma_env['neutral_strikes']}")


def display_key_metrics(market_metrics, walls: dict):
    """Display key metrics"""
    print_section("Key Metrics")
    
    print_metric("Total Net Gamma", f"{market_metrics.total_net_gamma:,.0f}")
    print_metric("Weighted Avg Strike", f"{market_metrics.gamma_weighted_avg_strike:.0f}")
    print_metric("Call/Put Ratio", f"{market_metrics.call_put_gamma_ratio:.2f}")
    print_metric("Max Call Exposure", f"{market_metrics.max_call_exposure:,.0f}", "resistance")
    print_metric("Max Put Exposure", f"{market_metrics.max_put_exposure:,.0f}", "support")
    print_metric("Gamma Std Dev", f"{market_metrics.gamma_exposure_std:,.0f}")
    
    total_walls = len(walls['call_walls']) + len(walls['put_walls'])
    print_metric("Total Walls", f"{total_walls}")


def display_walls(walls: dict, current_price: float):
    """Display gamma walls"""
    print_section("Gamma Walls")
    
    call_walls = walls.get('call_walls', [])
    put_walls = walls.get('put_walls', [])
    
    if call_walls:
        print("🔴 Call Walls (Resistance):")
        for wall in call_walls[:5]:  # Show top 5
            distance_pct = (wall.distance_from_spot / current_price) * 100
            print(f"   #{wall.significance_rank}: {wall.strike:.0f} "
                  f"({distance_pct:+.1f}%) - {wall.exposure_value:,.0f}")
    
    if put_walls:
        print("\n🟢 Put Walls (Support):")
        for wall in put_walls[:5]:  # Show top 5
            distance_pct = (wall.distance_from_spot / current_price) * 100
            print(f"   #{wall.significance_rank}: {wall.strike:.0f} "
                  f"({distance_pct:+.1f}%) - {wall.exposure_value:,.0f}")
    
    if not call_walls and not put_walls:
        print("No significant gamma walls identified")


def display_trading_implications(gamma_env: dict, walls: dict, current_price: float):
    """Display trading implications"""
    print_section("Trading Implications")
    
    strength_info = gamma_env['strength_interpretation']
    
    # Environment implications
    if gamma_env['environment'] == 'positive':
        print("🛡️ Positive Gamma Environment:")
        print("   • Market makers provide stabilizing force")
        print("   • Buy dips, sell rallies strategy")
        print("   • Lower volatility expected")
        print("   • Mean-reverting price action")
    elif gamma_env['environment'] == 'negative':
        print("⚡ Negative Gamma Environment:")
        print("   • Market makers amplify moves")
        print("   • Momentum/trend following strategy")
        print("   • Higher volatility expected")
        print("   • Trending price action")
    else:
        print("⚖️ Neutral Gamma Environment:")
        print("   • Balanced gamma forces")
        print("   • Mixed market maker influence")
        print("   • Moderate volatility expected")
    
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


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="SPX Gamma Exposure Calculator - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gamma_cli.py SPY                           # SPY with nearest expiration
  python gamma_cli.py SPY 2025-01-17               # SPY with specific date
  python gamma_cli.py SPY specific                  # SPY with interactive selection
  python gamma_cli.py QQQ multiple                  # QQQ with multiple expirations
  python gamma_cli.py --list-symbols                # Show available symbols
  python gamma_cli.py --list-expirations SPY       # Show SPY expirations
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
        
        print_header(f"SPX Gamma Exposure Analysis - {symbol}")
        print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get current price
        print("\n📈 Fetching current price...")
        try:
            current_price = fetcher.get_current_price(symbol)
            print(f"Current {symbol} Price: ${current_price:.2f}")
        except YFinanceFetchError as e:
            print(f"Warning: Could not fetch current price: {e}")
            current_price = 4500.0  # Default fallback
        
        # Get expiration dates
        print("\n📅 Fetching expiration dates...")
        expirations = fetcher.get_expiration_dates(symbol)
        print(f"Available expirations: {len(expirations)}")
        
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
        print(f"\n📊 Fetching options chain data...")
        options_df = fetcher.fetch_options_chain(
            symbol=symbol,
            expiration_date=selected_expiration,
            include_all_expirations=include_all
        )
        
        contracts = fetcher.convert_to_contracts(options_df)
        print(f"Loaded {len(contracts)} option contracts")
        
        if not contracts:
            print("❌ No valid options data found")
            return 1
        
        # Calculate gamma exposures
        print("\n⚡ Calculating gamma exposures...")
        calculator = GammaCalculator(risk_free_rate=args.risk_free_rate)
        gamma_exposures = calculator.aggregate_by_strike(contracts, current_price)
        print(f"Calculated gamma exposure for {len(gamma_exposures)} strikes")
        
        # Analyze walls
        print("\n🧱 Analyzing gamma walls...")
        wall_analyzer = WallAnalyzer()
        walls = wall_analyzer.find_all_walls(gamma_exposures, current_price)
        
        # Calculate metrics
        print("\n📊 Computing market metrics...")
        metrics_calc = MetricsCalculator()
        market_metrics = metrics_calc.calculate_all_metrics(gamma_exposures)
        gamma_environment = metrics_calc.calculate_gamma_environment(gamma_exposures, current_price)
        
        # Display results
        display_gamma_environment(gamma_environment, current_price)
        display_key_metrics(market_metrics, walls)
        display_walls(walls, current_price)
        display_trading_implications(gamma_environment, walls, current_price)
        
        print_header("Analysis Complete")
        print(f"✅ {symbol} gamma exposure analysis completed successfully!")
        
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