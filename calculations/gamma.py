"""
Gamma calculation using Black-Scholes model
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import List, Dict, Any, Optional
from datetime import datetime

from data.models import OptionsContract, GammaExposure
from config import SPX_CONTRACT_MULTIPLIER, DEFAULT_RISK_FREE_RATE, DEFAULT_VOLATILITY
from config import MIN_TIME_TO_EXPIRY, MAX_TIME_TO_EXPIRY, MIN_VOLATILITY, MAX_VOLATILITY


class GammaCalculationError(Exception):
    """Custom exception for gamma calculation errors"""
    pass


class GammaCalculator:
    """Calculates gamma values and exposure using Black-Scholes model"""
    
    def __init__(self, 
                 risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
                 contract_multiplier: int = SPX_CONTRACT_MULTIPLIER):
        """
        Initialize gamma calculator
        
        Args:
            risk_free_rate: Risk-free interest rate (default from config)
            contract_multiplier: Contract multiplier for exposure calculation
        """
        self.risk_free_rate = risk_free_rate
        self.contract_multiplier = contract_multiplier
        self.validate_parameters()
    
    def validate_parameters(self):
        """Validate calculator parameters"""
        if not 0 <= self.risk_free_rate <= 1:
            raise GammaCalculationError(f"Risk-free rate must be between 0 and 1: {self.risk_free_rate}")
        if self.contract_multiplier <= 0:
            raise GammaCalculationError(f"Contract multiplier must be positive: {self.contract_multiplier}")
    
    def calculate_time_to_expiry(self, expiry_date: datetime, current_date: Optional[datetime] = None) -> float:
        """
        Calculate time to expiry in years
        
        Args:
            expiry_date: Option expiry date
            current_date: Current date (defaults to now)
            
        Returns:
            Time to expiry in years
        """
        if current_date is None:
            current_date = datetime.now()
        
        time_diff = (expiry_date - current_date).total_seconds() / (365.25 * 24 * 3600)
        
        # For options expiring today or very soon, use minimum time to expiry
        if time_diff <= 0:
            time_to_expiry = MIN_TIME_TO_EXPIRY  # Use minimum instead of raising error
        else:
            # Ensure time is within reasonable bounds
            time_to_expiry = max(MIN_TIME_TO_EXPIRY, min(MAX_TIME_TO_EXPIRY, time_diff))
        
        return time_to_expiry
    
    def calculate_gamma(self, 
                       spot: float, 
                       strike: float, 
                       time_to_expiry: float, 
                       volatility: float, 
                       option_type: str) -> float:
        """
        Calculate gamma using Black-Scholes formula
        
        Args:
            spot: Current underlying price
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility
            option_type: 'call' or 'put'
            
        Returns:
            Gamma value
        """
        # Validate inputs
        if spot <= 0:
            raise GammaCalculationError(f"Spot price must be positive: {spot}")
        if strike <= 0:
            raise GammaCalculationError(f"Strike price must be positive: {strike}")
        if time_to_expiry <= 0:
            raise GammaCalculationError(f"Time to expiry must be positive: {time_to_expiry}")
        if not MIN_VOLATILITY <= volatility <= MAX_VOLATILITY:
            raise GammaCalculationError(f"Volatility must be between {MIN_VOLATILITY} and {MAX_VOLATILITY}: {volatility}")
        if option_type not in ['call', 'put']:
            raise GammaCalculationError(f"Option type must be 'call' or 'put': {option_type}")
        
        try:
            # Black-Scholes gamma calculation
            d1 = (np.log(spot / strike) + (self.risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
            
            # Gamma is the same for calls and puts
            gamma = norm.pdf(d1) / (spot * volatility * np.sqrt(time_to_expiry))
            
            # Handle numerical issues
            if np.isnan(gamma) or np.isinf(gamma):
                raise GammaCalculationError("Gamma calculation resulted in NaN or infinity")
            
            return float(gamma)
            
        except Exception as e:
            if isinstance(e, GammaCalculationError):
                raise
            else:
                raise GammaCalculationError(f"Error calculating gamma: {str(e)}")
    
    def calculate_exposure(self, 
                          gamma: float, 
                          open_interest: int, 
                          spot: float,
                          option_type: str) -> float:
        """
        Calculate gamma exposure (gamma × open interest × multiplier × spot)
        
        Args:
            gamma: Gamma value
            open_interest: Number of contracts
            spot: Current underlying price
            option_type: 'call' or 'put'
            
        Returns:
            Gamma exposure value
        """
        if open_interest < 0:
            raise GammaCalculationError(f"Open interest cannot be negative: {open_interest}")
        if spot <= 0:
            raise GammaCalculationError(f"Spot price must be positive: {spot}")
        
        # Basic exposure calculation
        exposure = gamma * open_interest * self.contract_multiplier * spot
        
        # Apply sign convention: 
        # - Market makers are typically short options, so they have opposite gamma exposure
        # - When MM are short calls, they have negative gamma (need to buy as price rises)
        # - When MM are short puts, they have positive gamma (need to sell as price falls)
        if option_type == 'call':
            exposure = -exposure  # Negative for calls (resistance)
        else:  # put
            exposure = exposure   # Positive for puts (support)
        
        return float(exposure)
    
    def calculate_contract_gamma_exposure(self, 
                                        contract: OptionsContract, 
                                        spot: float,
                                        current_date: Optional[datetime] = None) -> float:
        """
        Calculate gamma exposure for a single options contract
        
        Args:
            contract: OptionsContract object
            spot: Current underlying price
            current_date: Current date (defaults to now)
            
        Returns:
            Gamma exposure for the contract
        """
        try:
            # Calculate time to expiry
            time_to_expiry = self.calculate_time_to_expiry(contract.expiry_date, current_date)
            
            # Use implied volatility from contract, with fallback
            volatility = contract.implied_volatility if contract.implied_volatility > 0 else DEFAULT_VOLATILITY
            volatility = max(MIN_VOLATILITY, min(MAX_VOLATILITY, volatility))
            
            # Calculate gamma
            gamma = self.calculate_gamma(
                spot=spot,
                strike=contract.strike,
                time_to_expiry=time_to_expiry,
                volatility=volatility,
                option_type=contract.option_type
            )
            
            # Calculate exposure
            exposure = self.calculate_exposure(
                gamma=gamma,
                open_interest=contract.open_interest,
                spot=spot,
                option_type=contract.option_type
            )
            
            return exposure
            
        except Exception as e:
            raise GammaCalculationError(f"Error calculating exposure for contract {contract.symbol} {contract.strike} {contract.option_type}: {str(e)}")
    
    def aggregate_by_strike(self, 
                           contracts: List[OptionsContract], 
                           spot: float,
                           current_date: Optional[datetime] = None) -> List[GammaExposure]:
        """
        Calculate and aggregate gamma exposure by strike price
        
        Args:
            contracts: List of OptionsContract objects
            spot: Current underlying price
            current_date: Current date (defaults to now)
            
        Returns:
            List of GammaExposure objects aggregated by strike
        """
        if not contracts:
            return []
        
        # Group contracts by strike
        strike_groups = {}
        for contract in contracts:
            strike = contract.strike
            if strike not in strike_groups:
                strike_groups[strike] = {'calls': [], 'puts': []}
            
            if contract.option_type == 'call':
                strike_groups[strike]['calls'].append(contract)
            else:
                strike_groups[strike]['puts'].append(contract)
        
        # Calculate exposure for each strike
        gamma_exposures = []
        
        for strike, groups in strike_groups.items():
            call_exposure = 0.0
            put_exposure = 0.0
            total_oi = 0
            
            # Calculate call exposure
            for call_contract in groups['calls']:
                try:
                    exposure = self.calculate_contract_gamma_exposure(call_contract, spot, current_date)
                    call_exposure += exposure
                    total_oi += call_contract.open_interest
                except GammaCalculationError as e:
                    print(f"Warning: {e}")
                    continue
            
            # Calculate put exposure  
            for put_contract in groups['puts']:
                try:
                    exposure = self.calculate_contract_gamma_exposure(put_contract, spot, current_date)
                    put_exposure += exposure
                    total_oi += put_contract.open_interest
                except GammaCalculationError as e:
                    print(f"Warning: {e}")
                    continue
            
            # Create GammaExposure object
            net_exposure = call_exposure + put_exposure
            
            gamma_exposure = GammaExposure(
                strike=strike,
                call_gamma_exposure=call_exposure,
                put_gamma_exposure=put_exposure,
                net_gamma_exposure=net_exposure,
                total_open_interest=total_oi
            )
            
            gamma_exposures.append(gamma_exposure)
        
        # Sort by strike price
        gamma_exposures.sort(key=lambda x: x.strike)
        
        return gamma_exposures
    
    def calculate_portfolio_metrics(self, gamma_exposures: List[GammaExposure]) -> Dict[str, float]:
        """
        Calculate portfolio-level gamma metrics
        
        Args:
            gamma_exposures: List of GammaExposure objects
            
        Returns:
            Dictionary of portfolio metrics
        """
        if not gamma_exposures:
            return {
                'total_net_gamma': 0.0,
                'total_call_gamma': 0.0,
                'total_put_gamma': 0.0,
                'gamma_weighted_avg_strike': 0.0,
                'total_open_interest': 0
            }
        
        total_net_gamma = sum(ge.net_gamma_exposure for ge in gamma_exposures)
        total_call_gamma = sum(ge.call_gamma_exposure for ge in gamma_exposures)
        total_put_gamma = sum(ge.put_gamma_exposure for ge in gamma_exposures)
        total_open_interest = sum(ge.total_open_interest for ge in gamma_exposures)
        
        # Calculate gamma-weighted average strike
        if total_net_gamma != 0:
            weighted_sum = sum(ge.strike * abs(ge.net_gamma_exposure) for ge in gamma_exposures)
            total_abs_gamma = sum(abs(ge.net_gamma_exposure) for ge in gamma_exposures)
            gamma_weighted_avg_strike = weighted_sum / total_abs_gamma if total_abs_gamma > 0 else 0.0
        else:
            gamma_weighted_avg_strike = 0.0
        
        return {
            'total_net_gamma': total_net_gamma,
            'total_call_gamma': total_call_gamma,
            'total_put_gamma': total_put_gamma,
            'gamma_weighted_avg_strike': gamma_weighted_avg_strike,
            'total_open_interest': total_open_interest
        }