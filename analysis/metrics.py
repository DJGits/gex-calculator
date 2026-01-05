"""
Market metrics calculation for gamma exposure analysis
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

from data.models import GammaExposure, MarketMetrics


class MetricsCalculationError(Exception):
    """Custom exception for metrics calculation errors"""
    pass


class MetricsCalculator:
    """Calculates comprehensive market metrics from gamma exposure data"""
    
    def __init__(self, debug: bool = False):
        """
        Initialize metrics calculator
        
        Args:
            debug: Enable debug mode for detailed variable printing
        """
        self.debug = debug
    
    def calculate_gamma_environment(self, 
                                  gamma_exposures: List[GammaExposure],
                                  current_price: float) -> Dict[str, Any]:
        """
        Analyze the gamma environment (positive vs negative gamma)
        
        Args:
            gamma_exposures: List of GammaExposure objects
            current_price: Current underlying price
            
        Returns:
            Dictionary with gamma environment analysis
        """
        if not gamma_exposures:
            return {
                'environment': 'neutral',
                'total_net_gamma': 0.0,
                'environment_strength': 0.0,
                'description': 'No gamma data available'
            }
        
        total_net_gamma = self.calculate_total_net_gamma(gamma_exposures)
        
        # Determine environment type
        if total_net_gamma > 0:
            environment = 'positive'
            description = 'Positive Gamma Environment - Market makers provide support (buy dips, sell rallies)'
        elif total_net_gamma < 0:
            environment = 'negative'
            description = 'Negative Gamma Environment - Market makers amplify moves (sell dips, buy rallies)'
        else:
            environment = 'neutral'
            description = 'Neutral Gamma Environment - Balanced gamma exposure'
        
        # Calculate environment strength (normalized by current price and open interest)
        total_oi = sum(ge.total_open_interest for ge in gamma_exposures)
        if total_oi > 0 and current_price > 0:
            # Normalize by price and open interest to get strength measure
            environment_strength = abs(total_net_gamma) / (current_price * total_oi)
        else:
            environment_strength = 0.0
        
        # Calculate strength interpretation
        strength_interpretation = self._interpret_environment_strength(environment_strength)
        
        # Additional analysis
        positive_strikes = len([ge for ge in gamma_exposures if ge.net_gamma_exposure > 0])
        negative_strikes = len([ge for ge in gamma_exposures if ge.net_gamma_exposure < 0])
        total_strikes = len(gamma_exposures)
        
        return {
            'environment': environment,
            'total_net_gamma': total_net_gamma,
            'environment_strength': environment_strength,
            'strength_interpretation': strength_interpretation,
            'description': description,
            'positive_strikes': positive_strikes,
            'negative_strikes': negative_strikes,
            'neutral_strikes': total_strikes - positive_strikes - negative_strikes,
            'positive_strike_percentage': (positive_strikes / total_strikes * 100) if total_strikes > 0 else 0,
            'negative_strike_percentage': (negative_strikes / total_strikes * 100) if total_strikes > 0 else 0,
            'gamma_flip_level': self._find_gamma_flip_level(gamma_exposures, current_price)
        }
    
    def _interpret_environment_strength(self, strength: float) -> Dict[str, Any]:
        """
        Interpret environment strength value
        
        Args:
            strength: Environment strength value
            
        Returns:
            Dictionary with strength interpretation
        """
        if strength >= 0.1:
            level = "Very Strong"
            description = "Extremely powerful gamma forces - expect significant market maker impact"
            volatility_impact = "Very High"
            color = "🔴"
        elif strength >= 0.05:
            level = "Strong"
            description = "Strong gamma forces - market makers will have notable impact on price action"
            volatility_impact = "High"
            color = "🟠"
        elif strength >= 0.02:
            level = "Moderate"
            description = "Moderate gamma forces - noticeable but not dominant market maker influence"
            volatility_impact = "Medium"
            color = "🟡"
        elif strength >= 0.01:
            level = "Weak"
            description = "Weak gamma forces - limited market maker impact on price action"
            volatility_impact = "Low"
            color = "🟢"
        else:
            level = "Very Weak"
            description = "Minimal gamma forces - negligible market maker impact"
            volatility_impact = "Very Low"
            color = "⚪"
        
        return {
            'level': level,
            'description': description,
            'volatility_impact': volatility_impact,
            'color': color,
            'raw_value': strength
        }
        
        return {
            'environment': environment,
            'total_net_gamma': total_net_gamma,
            'environment_strength': environment_strength,
            'description': description,
            'positive_strikes': positive_strikes,
            'negative_strikes': negative_strikes,
            'neutral_strikes': total_strikes - positive_strikes - negative_strikes,
            'positive_strike_percentage': (positive_strikes / total_strikes * 100) if total_strikes > 0 else 0,
            'negative_strike_percentage': (negative_strikes / total_strikes * 100) if total_strikes > 0 else 0,
            'gamma_flip_level': self._find_gamma_flip_level(gamma_exposures, current_price)
        }
    
    def _find_gamma_flip_level(self, 
                              gamma_exposures: List[GammaExposure], 
                              current_price: float) -> Optional[float]:
        """
        Find the approximate price level where gamma environment flips
        
        Args:
            gamma_exposures: List of GammaExposure objects
            current_price: Current underlying price
            
        Returns:
            Approximate gamma flip level or None if not found
        """
        if not gamma_exposures:
            return None
        
        # Sort by strike price
        sorted_exposures = sorted(gamma_exposures, key=lambda x: x.strike)
        
        # Look for the strike where net gamma changes sign most significantly
        max_flip_magnitude = 0
        flip_level = None
        
        for i in range(len(sorted_exposures) - 1):
            current_gamma = sorted_exposures[i].net_gamma_exposure
            next_gamma = sorted_exposures[i + 1].net_gamma_exposure
            
            # Check if there's a sign change
            if (current_gamma > 0 and next_gamma < 0) or (current_gamma < 0 and next_gamma > 0):
                flip_magnitude = abs(current_gamma) + abs(next_gamma)
                if flip_magnitude > max_flip_magnitude:
                    max_flip_magnitude = flip_magnitude
                    # Interpolate between the two strikes
                    flip_level = (sorted_exposures[i].strike + sorted_exposures[i + 1].strike) / 2
        
        return flip_level

    def calculate_total_net_gamma(self, gamma_exposures: List[GammaExposure]) -> float:
        """
        Calculate total net gamma exposure across all strikes
        
        Args:
            gamma_exposures: List of GammaExposure objects
            
        Returns:
            Total net gamma exposure
        """
        if not gamma_exposures:
            return 0.0
        
        return sum(ge.net_gamma_exposure for ge in gamma_exposures)
    
    def calculate_gamma_weighted_average_strike(self, gamma_exposures: List[GammaExposure]) -> float:
        """
        Calculate gamma-weighted average strike price
        
        Args:
            gamma_exposures: List of GammaExposure objects
            
        Returns:
            Gamma-weighted average strike price
        """
        if not gamma_exposures:
            return 0.0
        
        # Use absolute gamma exposure for weighting to avoid cancellation
        weighted_sum = 0.0
        total_weight = 0.0
        
        for ge in gamma_exposures:
            weight = abs(ge.net_gamma_exposure)
            if weight > 0:  # Only include strikes with non-zero gamma
                weighted_sum += ge.strike * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def calculate_call_put_gamma_ratio(self, gamma_exposures: List[GammaExposure]) -> float:
        """
        Calculate ratio of call gamma exposure to put gamma exposure
        
        Args:
            gamma_exposures: List of GammaExposure objects
            
        Returns:
            Call/put gamma exposure ratio
        """
        if not gamma_exposures:
            return 0.0
        
        total_call_gamma = sum(abs(ge.call_gamma_exposure) for ge in gamma_exposures if ge.call_gamma_exposure != 0)
        total_put_gamma = sum(abs(ge.put_gamma_exposure) for ge in gamma_exposures if ge.put_gamma_exposure != 0)
        
        if total_put_gamma == 0:
            return float('inf') if total_call_gamma > 0 else 0.0
        
        return total_call_gamma / total_put_gamma
    
    def calculate_max_exposures(self, gamma_exposures: List[GammaExposure]) -> Dict[str, float]:
        """
        Calculate maximum call and put gamma exposures
        
        Args:
            gamma_exposures: List of GammaExposure objects
            
        Returns:
            Dictionary with max_call_exposure and max_put_exposure
        """
        if not gamma_exposures:
            if self.debug:
                print("\n" + "="*80)
                print("DEBUG: calculate_max_exposures()")
                print("="*80)
                print("No gamma exposures provided")
                print("="*80 + "\n")
            return {'max_call_exposure': 0.0, 'max_put_exposure': 0.0}
        
        if self.debug:
            print("\n" + "="*80)
            print("DEBUG: calculate_max_exposures()")
            print("="*80)
            print(f"Total strikes analyzed: {len(gamma_exposures)}")
            print("\nAll Call Gamma Exposures:")
            print("-" * 80)
        
        # For calls, we want the most negative exposure (strongest resistance)
        call_exposures = []
        for i, ge in enumerate(gamma_exposures):
            if ge.call_gamma_exposure < 0:
                call_exposures.append(ge.call_gamma_exposure)
                if self.debug:
                    print(f"  Strike {ge.strike:>8.2f}: call_gamma_exposure = {ge.call_gamma_exposure:>20,.2f}")
        
        if self.debug:
            print(f"\nTotal negative call exposures found: {len(call_exposures)}")
            if call_exposures:
                print(f"All negative call exposures: {[f'{x:,.2f}' for x in sorted(call_exposures)]}")
        
        max_call_exposure = min(call_exposures) if call_exposures else 0.0
        
        if self.debug:
            print(f"\n{'MAX CALL EXPOSURE (most negative):':<40} {max_call_exposure:>20,.2f}")
            if call_exposures:
                max_strike = next((ge.strike for ge in gamma_exposures if ge.call_gamma_exposure == max_call_exposure), None)
                if max_strike:
                    print(f"{'Strike with max call exposure:':<40} {max_strike:>20.2f}")
        
        # For puts, we want the most positive exposure (strongest support)
        if self.debug:
            print("\n" + "-" * 80)
            print("All Put Gamma Exposures:")
            print("-" * 80)
        
        put_exposures = []
        for ge in gamma_exposures:
            if ge.put_gamma_exposure > 0:
                put_exposures.append(ge.put_gamma_exposure)
                if self.debug:
                    print(f"  Strike {ge.strike:>8.2f}: put_gamma_exposure = {ge.put_gamma_exposure:>20,.2f}")
        
        if self.debug:
            print(f"\nTotal positive put exposures found: {len(put_exposures)}")
            if put_exposures:
                print(f"All positive put exposures: {[f'{x:,.2f}' for x in sorted(put_exposures, reverse=True)]}")
        
        max_put_exposure = max(put_exposures) if put_exposures else 0.0
        
        if self.debug:
            print(f"\n{'MAX PUT EXPOSURE (most positive):':<40} {max_put_exposure:>20,.2f}")
            if put_exposures:
                max_strike = next((ge.strike for ge in gamma_exposures if ge.put_gamma_exposure == max_put_exposure), None)
                if max_strike:
                    print(f"{'Strike with max put exposure:':<40} {max_strike:>20.2f}")
            print("="*80 + "\n")
        
        return {
            'max_call_exposure': max_call_exposure,
            'max_put_exposure': max_put_exposure
        }
    
    def calculate_gamma_exposure_statistics(self, gamma_exposures: List[GammaExposure]) -> Dict[str, float]:
        """
        Calculate statistical measures of gamma exposure distribution
        
        Args:
            gamma_exposures: List of GammaExposure objects
            
        Returns:
            Dictionary with statistical measures
        """
        if not gamma_exposures:
            return {
                'mean': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0,
                'median': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0
            }
        
        # Extract net gamma exposures
        exposures = [ge.net_gamma_exposure for ge in gamma_exposures]
        exposures_array = np.array(exposures)
        
        try:
            stats = {
                'mean': float(np.mean(exposures_array)),
                'std': float(np.std(exposures_array)),
                'min': float(np.min(exposures_array)),
                'max': float(np.max(exposures_array)),
                'median': float(np.median(exposures_array))
            }
            
            # Calculate skewness and kurtosis if scipy is available
            try:
                from scipy.stats import skew, kurtosis
                stats['skewness'] = float(skew(exposures_array))
                stats['kurtosis'] = float(kurtosis(exposures_array))
            except ImportError:
                stats['skewness'] = 0.0
                stats['kurtosis'] = 0.0
            
            return stats
            
        except Exception as e:
            raise MetricsCalculationError(f"Error calculating statistics: {str(e)}")
    
    def calculate_exposure_percentiles(self, 
                                     gamma_exposures: List[GammaExposure],
                                     percentiles: List[float] = [10, 25, 50, 75, 90]) -> Dict[str, float]:
        """
        Calculate percentiles of gamma exposure distribution
        
        Args:
            gamma_exposures: List of GammaExposure objects
            percentiles: List of percentile values to calculate
            
        Returns:
            Dictionary with percentile values
        """
        if not gamma_exposures:
            return {f'p{p}': 0.0 for p in percentiles}
        
        exposures = [ge.net_gamma_exposure for ge in gamma_exposures]
        
        try:
            percentile_values = {}
            for p in percentiles:
                percentile_values[f'p{p}'] = float(np.percentile(exposures, p))
            
            return percentile_values
            
        except Exception as e:
            raise MetricsCalculationError(f"Error calculating percentiles: {str(e)}")
    
    def calculate_concentration_metrics(self, gamma_exposures: List[GammaExposure]) -> Dict[str, float]:
        """
        Calculate concentration metrics for gamma exposure
        
        Args:
            gamma_exposures: List of GammaExposure objects
            
        Returns:
            Dictionary with concentration metrics
        """
        if not gamma_exposures:
            return {
                'top_5_concentration': 0.0,
                'top_10_concentration': 0.0,
                'herfindahl_index': 0.0
            }
        
        # Sort by absolute exposure (descending)
        sorted_exposures = sorted(gamma_exposures, 
                                key=lambda x: abs(x.net_gamma_exposure), 
                                reverse=True)
        
        total_abs_exposure = sum(abs(ge.net_gamma_exposure) for ge in gamma_exposures)
        
        if total_abs_exposure == 0:
            return {
                'top_5_concentration': 0.0,
                'top_10_concentration': 0.0,
                'herfindahl_index': 0.0
            }
        
        # Top 5 concentration
        top_5_exposure = sum(abs(ge.net_gamma_exposure) for ge in sorted_exposures[:5])
        top_5_concentration = top_5_exposure / total_abs_exposure
        
        # Top 10 concentration
        top_10_exposure = sum(abs(ge.net_gamma_exposure) for ge in sorted_exposures[:10])
        top_10_concentration = top_10_exposure / total_abs_exposure
        
        # Herfindahl-Hirschman Index
        hhi = sum((abs(ge.net_gamma_exposure) / total_abs_exposure) ** 2 for ge in gamma_exposures)
        
        return {
            'top_5_concentration': top_5_concentration,
            'top_10_concentration': top_10_concentration,
            'herfindahl_index': hhi
        }
    
    def calculate_all_metrics(self, gamma_exposures: List[GammaExposure]) -> MarketMetrics:
        """
        Calculate all market metrics and return as MarketMetrics object
        
        Args:
            gamma_exposures: List of GammaExposure objects
            
        Returns:
            MarketMetrics object with all calculated metrics
        """
        try:
            # Basic metrics
            total_net_gamma = self.calculate_total_net_gamma(gamma_exposures)
            gamma_weighted_avg_strike = self.calculate_gamma_weighted_average_strike(gamma_exposures)
            call_put_gamma_ratio = self.calculate_call_put_gamma_ratio(gamma_exposures)
            
            # Max exposures
            max_exposures = self.calculate_max_exposures(gamma_exposures)
            max_call_exposure = max_exposures['max_call_exposure']
            max_put_exposure = max_exposures['max_put_exposure']
            
            # Statistical measures
            stats = self.calculate_gamma_exposure_statistics(gamma_exposures)
            gamma_exposure_std = stats['std']
            
            return MarketMetrics(
                total_net_gamma=total_net_gamma,
                gamma_weighted_avg_strike=gamma_weighted_avg_strike,
                call_put_gamma_ratio=call_put_gamma_ratio,
                max_call_exposure=max_call_exposure,
                max_put_exposure=max_put_exposure,
                gamma_exposure_std=gamma_exposure_std
            )
            
        except Exception as e:
            raise MetricsCalculationError(f"Error calculating market metrics: {str(e)}")
    
    def get_metrics_summary(self, 
                           gamma_exposures: List[GammaExposure],
                           current_price: float) -> Dict[str, Any]:
        """
        Generate comprehensive metrics summary
        
        Args:
            gamma_exposures: List of GammaExposure objects
            current_price: Current SPX price
            
        Returns:
            Dictionary with comprehensive metrics summary
        """
        if not gamma_exposures:
            return {"error": "No gamma exposure data available"}
        
        try:
            # Core metrics
            market_metrics = self.calculate_all_metrics(gamma_exposures)
            
            # Additional statistics
            stats = self.calculate_gamma_exposure_statistics(gamma_exposures)
            percentiles = self.calculate_exposure_percentiles(gamma_exposures)
            concentration = self.calculate_concentration_metrics(gamma_exposures)
            
            # Summary
            summary = {
                "core_metrics": market_metrics.to_dict(),
                "current_price": current_price,
                "statistics": stats,
                "percentiles": percentiles,
                "concentration": concentration,
                "data_quality": {
                    "total_strikes": len(gamma_exposures),
                    "strikes_with_exposure": len([ge for ge in gamma_exposures if ge.net_gamma_exposure != 0]),
                    "total_open_interest": sum(ge.total_open_interest for ge in gamma_exposures)
                }
            }
            
            return summary
            
        except Exception as e:
            raise MetricsCalculationError(f"Error generating metrics summary: {str(e)}")