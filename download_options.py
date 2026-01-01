#!/usr/bin/env python3
"""
Options Chain Downloader - Download and save options data to CSV
Usage: python download_options.py SYMBOL [EXPIRATION]
"""

import sys
import argparse
from datetime import datetime
import yfinance as yf
import pandas as pd


def list_expirations(symbol):
    """List all available expiration dates for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        expirations = ticker.options
        
        if not expirations:
            print(f"❌ No options available for {symbol}")
            return []
        
        print(f"\n📅 Available expiration dates for {symbol}:")
        print("-" * 50)
        for i, exp_date in enumerate(expirations, 1):
            print(f"{i:2d}. {exp_date}")
        print("-" * 50)
        
        return expirations
    except Exception as e:
        print(f"❌ Error fetching expirations: {str(e)}")
        return []


def download_options_chain(symbol, expiration=None, output_file=None):
    """
    Download options chain data and save to CSV
    
    Args:
        symbol: Stock symbol (e.g., 'SPY', 'AAPL')
        expiration: Expiration date (YYYY-MM-DD) or None for nearest
        output_file: Output CSV filename or None for auto-generated
    
    Returns:
        Path to saved CSV file or None on error
    """
    try:
        print(f"\n📊 Downloading options chain for {symbol}...")
        
        # Get ticker
        ticker = yf.Ticker(symbol)
        
        # Get available expirations
        expirations = ticker.options
        if not expirations:
            print(f"❌ No options available for {symbol}")
            return None
        
        # Determine which expiration to use
        if expiration:
            if expiration not in expirations:
                print(f"❌ Expiration {expiration} not available")
                print(f"Available expirations: {', '.join(expirations[:5])}...")
                return None
            selected_expiration = expiration
        else:
            selected_expiration = expirations[0]
            print(f"📅 Using nearest expiration: {selected_expiration}")
        
        # Fetch options chain
        print(f"⏳ Fetching options data...")
        options_chain = ticker.option_chain(selected_expiration)
        
        # Get current price
        try:
            info = ticker.info
            current_price = info.get('regularMarketPrice') or info.get('previousClose')
            if current_price is None:
                hist = ticker.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
        except:
            current_price = None
        
        # Process calls
        calls_df = options_chain.calls.copy()
        calls_df['option_type'] = 'call'
        calls_df['expiry_date'] = selected_expiration
        calls_df['symbol'] = symbol
        
        # Process puts
        puts_df = options_chain.puts.copy()
        puts_df['option_type'] = 'put'
        puts_df['expiry_date'] = selected_expiration
        puts_df['symbol'] = symbol
        
        # Combine
        combined_df = pd.concat([calls_df, puts_df], ignore_index=True)
        
        # Standardize column names
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
        available_columns = {col: column_mapping.get(col, col) 
                           for col in combined_df.columns if col in column_mapping}
        combined_df = combined_df.rename(columns=available_columns)
        
        # Select and order columns
        output_columns = [
            'symbol', 'strike', 'expiry_date', 'option_type',
            'last_price', 'bid', 'ask', 'volume', 'open_interest', 'implied_volatility'
        ]
        
        # Keep only columns that exist
        output_columns = [col for col in output_columns if col in combined_df.columns]
        final_df = combined_df[output_columns]
        
        # Sort by strike and option type
        final_df = final_df.sort_values(['strike', 'option_type']).reset_index(drop=True)
        
        # Generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"{symbol}_{selected_expiration}_{timestamp}.csv"
        
        # Save to CSV
        final_df.to_csv(output_file, index=False)
        
        # Display summary
        print(f"\n✅ Successfully downloaded options chain!")
        print(f"📁 Saved to: {output_file}")
        print(f"\n📊 Summary:")
        print(f"   Symbol: {symbol}")
        if current_price:
            print(f"   Current Price: ${current_price:.2f}")
        print(f"   Expiration: {selected_expiration}")
        print(f"   Total Contracts: {len(final_df)}")
        print(f"   Calls: {len(final_df[final_df['option_type'] == 'call'])}")
        print(f"   Puts: {len(final_df[final_df['option_type'] == 'put'])}")
        print(f"   Unique Strikes: {final_df['strike'].nunique()}")
        print(f"   Total Open Interest: {final_df['open_interest'].sum():,.0f}")
        
        # Show strike range
        min_strike = final_df['strike'].min()
        max_strike = final_df['strike'].max()
        print(f"   Strike Range: {min_strike:.0f} - {max_strike:.0f}")
        
        # Show sample data
        print(f"\n📋 Sample Data (first 5 rows):")
        print(final_df.head().to_string(index=False))
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error downloading options chain: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Download options chain data to CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download nearest expiration for SPY
  python download_options.py SPY
  
  # Download specific expiration
  python download_options.py SPY 2025-01-17
  
  # List available expirations
  python download_options.py SPY --list
  
  # Specify output filename
  python download_options.py AAPL 2025-02-21 --output aapl_options.csv
  
  # Interactive mode
  python download_options.py SPY --interactive
        """
    )
    
    parser.add_argument('symbol', help='Stock symbol (e.g., SPY, AAPL, TSLA)')
    parser.add_argument('expiration', nargs='?', help='Expiration date (YYYY-MM-DD) or omit for nearest')
    parser.add_argument('--list', '-l', action='store_true', help='List available expirations and exit')
    parser.add_argument('--output', '-o', help='Output CSV filename')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive expiration selection')
    
    args = parser.parse_args()
    
    symbol = args.symbol.upper()
    
    # List expirations mode
    if args.list:
        list_expirations(symbol)
        return 0
    
    # Interactive mode
    if args.interactive:
        expirations = list_expirations(symbol)
        if not expirations:
            return 1
        
        try:
            choice = input(f"\nSelect expiration (1-{len(expirations)}) or press Enter for nearest: ").strip()
            if choice:
                idx = int(choice) - 1
                if 0 <= idx < len(expirations):
                    expiration = expirations[idx]
                else:
                    print("Invalid choice, using nearest expiration")
                    expiration = None
            else:
                expiration = None
        except (ValueError, KeyboardInterrupt):
            print("\nUsing nearest expiration")
            expiration = None
    else:
        expiration = args.expiration
    
    # Download options chain
    result = download_options_chain(symbol, expiration, args.output)
    
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
