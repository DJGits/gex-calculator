#!/usr/bin/env python3
"""
Covered Call Strategy Analyzer - Analyze gamma environment for covered call optimization
Usage: python covered_call_analyzer.py [symbol] [expiration]
"""

import sys
from datetime import datetime
from data.yfinance_fetcher import YFinanceOptionsFetcher
from calculations.gamma import GammaCalculator
from analysis.walls import WallAnalyzer
from analysis.metrics import MetricsCalculator


def analyze_covered_call_environment(symbol='SPY', expiration=None):
    """Analyze gamma environment for covered call strategy"""
    try:
        print(f"📊 Covered Call Strategy Analysis: {symbol}")
        if expiration:
            print(f"📅 Expiration: {expiration}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Fetch data
        fetcher = YFinanceOptionsFetcher()
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
        
        # Calculate gamma metrics
        calculator = GammaCalculator()
        gamma_exposures = calculator.aggregate_by_strike(contracts, current_price)
        
        wall_analyzer = WallAnalyzer()
        walls = wall_analyzer.find_all_walls(gamma_exposures, current_price)
        
        metrics_calc = MetricsCalculator()
        market_metrics = metrics_calc.calculate_all_metrics(gamma_exposures)
        gamma_env = metrics_calc.calculate_gamma_environment(gamma_exposures, current_price)
        
        # Display current market state
        print(f"💰 Current {symbol} Price: ${current_price:.2f}")
        print(f"📊 Options Contracts Analyzed: {len(contracts)}")
        
        # Gamma environment analysis
        print(f"\n🌊 GAMMA ENVIRONMENT ANALYSIS")
        print("-" * 50)
        
        env_type = gamma_env['environment'].upper()
        strength_info = gamma_env['strength_interpretation']
        
        if gamma_env['environment'] == 'positive':
            env_icon = "🛡️"
            cc_rating = "EXCELLENT"
            cc_color = "🟢"
        elif gamma_env['environment'] == 'negative':
            env_icon = "⚡"
            cc_rating = "RISKY"
            cc_color = "🔴"
        else:
            env_icon = "⚖️"
            cc_rating = "MODERATE"
            cc_color = "🟡"
        
        print(f"{env_icon} Environment: {env_type}")
        print(f"💪 Strength: {strength_info['level']} ({gamma_env['environment_strength']:.4f})")
        print(f"{cc_color} Covered Call Rating: {cc_rating}")
        
        # Covered call specific analysis
        print(f"\n📋 COVERED CALL STRATEGY ANALYSIS")
        print("-" * 50)
        
        if gamma_env['environment'] == 'positive':
            print("✅ POSITIVE GAMMA - EXCELLENT for Covered Calls:")
            print("   🛡️ Market makers provide price stability")
            print("   📉 Mean-reverting price action expected")
            print("   🔄 Lower volatility environment")
            print("   🎯 Higher probability of calls expiring worthless")
            print("   💰 Better premium retention")
            
            if strength_info['level'] in ['Very Strong', 'Strong']:
                print("   🚀 HIGH CONFIDENCE: Strong gamma forces support strategy")
            else:
                print("   ⚠️ MODERATE CONFIDENCE: Weaker gamma forces")
        
        elif gamma_env['environment'] == 'negative':
            print("❌ NEGATIVE GAMMA - RISKY for Covered Calls:")
            print("   ⚡ Market makers amplify price moves")
            print("   📈 Momentum/trending price action expected")
            print("   🌪️ Higher volatility environment")
            print("   💥 Higher risk of calls being exercised")
            print("   📊 Consider defensive adjustments")
            
            if strength_info['level'] in ['Very Strong', 'Strong']:
                print("   🚨 HIGH RISK: Strong negative gamma forces")
            else:
                print("   ⚠️ MODERATE RISK: Weaker negative gamma forces")
        
        else:
            print("⚖️ NEUTRAL GAMMA - MODERATE for Covered Calls:")
            print("   🎯 Mixed gamma forces")
            print("   📊 Moderate volatility expected")
            print("   🔄 Standard covered call management applies")
        
        # Call wall analysis for strike selection
        call_walls = walls.get('call_walls', [])
        if call_walls:
            print(f"\n🔴 CALL WALL ANALYSIS (Resistance Levels)")
            print("-" * 50)
            print("Optimal strike selection based on gamma walls:")
            
            for i, wall in enumerate(call_walls[:3], 1):
                distance_pct = ((wall.strike - current_price) / current_price) * 100
                
                if distance_pct > 0:  # Above current price
                    if 1 <= distance_pct <= 5:
                        recommendation = "🎯 OPTIMAL"
                    elif distance_pct <= 1:
                        recommendation = "⚠️ TOO CLOSE"
                    else:
                        recommendation = "📊 CONSERVATIVE"
                else:
                    recommendation = "❌ AVOID (ITM)"
                
                print(f"   #{i}: {wall.strike:.0f} ({distance_pct:+.1f}%) - {recommendation}")
                print(f"       Gamma Exposure: {wall.exposure_value:,.0f}")
                
                if recommendation == "🎯 OPTIMAL":
                    print(f"       💡 Strong resistance, good risk/reward")
                elif recommendation == "⚠️ TOO CLOSE":
                    print(f"       💡 High assignment risk, low premium")
                elif recommendation == "📊 CONSERVATIVE":
                    print(f"       💡 Lower assignment risk, lower premium")
        
        # Flip level implications for covered calls
        if gamma_env['gamma_flip_level']:
            flip_level = gamma_env['gamma_flip_level']
            flip_distance = flip_level - current_price
            flip_distance_pct = (flip_distance / current_price) * 100
            
            print(f"\n🔄 GAMMA FLIP LEVEL IMPLICATIONS")
            print("-" * 50)
            print(f"Flip Level: {flip_level:.0f} ({flip_distance:+.0f}, {flip_distance_pct:+.1f}%)")
            
            if gamma_env['environment'] == 'positive' and flip_distance > 0:
                print("🎯 COVERED CALL SWEET SPOT:")
                print(f"   • Current price protected by positive gamma")
                print(f"   • Strong resistance expected below {flip_level:.0f}")
                print(f"   • Consider strikes between current price and flip level")
                print(f"   • If breached above {flip_level:.0f}, expect acceleration")
            
            elif gamma_env['environment'] == 'negative' and flip_distance > 0:
                print("⚠️ COVERED CALL CAUTION:")
                print(f"   • Currently in momentum environment")
                print(f"   • Stabilization only above {flip_level:.0f}")
                print(f"   • High risk of upward acceleration")
                print(f"   • Consider wider strikes or defensive management")
        
        # Strategy recommendations
        print(f"\n💡 COVERED CALL STRATEGY RECOMMENDATIONS")
        print("-" * 50)
        
        if gamma_env['environment'] == 'positive':
            if strength_info['level'] in ['Very Strong', 'Strong']:
                print("🚀 AGGRESSIVE STRATEGY (High Confidence):")
                print("   • Sell calls closer to current price (1-3% OTM)")
                print("   • Higher premium collection")
                print("   • Strong gamma support reduces assignment risk")
            else:
                print("📊 STANDARD STRATEGY (Moderate Confidence):")
                print("   • Sell calls at moderate distance (2-5% OTM)")
                print("   • Balance premium vs assignment risk")
        
        elif gamma_env['environment'] == 'negative':
            if strength_info['level'] in ['Very Strong', 'Strong']:
                print("🛡️ DEFENSIVE STRATEGY (High Risk):")
                print("   • Sell calls further OTM (5-10% OTM)")
                print("   • Consider shorter expirations")
                print("   • Prepare for early assignment")
                print("   • Consider avoiding covered calls entirely")
            else:
                print("⚠️ CAUTIOUS STRATEGY (Moderate Risk):")
                print("   • Sell calls at wider strikes (3-7% OTM)")
                print("   • Monitor closely for momentum breaks")
        
        else:
            print("📊 BALANCED STRATEGY:")
            print("   • Standard covered call approach (2-5% OTM)")
            print("   • Normal risk management")
        
        # Risk assessment
        print(f"\n⚠️ RISK ASSESSMENT")
        print("-" * 50)
        
        if gamma_env['environment'] == 'positive':
            risk_level = "LOW" if strength_info['level'] in ['Very Strong', 'Strong'] else "MODERATE"
            print(f"🟢 Assignment Risk: {risk_level}")
            print("   • Mean-reverting environment favors covered calls")
            print("   • Strong support levels limit upside")
        else:
            risk_level = "HIGH" if strength_info['level'] in ['Very Strong', 'Strong'] else "MODERATE"
            print(f"🔴 Assignment Risk: {risk_level}")
            print("   • Momentum environment increases assignment risk")
            print("   • Consider defensive position sizing")
        
        print(f"\n✅ Analysis complete for {symbol} covered call strategy")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Usage: python covered_call_analyzer.py [symbol] [expiration]")
        print("Examples:")
        print("  python covered_call_analyzer.py SPY")
        print("  python covered_call_analyzer.py SPY 2025-01-17")
        print("  python covered_call_analyzer.py QQQ multiple")
        return 0
    
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else 'SPY'
    expiration = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = analyze_covered_call_environment(symbol, expiration)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())