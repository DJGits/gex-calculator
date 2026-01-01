"""
Options data processing and validation
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import io
from pathlib import Path

from .models import OptionsContract, dataframe_to_options_contracts
from config import SUPPORTED_FILE_TYPES, MAX_FILE_SIZE_MB


class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass


class OptionsDataProcessor:
    """Handles loading, validation, and preprocessing of options chain data"""
    
    REQUIRED_COLUMNS = [
        'strike', 'expiry_date', 'option_type', 'open_interest'
    ]
    
    OPTIONAL_COLUMNS = [
        'symbol', 'volume', 'bid', 'ask', 'last_price', 'implied_volatility'
    ]
    
    def __init__(self):
        self.last_loaded_data: Optional[pd.DataFrame] = None
        self.validation_errors: List[str] = []
    
    def load_options_data(self, file_path_or_buffer) -> pd.DataFrame:
        """
        Load options data from file or buffer
        
        Args:
            file_path_or_buffer: File path string, Path object, or file-like buffer
            
        Returns:
            pd.DataFrame: Loaded and validated options data
            
        Raises:
            DataValidationError: If file format is invalid or data cannot be loaded
        """
        try:
            # Handle different input types
            if isinstance(file_path_or_buffer, (str, Path)):
                file_path = Path(file_path_or_buffer)
                if not file_path.exists():
                    raise DataValidationError(f"File not found: {file_path}")
                
                # Check file size
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    raise DataValidationError(f"File too large: {file_size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB")
                
                # Load based on file extension
                suffix = file_path.suffix.lower()
                if suffix == '.csv':
                    df = pd.read_csv(file_path)
                elif suffix in ['.xlsx', '.xls']:
                    df = pd.read_excel(file_path)
                else:
                    raise DataValidationError(f"Unsupported file type: {suffix}. Supported: {SUPPORTED_FILE_TYPES}")
            
            else:
                # Assume it's a file-like buffer
                try:
                    # Try CSV first
                    df = pd.read_csv(file_path_or_buffer)
                except:
                    # Reset buffer position and try Excel
                    if hasattr(file_path_or_buffer, 'seek'):
                        file_path_or_buffer.seek(0)
                    df = pd.read_excel(file_path_or_buffer)
            
            # Validate and clean the data
            df = self.validate_data_format(df)
            df = self.clean_and_normalize(df)
            
            self.last_loaded_data = df
            return df
            
        except Exception as e:
            if isinstance(e, DataValidationError):
                raise
            else:
                raise DataValidationError(f"Error loading data: {str(e)}")
    
    def validate_data_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate that DataFrame has required columns and data types
        
        Args:
            df: Input DataFrame
            
        Returns:
            pd.DataFrame: Validated DataFrame
            
        Raises:
            DataValidationError: If validation fails
        """
        self.validation_errors = []
        
        if df.empty:
            raise DataValidationError("Data file is empty")
        
        # Check for required columns
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise DataValidationError(f"Missing required columns: {missing_columns}")
        
        # Validate data types and ranges
        try:
            # Strike prices must be positive numbers
            if not pd.api.types.is_numeric_dtype(df['strike']):
                df['strike'] = pd.to_numeric(df['strike'], errors='coerce')
            
            invalid_strikes = df['strike'].isna() | (df['strike'] <= 0)
            if invalid_strikes.any():
                self.validation_errors.append(f"Invalid strike prices found in {invalid_strikes.sum()} rows")
            
            # Option type must be 'call' or 'put'
            df['option_type'] = df['option_type'].str.lower().str.strip()
            invalid_types = ~df['option_type'].isin(['call', 'put'])
            if invalid_types.any():
                self.validation_errors.append(f"Invalid option types found in {invalid_types.sum()} rows")
            
            # Open interest must be non-negative integers
            if not pd.api.types.is_numeric_dtype(df['open_interest']):
                df['open_interest'] = pd.to_numeric(df['open_interest'], errors='coerce')
            
            invalid_oi = df['open_interest'].isna() | (df['open_interest'] < 0)
            if invalid_oi.any():
                self.validation_errors.append(f"Invalid open interest values found in {invalid_oi.sum()} rows")
            
            # Expiry date validation
            if not pd.api.types.is_datetime64_any_dtype(df['expiry_date']):
                df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
            
            invalid_dates = df['expiry_date'].isna()
            if invalid_dates.any():
                self.validation_errors.append(f"Invalid expiry dates found in {invalid_dates.sum()} rows")
            
            # Check for future expiry dates
            today = pd.Timestamp.now().normalize()
            past_dates = df['expiry_date'] < today
            if past_dates.any():
                self.validation_errors.append(f"Past expiry dates found in {past_dates.sum()} rows")
            
        except Exception as e:
            raise DataValidationError(f"Data type validation failed: {str(e)}")
        
        # Report validation errors but don't fail unless critical
        if self.validation_errors:
            error_summary = "; ".join(self.validation_errors)
            # For now, just warn - in production might want to be stricter
            print(f"Data validation warnings: {error_summary}")
        
        return df
    
    def clean_and_normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize the data
        
        Args:
            df: Input DataFrame
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        df = df.copy()
        
        # Remove rows with critical missing data
        critical_missing = (
            df['strike'].isna() | 
            df['option_type'].isna() | 
            df['expiry_date'].isna() |
            (df['strike'] <= 0)
        )
        
        if critical_missing.any():
            print(f"Removing {critical_missing.sum()} rows with critical missing data")
            df = df[~critical_missing]
        
        # Fill optional columns with defaults
        if 'symbol' not in df.columns:
            df['symbol'] = 'SPX'
        
        if 'volume' not in df.columns:
            df['volume'] = 0
        else:
            df['volume'] = df['volume'].fillna(0)
        
        if 'bid' not in df.columns:
            df['bid'] = 0.0
        else:
            df['bid'] = df['bid'].fillna(0.0)
        
        if 'ask' not in df.columns:
            df['ask'] = 0.0
        else:
            df['ask'] = df['ask'].fillna(0.0)
        
        if 'last_price' not in df.columns:
            df['last_price'] = 0.0
        else:
            df['last_price'] = df['last_price'].fillna(0.0)
        
        if 'implied_volatility' not in df.columns:
            df['implied_volatility'] = 0.2  # Default 20% volatility
        else:
            df['implied_volatility'] = df['implied_volatility'].fillna(0.2)
            
            # IV Normalization Strategy:
            # Yahoo Finance returns IV as decimal (0.25 = 25%, 1.5 = 150%)
            # Some sources may return as percentage (25 = 25%, 150 = 150%)
            # 
            # Decision logic:
            # - If IV > 10: Definitely a percentage, divide by 100 (e.g., 25 → 0.25, 150 → 1.50)
            # - If IV <= 10: Already in decimal format, use as-is (e.g., 0.25, 1.5, 2.0)
            #
            # Rationale: IV rarely exceeds 1000%, so any value > 10 must be a percentage
            # Values 0-10 are treated as decimals since they represent 0-1000% IV range
            
            # Apply normalization only to values > 10
            mask = df['implied_volatility'] > 10.0
            if mask.any():
                print(f"Normalizing {mask.sum()} IV values from percentage to decimal")
                df.loc[mask, 'implied_volatility'] = df.loc[mask, 'implied_volatility'] / 100.0
        
        # Ensure open interest is integer
        df['open_interest'] = df['open_interest'].fillna(0).astype(int)
        df['volume'] = df['volume'].astype(int)
        
        # Sort by strike and option type for consistency
        df = df.sort_values(['strike', 'option_type']).reset_index(drop=True)
        
        return df
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for loaded data
        
        Args:
            df: Options data DataFrame
            
        Returns:
            Dict containing summary statistics
        """
        if df.empty:
            return {"error": "No data available"}
        
        summary = {
            "total_contracts": len(df),
            "unique_strikes": df['strike'].nunique(),
            "strike_range": {
                "min": float(df['strike'].min()),
                "max": float(df['strike'].max())
            },
            "expiry_dates": {
                "min": df['expiry_date'].min().strftime('%Y-%m-%d'),
                "max": df['expiry_date'].max().strftime('%Y-%m-%d'),
                "unique_count": df['expiry_date'].nunique()
            },
            "option_types": {
                "calls": int((df['option_type'] == 'call').sum()),
                "puts": int((df['option_type'] == 'put').sum())
            },
            "total_open_interest": int(df['open_interest'].sum()),
            "avg_implied_volatility": float(df['implied_volatility'].mean()),
            "validation_errors": self.validation_errors
        }
        
        return summary
    
    def convert_to_contracts(self, df: pd.DataFrame) -> List[OptionsContract]:
        """
        Convert DataFrame to list of OptionsContract objects
        
        Args:
            df: Options data DataFrame
            
        Returns:
            List of OptionsContract objects
        """
        try:
            return dataframe_to_options_contracts(df)
        except Exception as e:
            raise DataValidationError(f"Error converting to contracts: {str(e)}")
    
    def create_sample_data(self, 
                          spot_price: float = 4500, 
                          num_strikes: int = 20,
                          days_to_expiry: int = 30) -> pd.DataFrame:
        """
        Create sample options data for testing
        
        Args:
            spot_price: Current SPX price
            num_strikes: Number of strike prices to generate
            days_to_expiry: Days until expiration
            
        Returns:
            pd.DataFrame: Sample options data
        """
        # Generate strikes around current price
        strike_range = np.linspace(spot_price * 0.9, spot_price * 1.1, num_strikes)
        
        data = []
        expiry_date = datetime.now() + pd.Timedelta(days=days_to_expiry)
        
        for strike in strike_range:
            # Create call option
            data.append({
                'symbol': 'SPX',
                'strike': round(strike),
                'expiry_date': expiry_date,
                'option_type': 'call',
                'open_interest': np.random.randint(100, 5000),
                'volume': np.random.randint(0, 1000),
                'bid': max(0.1, spot_price - strike + np.random.normal(0, 10)),
                'ask': max(0.2, spot_price - strike + np.random.normal(0, 10) + 0.5),
                'last_price': max(0.15, spot_price - strike + np.random.normal(0, 10) + 0.25),
                'implied_volatility': max(0.1, np.random.normal(0.2, 0.05))
            })
            
            # Create put option
            data.append({
                'symbol': 'SPX',
                'strike': round(strike),
                'expiry_date': expiry_date,
                'option_type': 'put',
                'open_interest': np.random.randint(100, 5000),
                'volume': np.random.randint(0, 1000),
                'bid': max(0.1, strike - spot_price + np.random.normal(0, 10)),
                'ask': max(0.2, strike - spot_price + np.random.normal(0, 10) + 0.5),
                'last_price': max(0.15, strike - spot_price + np.random.normal(0, 10) + 0.25),
                'implied_volatility': max(0.1, np.random.normal(0.2, 0.05))
            })
        
        return pd.DataFrame(data)