"""
Data models for SPX Gamma Exposure Calculator
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd


@dataclass
class OptionsContract:
    """Represents a single options contract"""
    symbol: str
    strike: float
    expiry_date: datetime
    option_type: str  # 'call' or 'put'
    open_interest: int
    volume: int
    bid: float
    ask: float
    last_price: float
    implied_volatility: float
    
    def __post_init__(self):
        """Validate data after initialization"""
        if self.option_type not in ['call', 'put']:
            raise ValueError(f"Invalid option_type: {self.option_type}. Must be 'call' or 'put'")
        if self.strike <= 0:
            raise ValueError(f"Strike price must be positive: {self.strike}")
        if self.open_interest < 0:
            raise ValueError(f"Open interest cannot be negative: {self.open_interest}")
        if self.implied_volatility < 0:
            raise ValueError(f"Implied volatility cannot be negative: {self.implied_volatility}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'symbol': self.symbol,
            'strike': self.strike,
            'expiry_date': self.expiry_date.isoformat(),
            'option_type': self.option_type,
            'open_interest': self.open_interest,
            'volume': self.volume,
            'bid': self.bid,
            'ask': self.ask,
            'last_price': self.last_price,
            'implied_volatility': self.implied_volatility
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptionsContract':
        """Create instance from dictionary"""
        data = data.copy()
        if isinstance(data['expiry_date'], str):
            data['expiry_date'] = datetime.fromisoformat(data['expiry_date'])
        return cls(**data)


@dataclass
class GammaExposure:
    """Represents gamma exposure data for a strike price"""
    strike: float
    call_gamma_exposure: float
    put_gamma_exposure: float
    net_gamma_exposure: float
    total_open_interest: int
    
    def __post_init__(self):
        """Validate and calculate derived values"""
        if self.strike <= 0:
            raise ValueError(f"Strike price must be positive: {self.strike}")
        if self.total_open_interest < 0:
            raise ValueError(f"Total open interest cannot be negative: {self.total_open_interest}")
        
        # Verify net gamma calculation
        calculated_net = self.call_gamma_exposure + self.put_gamma_exposure
        if abs(calculated_net - self.net_gamma_exposure) > 1e-6:
            raise ValueError(f"Net gamma exposure mismatch: {self.net_gamma_exposure} != {calculated_net}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'strike': self.strike,
            'call_gamma_exposure': self.call_gamma_exposure,
            'put_gamma_exposure': self.put_gamma_exposure,
            'net_gamma_exposure': self.net_gamma_exposure,
            'total_open_interest': self.total_open_interest
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GammaExposure':
        """Create instance from dictionary"""
        return cls(**data)


@dataclass
class WallLevel:
    """Represents a gamma wall (support/resistance level)"""
    strike: float
    exposure_value: float
    wall_type: str  # 'call_wall' or 'put_wall'
    distance_from_spot: float
    significance_rank: int
    
    def __post_init__(self):
        """Validate wall data"""
        if self.wall_type not in ['call_wall', 'put_wall']:
            raise ValueError(f"Invalid wall_type: {self.wall_type}. Must be 'call_wall' or 'put_wall'")
        if self.strike <= 0:
            raise ValueError(f"Strike price must be positive: {self.strike}")
        if self.significance_rank < 1:
            raise ValueError(f"Significance rank must be >= 1: {self.significance_rank}")
        if self.distance_from_spot < 0:
            raise ValueError(f"Distance from spot cannot be negative: {self.distance_from_spot}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'strike': self.strike,
            'exposure_value': self.exposure_value,
            'wall_type': self.wall_type,
            'distance_from_spot': self.distance_from_spot,
            'significance_rank': self.significance_rank
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WallLevel':
        """Create instance from dictionary"""
        return cls(**data)


@dataclass
class MarketMetrics:
    """Represents calculated market metrics"""
    total_net_gamma: float
    gamma_weighted_avg_strike: float
    call_put_gamma_ratio: float
    max_call_exposure: float
    max_put_exposure: float
    gamma_exposure_std: float
    
    def __post_init__(self):
        """Validate metrics"""
        if self.call_put_gamma_ratio < 0:
            raise ValueError(f"Call/put gamma ratio cannot be negative: {self.call_put_gamma_ratio}")
        # Allow gamma_weighted_avg_strike to be 0 (when there's no gamma exposure)
        if self.gamma_weighted_avg_strike < 0:
            raise ValueError(f"Gamma weighted average strike cannot be negative: {self.gamma_weighted_avg_strike}")
        if self.gamma_exposure_std < 0:
            raise ValueError(f"Standard deviation cannot be negative: {self.gamma_exposure_std}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'total_net_gamma': self.total_net_gamma,
            'gamma_weighted_avg_strike': self.gamma_weighted_avg_strike,
            'call_put_gamma_ratio': self.call_put_gamma_ratio,
            'max_call_exposure': self.max_call_exposure,
            'max_put_exposure': self.max_put_exposure,
            'gamma_exposure_std': self.gamma_exposure_std
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketMetrics':
        """Create instance from dictionary"""
        return cls(**data)


def dataframe_to_options_contracts(df: pd.DataFrame) -> list[OptionsContract]:
    """Convert DataFrame to list of OptionsContract objects"""
    contracts = []
    for _, row in df.iterrows():
        try:
            contract = OptionsContract(
                symbol=row.get('symbol', 'SPX'),
                strike=float(row['strike']),
                expiry_date=pd.to_datetime(row['expiry_date']),
                option_type=str(row['option_type']).lower(),
                open_interest=int(row.get('open_interest', 0)),
                volume=int(row.get('volume', 0)),
                bid=float(row.get('bid', 0.0)),
                ask=float(row.get('ask', 0.0)),
                last_price=float(row.get('last_price', 0.0)),
                implied_volatility=float(row.get('implied_volatility', 0.2))
            )
            contracts.append(contract)
        except (ValueError, KeyError) as e:
            raise ValueError(f"Error processing row {row.name}: {e}")
    
    return contracts


def options_contracts_to_dataframe(contracts: list[OptionsContract]) -> pd.DataFrame:
    """Convert list of OptionsContract objects to DataFrame"""
    data = [contract.to_dict() for contract in contracts]
    df = pd.DataFrame(data)
    if not df.empty:
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
    return df