"""
Yahoo Finance data fetcher for options chain data
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from .models import OptionsContract


class YFinanceFetchError(Exception):
    """Custom exception for Yahoo Finance fetch errors"""
    pass


class YFinanceOptionsFetcher:
    """Fetches options chain data from Yahoo Finance"""
    
    def __init__(self):
        """Initialize the fetcher"""
        # Popular symbols for quick selection
        self.popular_symbols = {
            'SPX': '^SPX',  # S&P 500 Index
            'SPY': 'SPY',   # SPDR S&P 500 ETF
            'QQQ': 'QQQ',   # Invesco QQQ Trust
            'IWM': 'IWM',   # iShares Russell 2000 ETF
            'VIX': '^VIX',  # CBOE Volatility Index
            'DIA': 'DIA',   # Dow Jones Industrial Average ETF
            'AAPL': 'AAPL', # Apple Inc.
            'MSFT': 'MSFT', # Microsoft Corporation
            'TSLA': 'TSLA', # Tesla Inc.
            'NVDA': 'NVDA', # NVIDIA Corporation
            'AMZN': 'AMZN', # Amazon.com Inc.
            'GOOGL': 'GOOGL', # Alphabet Inc.
            'META': 'META', # Meta Platforms Inc.
        }
    
    def get_available_symbols(self) -> Dict[str, str]:
        """Get list of popular symbols for quick selection"""
        return self.popular_symbols.copy()
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol exists and has options data
        
        Args:
            symbol: Symbol to validate
            
        Returns:
            True if symbol is valid and has options
        """
        try:
            ticker = yf.Ticker(symbol)
            # Check if options are available
            expirations = ticker.options
            return len(expirations) > 0
        except:
            return False
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for the underlying symbol
        
        Args:
            symbol: Symbol to fetch (e.g., 'SPY', 'SPX', 'AAPL')
            
        Returns:
            Current price of the underlying
        """
        try:
            # Check if it's a popular symbol with special mapping, otherwise use as-is
            yf_symbol = self.popular_symbols.get(symbol, symbol)
            ticker = yf.Ticker(yf_symbol)
            
            # Get current price from info or recent data
            info = ticker.info
            current_price = info.get('regularMarketPrice') or info.get('previousClose')
            
            if current_price is None:
                # Fallback to recent data
                hist = ticker.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            if current_price is None:
                raise YFinanceFetchError(f"Could not fetch current price for {symbol}")
            
            return float(current_price)
            
        except Exception as e:
            raise YFinanceFetchError(f"Error fetching current price for {symbol}: {str(e)}")
    
    def get_expiration_dates(self, symbol: str) -> List[str]:
        """
        Get available expiration dates for options
        
        Args:
            symbol: Symbol to fetch (e.g., 'SPY', 'SPX', 'AAPL')
            
        Returns:
            List of expiration date strings
        """
        try:
            yf_symbol = self.popular_symbols.get(symbol, symbol)
            ticker = yf.Ticker(yf_symbol)
            
            # Get expiration dates
            expirations = ticker.options
            
            if not expirations:
                raise YFinanceFetchError(f"No options expiration dates found for {symbol}")
            
            return list(expirations)
            
        except Exception as e:
            raise YFinanceFetchError(f"Error fetching expiration dates for {symbol}: {str(e)}")
    
    def fetch_options_chain(self, 
                           symbol: str, 
                           expiration_date: Optional[str] = None,
                           include_all_expirations: bool = False) -> pd.DataFrame:
        """
        Fetch options chain data from Yahoo Finance
        
        Args:
            symbol: Symbol to fetch (e.g., 'SPY', 'SPX', 'AAPL', 'TSLA')
            expiration_date: Specific expiration date (YYYY-MM-DD format)
            include_all_expirations: Whether to include all available expirations
            
        Returns:
            DataFrame with options chain data
        """
        try:
            yf_symbol = self.popular_symbols.get(symbol, symbol)
            ticker = yf.Ticker(yf_symbol)
            
            # Get available expiration dates
            expirations = ticker.options
            
            if not expirations:
                raise YFinanceFetchError(f"No options data available for {symbol}")
            
            # Determine which expirations to fetch
            if include_all_expirations:
                target_expirations = expirations[:5]  # Limit to first 5 to avoid too much data
            elif expiration_date:
                if expiration_date not in expirations:
                    raise YFinanceFetchError(f"Expiration date {expiration_date} not available for {symbol}")
                target_expirations = [expiration_date]
            else:
                # Use the nearest expiration
                target_expirations = [expirations[0]]
            
            all_options_data = []
            
            for exp_date in target_expirations:
                try:
                    # Get options chain for this expiration
                    options_chain = ticker.option_chain(exp_date)
                    
                    # Process calls
                    calls_df = options_chain.calls.copy()
                    calls_df['option_type'] = 'call'
                    calls_df['expiry_date'] = exp_date
                    calls_df['symbol'] = symbol
                    
                    # Process puts
                    puts_df = options_chain.puts.copy()
                    puts_df['option_type'] = 'put'
                    puts_df['expiry_date'] = exp_date
                    puts_df['symbol'] = symbol
                    
                    # Combine calls and puts
                    combined_df = pd.concat([calls_df, puts_df], ignore_index=True)
                    all_options_data.append(combined_df)
                    
                except Exception as e:
                    print(f"Warning: Could not fetch data for expiration {exp_date}: {str(e)}")
                    continue
            
            if not all_options_data:
                raise YFinanceFetchError(f"No options data could be fetched for {symbol}")
            
            # Combine all expiration data
            final_df = pd.concat(all_options_data, ignore_index=True)
            
            # Standardize column names to match our expected format
            final_df = self._standardize_columns(final_df)
            
            # Clean and validate the data
            final_df = self._clean_options_data(final_df)
            
            return final_df
            
        except Exception as e:
            if isinstance(e, YFinanceFetchError):
                raise
            else:
                raise YFinanceFetchError(f"Error fetching options chain for {symbol}: {str(e)}")
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to match our expected format"""
        
        # Column mapping from yfinance to our format
        column_mapping = {
            'strike': 'strike',
            'lastPrice': 'last_price',
            'bid': 'bid',
            'ask': 'ask',
            'volume': 'volume',
            'openInterest': 'open_interest',
            'impliedVolatility': 'implied_volatility',
            'option_type': 'option_type',
            'expiry_date': 'expiry_date',
            'symbol': 'symbol'
        }
        
        # Rename columns
        available_columns = {col: column_mapping.get(col, col) for col in df.columns if col in column_mapping}
        df = df.rename(columns=available_columns)
        
        # Ensure required columns exist
        required_columns = ['strike', 'option_type', 'expiry_date', 'symbol']
        for col in required_columns:
            if col not in df.columns:
                if col == 'symbol':
                    df[col] = 'SPY'  # Default symbol
                else:
                    raise YFinanceFetchError(f"Required column {col} not found in options data")
        
        # Add missing optional columns with defaults
        if 'open_interest' not in df.columns:
            df['open_interest'] = 0
        if 'volume' not in df.columns:
            df['volume'] = 0
        if 'bid' not in df.columns:
            df['bid'] = 0.0
        if 'ask' not in df.columns:
            df['ask'] = 0.0
        if 'last_price' not in df.columns:
            df['last_price'] = 0.0
        if 'implied_volatility' not in df.columns:
            df['implied_volatility'] = 0.2
        
        return df
    
    def _clean_options_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate options data"""
        
        # Remove rows with invalid strikes
        df = df[df['strike'] > 0]
        
        # Convert expiry_date to datetime
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        
        # Remove expired options (allow options expiring today)
        today = pd.Timestamp.now().normalize()
        df = df[df['expiry_date'] >= today]  # Changed from > to >= to include today
        
        # Fill NaN values
        numeric_columns = ['open_interest', 'volume', 'bid', 'ask', 'last_price', 'implied_volatility']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # Ensure positive values for certain columns
        df['open_interest'] = df['open_interest'].abs()
        df['volume'] = df['volume'].abs()
        df['implied_volatility'] = df['implied_volatility'].abs()
        
        # Set minimum implied volatility
        df.loc[df['implied_volatility'] < 0.01, 'implied_volatility'] = 0.01
        
        # Remove rows with zero open interest (optional - can be commented out)
        # df = df[df['open_interest'] > 0]
        
        # Sort by strike and option type
        df = df.sort_values(['expiry_date', 'strike', 'option_type']).reset_index(drop=True)
        
        return df
    
    def get_options_summary(self, symbol: str) -> Dict[str, Any]:
        """
        Get summary information about available options
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Dictionary with summary information
        """
        try:
            yf_symbol = self.popular_symbols.get(symbol, symbol)
            ticker = yf.Ticker(yf_symbol)
            
            # Get basic info
            info = ticker.info
            current_price = self.get_current_price(symbol)
            expirations = ticker.options
            
            # Get sample options chain for analysis
            if expirations:
                sample_chain = ticker.option_chain(expirations[0])
                total_calls = len(sample_chain.calls)
                total_puts = len(sample_chain.puts)
                
                # Calculate strike range
                all_strikes = list(sample_chain.calls['strike']) + list(sample_chain.puts['strike'])
                strike_range = {
                    'min': min(all_strikes) if all_strikes else 0,
                    'max': max(all_strikes) if all_strikes else 0
                }
            else:
                total_calls = 0
                total_puts = 0
                strike_range = {'min': 0, 'max': 0}
            
            summary = {
                'symbol': symbol,
                'yf_symbol': yf_symbol,
                'current_price': current_price,
                'company_name': info.get('longName', symbol),
                'available_expirations': len(expirations),
                'expiration_dates': expirations[:10] if expirations else [],  # Show first 10
                'sample_expiration_stats': {
                    'total_calls': total_calls,
                    'total_puts': total_puts,
                    'strike_range': strike_range
                }
            }
            
            return summary
            
        except Exception as e:
            raise YFinanceFetchError(f"Error getting options summary for {symbol}: {str(e)}")
    
    def convert_to_contracts(self, df: pd.DataFrame) -> List[OptionsContract]:
        """
        Convert DataFrame to list of OptionsContract objects
        
        Args:
            df: Options data DataFrame
            
        Returns:
            List of OptionsContract objects
        """
        contracts = []
        skipped_rows = 0
        
        for _, row in df.iterrows():
            try:
                contract = OptionsContract(
                    symbol=row.get('symbol', 'SPY'),
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
                # Skip invalid rows
                skipped_rows += 1
                continue
        
        if skipped_rows > 0:
            print(f"Warning: Skipped {skipped_rows} invalid rows during contract conversion")
        
        return contracts