#!/usr/bin/env python3
"""
Quick Gamma Analysis - Simplified CLI for fast gamma exposure checks
Usage: python quick_gamma.py [symbol]
"""

import sys
from datetime import datetime
from data.yfinance_fetcher import YFinanceOptionsFetcher
from calculations.gamma import GammaCalculator
from analysis.walls import WallAnalyzer
from analysis.metrics import MetricsCalculator


def quick_analysis(symbol='SPY', expiration=None):
    """Perform quick gamma analysis"""
    try:
        print(f"🔍 Quick Gamma Analysis: {symbol}")
        if expiration:
            print(f"📅 Expiration: {expiration}")
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 40)
        
        # Fetch data
        fetcher = YFinanceOptionsFetcher()
        current_price = fetcher.get_current_price(symbol)
        
        # Handle expiration parameter
        selected_expiration = None
        include_all = False
        
        if expiration:
            expirations = fetcher.get_expiration_dates(symbol)
            if expiration in expirations:
                selected_expiration = expiration
            elif expiration == 'multiple':
                include_all = True
            else:
                print(f"⚠️ Expiration {expiration} not available, using nearest")
        
        options_df = fetcher.fetch_options_chain(
            symbol, 
            expiration_date=selected_expiration,
            include_all_expirations=include_all
        )
        contracts = fetcher.convert_to_contracts(options_df)
        
        # Calculate
        calculator = GammaCalculator()
        gamma_exposures = calculator.aggregate_by_strike(contracts, current_price)
        
        wall_analyzer = WallAnalyzer()
        walls = wall_analyzer.find_all_walls(gamma_exposures, current_price)
        
        metrics_calc = MetricsCalculator()
        market_metrics = metrics_calc.calculate_all_metrics(gamma_exposures)
        gamma_env = metrics_calc.calculate_gamma_environment(gamma_exposures, current_price)
        
        # Display key info
        print(f"💰 Price: ${current_price:.2f}")
        print(f"📊 Contracts: {len(contracts)}")
        
        # Environment
        env_icon = "🛡️" if gamma_env['environment'] == 'positive' else "⚡" if gamma_env['environment'] == 'negative' else "⚖️"
        strength_info = gamma_env['strength_interpretation']
        print(f"{env_icon} Environment: {gamma_env['environment'].upper()} ({strength_info['level']})")
        
        # Key metrics
        print(f"🎯 Net Gamma: {market_metrics.total_net_gamma:,.0f}")
        print(f"📈 Weighted Strike: {market_metrics.gamma_weighted_avg_strike:.0f}")
        
        # Flip level
        if gamma_env['gamma_flip_level']:
            flip_distance = gamma_env['gamma_flip_level'] - current_price
            print(f"🔄 Flip Level: {gamma_env['gamma_flip_level']:.0f} ({flip_distance:+.0f})")
        
        # Top walls
        call_walls = walls.get('call_walls', [])
        put_walls = walls.get('put_walls', [])
        
        if call_walls:
            top_call = call_walls[0]
            distance = ((top_call.strike - current_price) / current_price) * 100
            print(f"🔴 Top Call Wall: {top_call.strike:.0f} ({distance:+.1f}%)")
        
        if put_walls:
            top_put = put_walls[0]
            distance = ((top_put.strike - current_price) / current_price) * 100
            print(f"🟢 Top Put Wall: {top_put.strike:.0f} ({distance:+.1f}%)")
        
        # Quick interpretation
        print("\n💡 Quick Take:")
        if gamma_env['environment'] == 'positive':
            print("   📉 Buy dips, sell rallies")
        elif gamma_env['environment'] == 'negative':
            print("   📈 Momentum/trend following")
        else:
            print("   ⚖️ Mixed signals")
        
        if strength_info['level'] in ['Very Strong', 'Strong']:
            print("   ✅ High confidence in gamma effects")
        else:
            print("   ⚠️ Low confidence - consider other factors")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Usage: python quick_gamma.py [symbol] [expiration]")
        print("Examples:")
        print("  python quick_gamma.py SPY")
        print("  python quick_gamma.py SPY 2025-01-17")
        print("  python quick_gamma.py QQQ multiple")
        return 0
    
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else 'SPY'
    expiration = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = quick_analysis(symbol, expiration)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())