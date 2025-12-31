#!/usr/bin/env python3
"""
Batch Gamma Analysis - Analyze multiple symbols at once
Usage: python batch_gamma.py [symbol1] [symbol2] ...
"""

import sys
from datetime import datetime
from data.yfinance_fetcher import YFinanceOptionsFetcher
from calculations.gamma import GammaCalculator
from analysis.walls import WallAnalyzer
from analysis.metrics import MetricsCalculator


def analyze_symbol(symbol: str, expiration: str, fetcher, calculator, wall_analyzer, metrics_calc):
    """Analyze a single symbol"""
    try:
        # Fetch data
        current_price = fetcher.get_current_price(symbol)
        
        # Handle expiration
        selected_expiration = None
        include_all = False
        
        if expiration and expiration != 'nearest':
            expirations = fetcher.get_expiration_dates(symbol)
            if expiration in expirations:
                selected_expiration = expiration
            elif expiration == 'multiple':
                include_all = True
        
        options_df = fetcher.fetch_options_chain(
            symbol,
            expiration_date=selected_expiration,
            include_all_expirations=include_all
        )
        contracts = fetcher.convert_to_contracts(options_df)
        
        if not contracts:
            return None
        
        # Calculate
        gamma_exposures = calculator.aggregate_by_strike(contracts, current_price)
        walls = wall_analyzer.find_all_walls(gamma_exposures, current_price)
        market_metrics = metrics_calc.calculate_all_metrics(gamma_exposures)
        gamma_env = metrics_calc.calculate_gamma_environment(gamma_exposures, current_price)
        
        return {
            'symbol': symbol,
            'price': current_price,
            'contracts': len(contracts),
            'environment': gamma_env['environment'],
            'strength': gamma_env['strength_interpretation']['level'],
            'net_gamma': market_metrics.total_net_gamma,
            'flip_level': gamma_env['gamma_flip_level'],
            'call_walls': len(walls.get('call_walls', [])),
            'put_walls': len(walls.get('put_walls', [])),
            'top_call_wall': walls['call_walls'][0].strike if walls.get('call_walls') else None,
            'top_put_wall': walls['put_walls'][0].strike if walls.get('put_walls') else None
        }
        
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}


def main():
    """Main batch analysis function"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Usage: python batch_gamma.py [symbol1] [symbol2] ... [--exp expiration]")
        print("Examples:")
        print("  python batch_gamma.py SPY QQQ IWM")
        print("  python batch_gamma.py SPY QQQ --exp 2025-01-17")
        print("  python batch_gamma.py SPY --exp multiple")
        print("Default: Analyzes SPY, QQQ, IWM with nearest expiration")
        return 0
    
    # Parse arguments
    symbols = []
    expiration = 'nearest'
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--exp' and i + 1 < len(sys.argv):
            expiration = sys.argv[i + 1]
            i += 2
        else:
            symbols.append(sys.argv[i].upper())
            i += 1
    
    if not symbols:
        symbols = ['SPY', 'QQQ', 'IWM']
    
    print("🔍 Batch Gamma Analysis")
    if expiration != 'nearest':
        print(f"📅 Expiration: {expiration}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Initialize components
    fetcher = YFinanceOptionsFetcher()
    calculator = GammaCalculator()
    wall_analyzer = WallAnalyzer()
    metrics_calc = MetricsCalculator()
    
    results = []
    
    # Analyze each symbol
    for symbol in symbols:
        print(f"\n📊 Analyzing {symbol}...")
        result = analyze_symbol(symbol, expiration, fetcher, calculator, wall_analyzer, metrics_calc)
        if result:
            results.append(result)
    
    # Display results table
    print("\n" + "=" * 80)
    print("📊 GAMMA ANALYSIS SUMMARY")
    print("=" * 80)
    
    # Header
    print(f"{'Symbol':<6} {'Price':<8} {'Environment':<12} {'Strength':<12} {'Net Gamma':<12} {'Flip':<6} {'Walls':<6}")
    print("-" * 80)
    
    # Results
    for result in results:
        if 'error' in result:
            print(f"{result['symbol']:<6} ERROR: {result['error']}")
            continue
        
        # Environment icon
        env_icon = "🛡️" if result['environment'] == 'positive' else "⚡" if result['environment'] == 'negative' else "⚖️"
        
        # Format values
        price_str = f"${result['price']:.0f}"
        env_str = f"{env_icon}{result['environment'][:3].upper()}"
        strength_str = result['strength'][:8]
        gamma_str = f"{result['net_gamma']/1e6:.1f}M" if abs(result['net_gamma']) >= 1e6 else f"{result['net_gamma']/1e3:.0f}k"
        flip_str = f"{result['flip_level']:.0f}" if result['flip_level'] else "N/A"
        walls_str = f"{result['call_walls']}C/{result['put_walls']}P"
        
        print(f"{result['symbol']:<6} {price_str:<8} {env_str:<12} {strength_str:<12} {gamma_str:<12} {flip_str:<6} {walls_str:<6}")
    
    # Detailed analysis
    print("\n" + "=" * 80)
    print("📋 DETAILED ANALYSIS")
    print("=" * 80)
    
    for result in results:
        if 'error' in result:
            continue
        
        print(f"\n🎯 {result['symbol']}:")
        
        # Environment analysis
        env_icon = "🛡️" if result['environment'] == 'positive' else "⚡" if result['environment'] == 'negative' else "⚖️"
        print(f"   {env_icon} Environment: {result['environment'].upper()} ({result['strength']})")
        
        # Key levels
        if result['flip_level']:
            flip_distance = result['flip_level'] - result['price']
            flip_pct = (flip_distance / result['price']) * 100
            print(f"   🔄 Flip Level: {result['flip_level']:.0f} ({flip_distance:+.0f}, {flip_pct:+.1f}%)")
        
        # Walls
        if result['top_call_wall']:
            call_distance = ((result['top_call_wall'] - result['price']) / result['price']) * 100
            print(f"   🔴 Top Call Wall: {result['top_call_wall']:.0f} ({call_distance:+.1f}%)")
        
        if result['top_put_wall']:
            put_distance = ((result['top_put_wall'] - result['price']) / result['price']) * 100
            print(f"   🟢 Top Put Wall: {result['top_put_wall']:.0f} ({put_distance:+.1f}%)")
        
        # Quick interpretation
        if result['environment'] == 'positive':
            strategy = "Buy dips, sell rallies"
        elif result['environment'] == 'negative':
            strategy = "Momentum/trend following"
        else:
            strategy = "Mixed signals"
        
        confidence = "High confidence" if result['strength'] in ['Very Strong', 'Strong'] else "Low confidence"
        print(f"   💡 Strategy: {strategy} ({confidence})")
    
    print(f"\n✅ Analysis complete for {len(results)} symbols")
    return 0


if __name__ == "__main__":
    sys.exit(main())