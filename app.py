"""
Gamma Exposure Calculator - Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
from typing import Optional, Dict, Any

# Import our modules
from data.processor import OptionsDataProcessor, DataValidationError
from data.yfinance_fetcher import YFinanceOptionsFetcher, YFinanceFetchError
from calculations.gamma import GammaCalculator, GammaCalculationError
from analysis.walls import WallAnalyzer, WallAnalysisError
from analysis.metrics import MetricsCalculator, MetricsCalculationError
from visualization.charts import VisualizationEngine, VisualizationError
from ui.export import ExportManager, ExportError

# Configure page
st.set_page_config(
    page_title="Gamma Exposure Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'gamma_exposures' not in st.session_state:
    st.session_state.gamma_exposures = None
if 'walls' not in st.session_state:
    st.session_state.walls = None
if 'market_metrics' not in st.session_state:
    st.session_state.market_metrics = None
if 'current_price' not in st.session_state:
    st.session_state.current_price = 4500.0

# Ensure current_price is within reasonable bounds
if st.session_state.current_price < 10.0:
    st.session_state.current_price = 4500.0
elif st.session_state.current_price > 15000.0:
    st.session_state.current_price = 4500.0

def render_sidebar():
    """Render sidebar with input controls"""
    st.sidebar.header("📊 Gamma Exposure Calculator")
    st.sidebar.markdown("---")
    
    # Current Price (flexible for different assets)
    st.sidebar.subheader("Market Data")
    current_price = st.sidebar.number_input(
        "Current Price",
        min_value=10.0,  # Allow for ETF prices like SPY
        max_value=15000.0,  # Allow for index prices like SPX
        value=st.session_state.current_price,
        step=0.01,
        help="Current underlying asset price (SPX, SPY, etc.)"
    )
    st.session_state.current_price = current_price
    
    # Risk-free rate
    risk_free_rate = st.sidebar.slider(
        "Risk-Free Rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=5.0,
        step=0.1,
        help="Risk-free interest rate for gamma calculations"
    ) / 100
    
    return current_price, risk_free_rate

def render_data_input_section():
    """Render data input section"""
    st.header("📁 Data Input")
    
    # Create tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["🌐 Yahoo Finance", "📤 Upload File", "🔧 Generate Sample Data"])
    
    with tab1:
        st.subheader("📈 Fetch Real Options Data")
        st.info("Download live options chain data from Yahoo Finance")
        
        # Initialize Yahoo Finance fetcher
        yf_fetcher = YFinanceOptionsFetcher()
        available_symbols = yf_fetcher.get_available_symbols()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Symbol selection method
            symbol_input_method = st.radio(
                "Symbol Selection",
                ["Popular Symbols", "Custom Ticker"],
                help="Choose from popular symbols or enter any ticker"
            )
            
            if symbol_input_method == "Popular Symbols":
                selected_symbol = st.selectbox(
                    "Select Symbol",
                    options=list(available_symbols.keys()),
                    index=1,  # Default to SPY
                    help="Choose from popular symbols with options"
                )
            else:
                selected_symbol = st.text_input(
                    "Enter Ticker Symbol",
                    value="AAPL",
                    help="Enter any valid ticker symbol (e.g., AAPL, TSLA, NVDA, AMD)"
                ).upper()
                
                # Validate custom symbol
                if selected_symbol:
                    with st.spinner(f"Validating {selected_symbol}..."):
                        if yf_fetcher.validate_symbol(selected_symbol):
                            st.success(f"✅ {selected_symbol} has options data available")
                        else:
                            st.error(f"❌ {selected_symbol} does not have options data or is invalid")
            
            # Get current price and update session state
            try:
                current_price = yf_fetcher.get_current_price(selected_symbol)
                # Ensure the price is within reasonable bounds before updating session state
                if 10.0 <= current_price <= 15000.0:
                    st.session_state.current_price = current_price
                    st.success(f"Current {selected_symbol} Price: ${current_price:.2f}")
                else:
                    st.warning(f"Fetched price ${current_price:.2f} is outside expected range. Using current session value.")
                    current_price = st.session_state.current_price
            except YFinanceFetchError as e:
                st.warning(f"Could not fetch current price: {str(e)}")
                current_price = st.session_state.current_price
        
        with col2:
            # Fetch expiration dates
            try:
                with st.spinner("Fetching available expiration dates..."):
                    expirations = yf_fetcher.get_expiration_dates(selected_symbol)
                
                expiration_option = st.radio(
                    "Expiration Selection",
                    ["Nearest expiration", "Specific expiration", "Multiple expirations"],
                    help="Choose how to select expiration dates"
                )
                
                selected_expiration = None
                include_all = False
                
                if expiration_option == "Specific expiration":
                    selected_expiration = st.selectbox(
                        "Select Expiration Date",
                        options=expirations[:10],  # Show first 10
                        help="Choose a specific expiration date"
                    )
                elif expiration_option == "Multiple expirations":
                    include_all = True
                    st.info("Will fetch data for the first 5 expiration dates")
                
            except YFinanceFetchError as e:
                st.error(f"Error fetching expiration dates: {str(e)}")
                expirations = []
                selected_expiration = None
                include_all = False
        
        # Fetch options data button
        if st.button("📊 Fetch Options Data", type="primary", disabled=not expirations):
            try:
                with st.spinner(f"Fetching options chain data for {selected_symbol}..."):
                    # Fetch options data
                    options_df = yf_fetcher.fetch_options_chain(
                        symbol=selected_symbol,
                        expiration_date=selected_expiration,
                        include_all_expirations=include_all
                    )
                    
                    # Convert to contracts
                    contracts = yf_fetcher.convert_to_contracts(options_df)
                
                if contracts:
                    # Store in session state
                    st.session_state.options_data = options_df
                    st.session_state.options_contracts = contracts
                    st.session_state.data_loaded = True
                    st.session_state.current_symbol = selected_symbol  # Store the symbol
                    
                    # Display summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Contracts", len(contracts))
                    with col2:
                        unique_strikes = len(set(c.strike for c in contracts))
                        st.metric("Unique Strikes", unique_strikes)
                    with col3:
                        total_oi = sum(c.open_interest for c in contracts)
                        st.metric("Total Open Interest", f"{total_oi:,}")
                    
                    st.success(f"✅ Successfully fetched {len(contracts)} option contracts from Yahoo Finance!")
                    
                    # Show data preview - strikes closest to spot price
                    with st.expander("📋 Data Preview (15 strikes closest to spot)"):
                        # Get unique strikes and find closest to current price
                        options_df_sorted = options_df.copy()
                        options_df_sorted['distance_from_spot'] = abs(options_df_sorted['strike'] - current_price)
                        
                        # Get 15 closest strikes
                        closest_strikes = options_df_sorted.nsmallest(15, 'distance_from_spot')['strike'].unique()
                        
                        # Filter dataframe to show only these strikes
                        preview_df = options_df_sorted[options_df_sorted['strike'].isin(closest_strikes)].copy()
                        preview_df = preview_df.sort_values(['strike', 'option_type'])
                        preview_df = preview_df.drop('distance_from_spot', axis=1)
                        
                        st.dataframe(preview_df, use_container_width=True)
                        st.caption(f"Showing options for 15 strikes closest to current price (${current_price:.2f})")
                else:
                    st.warning("No valid options data found.")
                    
            except YFinanceFetchError as e:
                st.error(f"❌ Yahoo Finance error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
        
        # # Show options summary
        # if st.button("ℹ️ Show Options Summary", type="secondary"):
        #     try:
        #         with st.spinner("Getting options summary..."):
        #             summary = yf_fetcher.get_options_summary(selected_symbol)
                
        #         st.subheader(f"📊 {summary['symbol']} Options Summary")
                
        #         col1, col2 = st.columns(2)
        #         with col1:
        #             st.write(f"**Company:** {summary['company_name']}")
        #             st.write(f"**Current Price:** ${summary['current_price']:.2f}")
        #             st.write(f"**Available Expirations:** {summary['available_expirations']}")
                
        #         with col2:
        #             sample_stats = summary['sample_expiration_stats']
        #             st.write(f"**Sample Expiration Stats:**")
        #             st.write(f"- Calls: {sample_stats['total_calls']}")
        #             st.write(f"- Puts: {sample_stats['total_puts']}")
        #             st.write(f"- Strike Range: {sample_stats['strike_range']['min']:.0f} - {sample_stats['strike_range']['max']:.0f}")
                
        #         if summary['expiration_dates']:
        #             st.write("**Next 10 Expiration Dates:**")
        #             for i, exp_date in enumerate(summary['expiration_dates'][:10], 1):
        #                 st.write(f"{i}. {exp_date}")
                        
        #     except YFinanceFetchError as e:
        #         st.error(f"❌ Error getting summary: {str(e)}")
    
    with tab2:
        st.subheader("Upload Options Chain Data")
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=['csv', 'xlsx', 'xls'],
            help="Upload options chain data with columns: strike, expiry_date, option_type, open_interest"
        )
        
        if uploaded_file is not None:
            try:
                processor = OptionsDataProcessor()
                
                # Load and validate data
                with st.spinner("Loading and validating data..."):
                    df = processor.load_options_data(uploaded_file)
                    contracts = processor.convert_to_contracts(df)
                
                # Display data summary
                summary = processor.get_data_summary(df)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Contracts", summary['total_contracts'])
                with col2:
                    st.metric("Unique Strikes", summary['unique_strikes'])
                with col3:
                    st.metric("Total Open Interest", f"{summary['total_open_interest']:,}")
                
                # Show validation warnings if any
                if summary.get('validation_errors'):
                    st.warning("Data validation warnings:")
                    for error in summary['validation_errors']:
                        st.write(f"• {error}")
                
                # Store in session state
                st.session_state.options_data = df
                st.session_state.options_contracts = contracts
                st.session_state.data_loaded = True
                
                st.success(f"✅ Successfully loaded {len(contracts)} option contracts!")
                
                # Show data preview - strikes closest to spot price
                with st.expander("📋 Data Preview (15 strikes closest to spot)"):
                    # Get current price from sidebar
                    current_price = st.session_state.current_price
                    
                    # Get unique strikes and find closest to current price
                    df_sorted = df.copy()
                    df_sorted['distance_from_spot'] = abs(df_sorted['strike'] - current_price)
                    
                    # Get 15 closest strikes
                    closest_strikes = df_sorted.nsmallest(15, 'distance_from_spot')['strike'].unique()
                    
                    # Filter dataframe to show only these strikes
                    preview_df = df_sorted[df_sorted['strike'].isin(closest_strikes)].copy()
                    preview_df = preview_df.sort_values(['strike', 'option_type'])
                    preview_df = preview_df.drop('distance_from_spot', axis=1)
                    
                    st.dataframe(preview_df, use_container_width=True)
                    st.caption(f"Showing options for 15 strikes closest to current price (${current_price:.2f})")
                
            except DataValidationError as e:
                st.error(f"❌ Data validation error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
    
    with tab3:
        st.subheader("Generate Sample Data")
        st.info("Generate synthetic options data for testing and demonstration")
        
        col1, col2 = st.columns(2)
        with col1:
            num_strikes = st.slider("Number of Strikes", 5, 50, 20)
            days_to_expiry = st.slider("Days to Expiry", 1, 365, 30)
        
        with col2:
            spot_price = st.number_input("Spot Price for Sample", 
                                       min_value=10.0,  # Allow for lower prices like SPY (~$687)
                                       max_value=15000.0,  # Allow for higher prices like SPX (~$4500)
                                       value=st.session_state.current_price,
                                       step=1.0,
                                       help="Spot price for generating sample options data")
        
        if st.button("🎲 Generate Sample Data", type="primary"):
            try:
                processor = OptionsDataProcessor()
                
                with st.spinner("Generating sample data..."):
                    df = processor.create_sample_data(
                        spot_price=spot_price,
                        num_strikes=num_strikes,
                        days_to_expiry=days_to_expiry
                    )
                    contracts = processor.convert_to_contracts(df)
                
                # Store in session state
                st.session_state.options_data = df
                st.session_state.options_contracts = contracts
                st.session_state.data_loaded = True
                
                st.success(f"✅ Generated {len(contracts)} sample option contracts!")
                
                # Show data preview - strikes closest to spot price
                with st.expander("📋 Sample Data Preview (15 strikes closest to spot)"):
                    # Get unique strikes and find closest to spot price
                    df_sorted = df.copy()
                    df_sorted['distance_from_spot'] = abs(df_sorted['strike'] - spot_price)
                    
                    # Get 15 closest strikes
                    closest_strikes = df_sorted.nsmallest(15, 'distance_from_spot')['strike'].unique()
                    
                    # Filter dataframe to show only these strikes
                    preview_df = df_sorted[df_sorted['strike'].isin(closest_strikes)].copy()
                    preview_df = preview_df.sort_values(['strike', 'option_type'])
                    preview_df = preview_df.drop('distance_from_spot', axis=1)
                    
                    st.dataframe(preview_df, use_container_width=True)
                    st.caption(f"Showing options for 15 strikes closest to spot price (${spot_price:.2f})")
                
            except Exception as e:
                st.error(f"❌ Error generating sample data: {str(e)}")

def render_analysis_section(current_price: float, risk_free_rate: float):
    """Render analysis section with calculations and results"""
    if not st.session_state.data_loaded:
        st.info("👆 Please load options data first to see analysis results.")
        return
    
    st.header("📈 Gamma Exposure Analysis")
    
    try:
        # Initialize calculators
        gamma_calc = GammaCalculator(risk_free_rate=risk_free_rate)
        wall_analyzer = WallAnalyzer()
        metrics_calc = MetricsCalculator()
        viz_engine = VisualizationEngine()
        
        # Calculate gamma exposures
        with st.spinner("Calculating gamma exposures..."):
            gamma_exposures = gamma_calc.aggregate_by_strike(
                st.session_state.options_contracts, 
                current_price
            )
            st.session_state.gamma_exposures = gamma_exposures
        
        if not gamma_exposures:
            st.warning("No gamma exposure data calculated. Please check your input data.")
            return
        
        # Calculate walls
        with st.spinner("Analyzing gamma walls..."):
            walls = wall_analyzer.find_all_walls(gamma_exposures, current_price)
            st.session_state.walls = walls
        
        # Calculate metrics
        with st.spinner("Computing market metrics..."):
            market_metrics = metrics_calc.calculate_all_metrics(gamma_exposures)
            metrics_summary = metrics_calc.get_metrics_summary(gamma_exposures, current_price)
            gamma_environment = metrics_calc.calculate_gamma_environment(gamma_exposures, current_price)
            st.session_state.market_metrics = market_metrics
            st.session_state.metrics_summary = metrics_summary
            st.session_state.gamma_environment = gamma_environment
        
        # Display gamma environment
        st.subheader("🌊 Gamma Environment")
        gamma_env = st.session_state.gamma_environment
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Environment type with color coding
            env_type = gamma_env['environment'].title()
            if gamma_env['environment'] == 'positive':
                st.success(f"📈 {env_type} Gamma Environment")
            elif gamma_env['environment'] == 'negative':
                st.error(f"📉 {env_type} Gamma Environment")
            else:
                st.info(f"⚖️ {env_type} Gamma Environment")
        
        with col2:
            strength_info = gamma_env['strength_interpretation']
            st.metric(
                "Environment Strength",
                f"{strength_info['color']} {strength_info['level']}",
                delta=f"Raw: {gamma_env['environment_strength']:.4f}",
                help=f"Strength Level: {strength_info['level']} | Volatility Impact: {strength_info['volatility_impact']}"
            )
        
        with col3:
            if gamma_env['gamma_flip_level']:
                flip_distance = gamma_env['gamma_flip_level'] - current_price
                flip_distance_pct = (flip_distance / current_price) * 100
                
                st.metric(
                    "Gamma Flip Level",
                    f"{gamma_env['gamma_flip_level']:.0f}",
                    delta=f"{flip_distance:+.0f} ({flip_distance_pct:+.1f}%)",
                    help="Price level where gamma environment changes"
                )
            else:
                st.metric("Gamma Flip Level", "N/A", help="No clear gamma flip level identified")
        
        # Environment description and details
        st.info(gamma_env['description'])
        
        # Environment Strength detailed explanation
        st.subheader("💪 Environment Strength Analysis")
        strength_info = gamma_env['strength_interpretation']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Strength Assessment:**")
            st.write(f"{strength_info['color']} **{strength_info['level']}** ({gamma_env['environment_strength']:.4f})")
            st.write(f"📊 **Volatility Impact**: {strength_info['volatility_impact']}")
            st.write(f"📝 {strength_info['description']}")
            
            st.write("**How It's Calculated:**")
            st.write("```")
            st.write("Strength = |Total Net Gamma| / (Current Price × Total Open Interest)")
            st.write("```")
            st.write("This normalizes gamma exposure by market size and price level")
        
        with col2:
            st.write("**Strength Scale Interpretation:**")
            st.write("🔴 **Very Strong (≥0.10)**: Dominant market maker forces")
            st.write("🟠 **Strong (0.05-0.10)**: Significant gamma impact")
            st.write("🟡 **Moderate (0.02-0.05)**: Noticeable influence")
            st.write("🟢 **Weak (0.01-0.02)**: Limited impact")
            st.write("⚪ **Very Weak (<0.01)**: Minimal influence")
            
            st.write("**Trading Implications:**")
            if strength_info['level'] in ['Very Strong', 'Strong']:
                st.write("• 🎯 **High confidence** in gamma effects")
                st.write("• 📈 **Strong** support/resistance at walls")
                st.write("• ⚡ **Significant** volatility changes expected")
            elif strength_info['level'] == 'Moderate':
                st.write("• 🎯 **Moderate confidence** in gamma effects")
                st.write("• 📊 **Noticeable** but not dominant influence")
                st.write("• 🔄 **Some** volatility impact expected")
            else:
                st.write("• ⚠️ **Low confidence** in gamma effects")
                st.write("• 📉 **Minimal** market maker influence")
                st.write("• 🎲 **Other factors** likely more important")
        
        # Gamma flip level interpretation
        if gamma_env['gamma_flip_level']:
            flip_level = gamma_env['gamma_flip_level']
            flip_distance = flip_level - current_price
            
            st.subheader("🎯 Gamma Flip Level Analysis")
            
            if gamma_env['environment'] == 'positive' and flip_distance > 0:
                st.success(f"**Upside Breakout Scenario** (Current: ${current_price:.0f} → Flip: ${flip_level:.0f})")
                st.write("**Current Situation:**")
                st.write("• 🛡️ You're in the **protective zone** of positive gamma")
                st.write("• 📉 Market makers will **buy dips** and provide support")
                st.write("• 🔄 **Mean-reverting** price action expected")
                
                st.write("**If Price Rises Above Flip Level:**")
                st.write(f"• ⚡ Environment flips to **negative gamma** above ${flip_level:.0f}")
                st.write("• 🚀 Market makers become **momentum amplifiers**")
                st.write("• 📈 **Breakout acceleration** potential")
                st.write("• 🌪️ **Higher volatility** environment")
                
            elif gamma_env['environment'] == 'positive' and flip_distance < 0:
                st.warning(f"**Downside Risk Scenario** (Current: ${current_price:.0f} → Flip: ${flip_level:.0f})")
                st.write("**Current Situation:**")
                st.write("• 🛡️ Still in **positive gamma** territory")
                st.write("• 📈 Market makers provide **upward support**")
                
                st.write("**If Price Falls Below Flip Level:**")
                st.write(f"• ⚡ Environment becomes **negative gamma** below ${flip_level:.0f}")
                st.write("• 📉 Market makers would **amplify downward moves**")
                st.write("• 💥 **Breakdown acceleration** risk")
                
            elif gamma_env['environment'] == 'negative' and flip_distance > 0:
                st.error(f"**Resistance Above** (Current: ${current_price:.0f} → Flip: ${flip_level:.0f})")
                st.write("**Current Situation:**")
                st.write("• ⚡ You're in **negative gamma** territory")
                st.write("• 📈 Market makers **amplify moves** upward")
                
                st.write("**If Price Rises Above Flip Level:**")
                st.write(f"• 🛡️ Environment becomes **positive gamma** above ${flip_level:.0f}")
                st.write("• 🔄 Market makers would provide **stabilization**")
                st.write("• 📊 **Lower volatility** expected")
                
            elif gamma_env['environment'] == 'negative' and flip_distance < 0:
                st.error(f"**Support Below** (Current: ${current_price:.0f} → Flip: ${flip_level:.0f})")
                st.write("**Current Situation:**")
                st.write("• ⚡ You're in **negative gamma** territory")
                st.write("• 📉 Market makers **amplify moves** downward")
                
                st.write("**If Price Falls Below Flip Level:**")
                st.write(f"• 🛡️ Environment becomes **positive gamma** below ${flip_level:.0f}")
                st.write("• 🔄 Market makers would provide **support**")
                st.write("• 📊 **Stabilization** expected")
        
        # Strike distribution
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Strike Distribution:**")
            st.write(f"• Positive Gamma Strikes: {gamma_env['positive_strikes']} ({gamma_env['positive_strike_percentage']:.1f}%)")
            st.write(f"• Negative Gamma Strikes: {gamma_env['negative_strikes']} ({gamma_env['negative_strike_percentage']:.1f}%)")
            st.write(f"• Neutral Strikes: {gamma_env['neutral_strikes']}")
        
        with col2:
            # Environment implications
            st.write("**Market Implications:**")
            if gamma_env['environment'] == 'positive':
                st.write("• 🛡️ Market makers provide **stabilizing** force")
                st.write("• 📉 **Buy dips**, sell rallies")
                st.write("• 🔄 **Lower volatility** environment")
                st.write("• 💪 **Support** at key levels")
            elif gamma_env['environment'] == 'negative':
                st.write("• ⚡ Market makers **amplify** moves")
                st.write("• 📈 **Sell dips**, buy rallies")
                st.write("• 🌪️ **Higher volatility** environment")
                st.write("• 💥 **Momentum** acceleration")
            else:
                st.write("• ⚖️ **Balanced** gamma exposure")
                st.write("• 🎯 **Mixed** market maker flows")
                st.write("• 📊 **Moderate** volatility expected")

        # Display key metrics
        st.subheader("🎯 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Net Gamma",
                f"{market_metrics.total_net_gamma:,.0f}",
                help="Total net gamma exposure across all strikes"
            )
        
        with col2:
            st.metric(
                "Weighted Avg Strike",
                f"{market_metrics.gamma_weighted_avg_strike:.0f}",
                help="Gamma-weighted average strike price"
            )
        
        with col3:
            st.metric(
                "Call/Put Ratio",
                f"{market_metrics.call_put_gamma_ratio:.2f}",
                help="Ratio of call to put gamma exposure"
            )
        
        with col4:
            total_walls = len(walls['call_walls']) + len(walls['put_walls'])
            st.metric(
                "Total Walls",
                total_walls,
                help="Number of identified gamma walls"
            )
        
        # Expected Move Section
        st.subheader("📏 Expected Move (Based on Implied Volatility)")
        
        # Calculate average IV from options data
        if st.session_state.options_contracts:
            import math
            from datetime import datetime
            
            # Find ATM (At-The-Money) IV for more accurate expected move
            # ATM options have strikes closest to current price
            contracts_with_distance = []
            for c in st.session_state.options_contracts:
                distance = abs(c.strike - current_price)
                contracts_with_distance.append((c, distance))
            
            # Sort by distance from current price
            contracts_with_distance.sort(key=lambda x: x[1])
            
            # Use ATM IV (average of closest 10 contracts, or all if less than 10)
            atm_contracts = [c for c, _ in contracts_with_distance[:min(10, len(contracts_with_distance))]]
            avg_iv = sum(c.implied_volatility for c in atm_contracts) / len(atm_contracts)
            
            # Also calculate overall average for comparison
            overall_avg_iv = sum(c.implied_volatility for c in st.session_state.options_contracts) / len(st.session_state.options_contracts)
            
            # Calculate days to expiry for each contract
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days_to_expiry_list = []
            for c in st.session_state.options_contracts:
                expiry = c.expiry_date if isinstance(c.expiry_date, datetime) else datetime.fromisoformat(str(c.expiry_date))
                # Normalize expiry to midnight if it has time component
                expiry = expiry.replace(hour=0, minute=0, second=0, microsecond=0)
                dte = max(1, (expiry - today).days)
                days_to_expiry_list.append(dte)
            
            # Get average days to expiry
            avg_dte = sum(days_to_expiry_list) / len(days_to_expiry_list)
            
            # Calculate expected move
            time_factor = math.sqrt(avg_dte / 365)
            expected_move_1sd = current_price * avg_iv * time_factor
            expected_move_2sd = expected_move_1sd * 2
            
            move_pct_1sd = (expected_move_1sd / current_price) * 100
            move_pct_2sd = (expected_move_2sd / current_price) * 100
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**1 Standard Deviation (~68% probability)**")
                st.write(f"**Expected Move:** ±${expected_move_1sd:.2f} (±{move_pct_1sd:.2f}%)")
                st.write(f"**Upper Bound:** ${current_price + expected_move_1sd:.2f}")
                st.write(f"**Lower Bound:** ${current_price - expected_move_1sd:.2f}")
                st.caption(f"Based on {avg_iv*100:.1f}% ATM IV and {avg_dte:.0f} days to expiry")
            
            with col2:
                st.warning(f"**2 Standard Deviations (~95% probability)**")
                st.write(f"**Expected Move:** ±${expected_move_2sd:.2f} (±{move_pct_2sd:.2f}%)")
                st.write(f"**Upper Bound:** ${current_price + expected_move_2sd:.2f}")
                st.write(f"**Lower Bound:** ${current_price - expected_move_2sd:.2f}")
                st.caption("Larger moves beyond this range are less likely")
            
            # Trading implications
            with st.expander("💡 Trading Implications & IV Details"):
                # Show IV comparison
                st.write("**Implied Volatility Analysis:**")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("ATM IV (used)", f"{avg_iv*100:.2f}%", help="IV of options closest to current price")
                with col_b:
                    st.metric("Overall Avg IV", f"{overall_avg_iv*100:.2f}%", help="Average IV across all strikes")
                
                st.markdown("---")
                st.write("**Strategy Suggestions Based on Expected Move:**")
                st.write(f"- **Iron Condor:** Sell strikes outside 1SD range (${current_price - expected_move_1sd:.0f} - ${current_price + expected_move_1sd:.0f})")
                st.write(f"- **Covered Calls:** Consider strikes near upper 1SD (~${current_price + expected_move_1sd:.0f})")
                st.write(f"- **Cash-Secured Puts:** Consider strikes near lower 1SD (~${current_price - expected_move_1sd:.0f})")
                st.write(f"- **Long Straddle/Strangle:** Profitable if move exceeds ${expected_move_1sd:.2f}")
                
                if avg_iv > 0.40:
                    st.error(f"🔴 **HIGH IV ({avg_iv*100:.1f}%)** - Large expected move. Premium selling may be attractive.")
                elif avg_iv > 0.25:
                    st.info(f"🟡 **MODERATE IV ({avg_iv*100:.1f}%)** - Normal expected move. Balanced strategies recommended.")
                else:
                    st.success(f"🟢 **LOW IV ({avg_iv*100:.1f}%)** - Small expected move. Buying options may be attractive.")
        
        # Display walls information
        if walls['call_walls'] or walls['put_walls']:
            st.subheader("🧱 Gamma Walls")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if walls['call_walls']:
                    st.write("**Call Walls (Resistance)**")
                    for wall in walls['call_walls'][:3]:  # Show top 3
                        distance_pct = (wall.distance_from_spot / current_price) * 100
                        st.write(f"#{wall.significance_rank}: {wall.strike:.0f} "
                               f"({distance_pct:+.1f}%) - {wall.exposure_value:,.0f}")
            
            with col2:
                if walls['put_walls']:
                    st.write("**Put Walls (Support)**")
                    for wall in walls['put_walls'][:3]:  # Show top 3
                        distance_pct = (wall.distance_from_spot / current_price) * 100
                        st.write(f"#{wall.significance_rank}: {wall.strike:.0f} "
                               f"({distance_pct:+.1f}%) - {wall.exposure_value:,.0f}")
        
        # Create and display charts
        st.subheader("📊 Visualizations")
        
        # Chart selection
        chart_type = st.selectbox(
            "Select Chart Type",
            ["Comprehensive Analysis", "Net Gamma Exposure", "Call vs Put Breakdown", "Metrics Summary"],
            help="Choose the type of chart to display"
        )
        
        try:
            if chart_type == "Comprehensive Analysis":
                symbol = st.session_state.get('current_symbol', 'Options')
                fig = viz_engine.create_comprehensive_chart(
                    gamma_exposures, walls, current_price,
                    f"{symbol} Gamma Exposure with Walls"
                )
            elif chart_type == "Net Gamma Exposure":
                fig = viz_engine.create_gamma_exposure_chart(
                    gamma_exposures, current_price,
                    "Net Gamma Exposure by Strike"
                )
            elif chart_type == "Call vs Put Breakdown":
                fig = viz_engine.create_call_put_breakdown_chart(
                    gamma_exposures, current_price,
                    "Call vs Put Gamma Exposure"
                )
            elif chart_type == "Metrics Summary":
                fig = viz_engine.create_metrics_summary_chart(
                    metrics_summary,
                    "Gamma Exposure Metrics Dashboard"
                )
            
            st.plotly_chart(fig, width='stretch')
            
            # Store chart for export
            st.session_state.current_chart = fig
            
        except VisualizationError as e:
            st.error(f"❌ Visualization error: {str(e)}")
        
    except (GammaCalculationError, WallAnalysisError, MetricsCalculationError) as e:
        st.error(f"❌ Calculation error: {str(e)}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")

def render_strategy_recommendations(current_price: float):
    """Render options strategy recommendations based on gamma environment"""
    if not st.session_state.data_loaded or not hasattr(st.session_state, 'gamma_environment'):
        return
    
    gamma_env = st.session_state.gamma_environment
    walls = st.session_state.walls
    strength_info = gamma_env['strength_interpretation']
    
    st.header("💡 Options Strategy Recommendations")
    st.markdown("Tailored strategy suggestions based on current gamma environment and market conditions")
    
    # Environment-based strategy overview
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if gamma_env['environment'] == 'positive':
            st.success("🛡️ **POSITIVE GAMMA ENVIRONMENT**")
            st.markdown("**Market Characteristics:**")
            st.markdown("- Mean-reverting price action")
            st.markdown("- Lower volatility expected")
            st.markdown("- Strong support/resistance at walls")
            st.markdown("- Market makers provide stability")
        elif gamma_env['environment'] == 'negative':
            st.error("⚡ **NEGATIVE GAMMA ENVIRONMENT**")
            st.markdown("**Market Characteristics:**")
            st.markdown("- Trending/momentum price action")
            st.markdown("- Higher volatility expected")
            st.markdown("- Breakout/breakdown potential")
            st.markdown("- Market makers amplify moves")
        else:
            st.info("⚖️ **NEUTRAL GAMMA ENVIRONMENT**")
            st.markdown("**Market Characteristics:**")
            st.markdown("- Mixed price action")
            st.markdown("- Moderate volatility")
            st.markdown("- Balanced market forces")
            st.markdown("- Standard trading conditions")
    
    with col2:
        st.markdown(f"**Environment Strength:** {strength_info['color']} {strength_info['level']}")
        st.markdown(f"**Confidence Level:** {'High' if strength_info['level'] in ['Very Strong', 'Strong'] else 'Moderate' if strength_info['level'] == 'Moderate' else 'Low'}")
        st.markdown(f"**Volatility Impact:** {strength_info['volatility_impact']}")
        
        if gamma_env['gamma_flip_level']:
            flip_distance = gamma_env['gamma_flip_level'] - current_price
            flip_distance_pct = (flip_distance / current_price) * 100
            st.markdown(f"**Gamma Flip Level:** {gamma_env['gamma_flip_level']:.0f} ({flip_distance_pct:+.1f}%)")
    
    st.markdown("---")
    
    # Strategy recommendations based on environment
    if gamma_env['environment'] == 'positive':
        render_positive_gamma_strategies(current_price, gamma_env, walls, strength_info)
    elif gamma_env['environment'] == 'negative':
        render_negative_gamma_strategies(current_price, gamma_env, walls, strength_info)
    else:
        render_neutral_gamma_strategies(current_price, gamma_env, walls, strength_info)

def render_positive_gamma_strategies(current_price: float, gamma_env: dict, walls: dict, strength_info: dict):
    """Render strategy recommendations for positive gamma environment"""
    
    st.subheader("📊 Recommended Strategies for Positive Gamma")
    
    # Create tabs for different strategy categories
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Premium Selling", "📉 Mean Reversion", "🛡️ Hedging", "⚠️ Avoid"])
    
    with tab1:
        st.markdown("### Premium Selling Strategies")
        st.success("**EXCELLENT ENVIRONMENT** for premium collection strategies")
        
        # Covered Calls
        with st.expander("📈 **Covered Calls** - ⭐⭐⭐⭐⭐ HIGHLY RECOMMENDED", expanded=True):
            st.markdown("**Strategy:** Sell call options against long stock position")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Why It Works:**")
                st.markdown("- Mean-reverting environment limits upside")
                st.markdown("- Lower volatility increases time decay")
                st.markdown("- Call walls provide natural resistance")
                st.markdown("- High probability of calls expiring worthless")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                if strength_info['level'] in ['Very Strong', 'Strong']:
                    st.success("**Risk:** LOW | **Reward:** MODERATE-HIGH")
                    st.markdown("- Strike Selection: 1-3% OTM (aggressive)")
                else:
                    st.info("**Risk:** MODERATE | **Reward:** MODERATE")
                    st.markdown("- Strike Selection: 2-5% OTM (standard)")
            
            # Show specific strikes if call walls exist
            call_walls = walls.get('call_walls', [])
            if call_walls:
                st.markdown("**🎯 Suggested Strikes (based on call walls):**")
                for i, wall in enumerate(call_walls[:3], 1):
                    distance_pct = ((wall.strike - current_price) / current_price) * 100
                    if 0 < distance_pct <= 5:
                        st.markdown(f"- **{wall.strike:.0f}** ({distance_pct:+.1f}%) - Strong resistance at this level")
        
        # Cash-Secured Puts
        with st.expander("💰 **Cash-Secured Puts** - ⭐⭐⭐⭐ RECOMMENDED"):
            st.markdown("**Strategy:** Sell put options with cash reserved to buy stock if assigned")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Why It Works:**")
                st.markdown("- Put walls provide strong support")
                st.markdown("- Mean reversion protects downside")
                st.markdown("- Good entry strategy for long positions")
                st.markdown("- Collect premium while waiting to buy")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                st.info("**Risk:** MODERATE | **Reward:** MODERATE")
                st.markdown("- Strike Selection: At or slightly below put walls")
                st.markdown("- Best for stocks you want to own")
            
            put_walls = walls.get('put_walls', [])
            if put_walls:
                st.markdown("**🎯 Suggested Strikes (based on put walls):**")
                for i, wall in enumerate(put_walls[:3], 1):
                    distance_pct = ((wall.strike - current_price) / current_price) * 100
                    if -5 <= distance_pct < 0:
                        st.markdown(f"- **{wall.strike:.0f}** ({distance_pct:+.1f}%) - Strong support at this level")
        
        # Iron Condors
        with st.expander("🦅 **Iron Condors** - ⭐⭐⭐⭐ RECOMMENDED"):
            st.markdown("**Strategy:** Sell OTM call spread + OTM put spread")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Why It Works:**")
                st.markdown("- Range-bound price action expected")
                st.markdown("- Profit from time decay on both sides")
                st.markdown("- Walls define natural boundaries")
                st.markdown("- Lower volatility helps all legs")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                st.info("**Risk:** MODERATE | **Reward:** MODERATE")
                st.markdown("- Width: Based on wall locations")
                st.markdown("- Best with 30-45 DTE")
                st.markdown("- Target: 50-70% max profit")
    
    with tab2:
        st.markdown("### Mean Reversion Strategies")
        st.success("**FAVORABLE ENVIRONMENT** for buying dips and selling rallies")
        
        with st.expander("📉 **Buy Dips (Long Stock/Calls)** - ⭐⭐⭐⭐"):
            st.markdown("**Strategy:** Buy on pullbacks to support levels")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Why It Works:**")
                st.markdown("- Market makers buy dips (support)")
                st.markdown("- Put walls act as strong support")
                st.markdown("- Mean reversion to center expected")
                st.markdown("- Lower risk entries at support")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                st.success("**Risk:** LOW-MODERATE | **Reward:** MODERATE")
                st.markdown("- Entry: Near put walls")
                st.markdown("- Stop: Below major put wall")
                st.markdown("- Target: Call walls or flip level")
        
        with st.expander("📈 **Sell Rallies (Short Calls/Stock)** - ⭐⭐⭐"):
            st.markdown("**Strategy:** Sell or take profits at resistance")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Why It Works:**")
                st.markdown("- Market makers sell rallies (resistance)")
                st.markdown("- Call walls act as strong resistance")
                st.markdown("- Mean reversion back down expected")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                st.info("**Risk:** MODERATE | **Reward:** MODERATE")
                st.markdown("- Entry: Near call walls")
                st.markdown("- Stop: Above major call wall")
                st.markdown("- Target: Put walls or center")
    
    with tab3:
        st.markdown("### Hedging Strategies")
        st.info("**OPTIONAL** - Lower urgency in stable environment")
        
        with st.expander("🛡️ **Protective Puts** - ⭐⭐⭐"):
            st.markdown("**Strategy:** Buy puts to protect long positions")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Considerations:**")
                st.markdown("- Less urgent in positive gamma")
                st.markdown("- Lower volatility = cheaper puts")
                st.markdown("- Good time to buy protection")
                st.markdown("- Consider longer-dated options")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                st.info("**Cost:** LOW | **Protection:** HIGH")
                st.markdown("- Strike: At or below put walls")
                st.markdown("- Expiration: 60-90 DTE")
                st.markdown("- Cost-effective insurance")
    
    with tab4:
        st.markdown("### Strategies to Avoid")
        st.error("**NOT RECOMMENDED** in positive gamma environment")
        
        with st.expander("❌ **Long Volatility Plays** - ⭐ AVOID"):
            st.markdown("**Why Avoid:**")
            st.markdown("- Volatility likely to decrease")
            st.markdown("- Long straddles/strangles will lose value")
            st.markdown("- Vega works against you")
            st.markdown("- Time decay accelerates in low vol")
        
        with st.expander("❌ **Momentum/Breakout Trades** - ⭐ AVOID"):
            st.markdown("**Why Avoid:**")
            st.markdown("- Mean reversion fights momentum")
            st.markdown("- Breakouts likely to fail at walls")
            st.markdown("- Market makers provide resistance")
            st.markdown("- Better to fade moves than chase them")

def render_negative_gamma_strategies(current_price: float, gamma_env: dict, walls: dict, strength_info: dict):
    """Render strategy recommendations for negative gamma environment"""
    
    st.subheader("⚡ Recommended Strategies for Negative Gamma")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Momentum", "🌪️ Volatility", "🛡️ Protection", "⚠️ Avoid"])
    
    with tab1:
        st.markdown("### Momentum Strategies")
        st.success("**EXCELLENT ENVIRONMENT** for trend following")
        
        with st.expander("🚀 **Breakout Trading** - ⭐⭐⭐⭐⭐ HIGHLY RECOMMENDED", expanded=True):
            st.markdown("**Strategy:** Buy breakouts above resistance or sell breakdowns below support")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Why It Works:**")
                st.markdown("- Market makers amplify moves")
                st.markdown("- Momentum accelerates on breaks")
                st.markdown("- Trending environment expected")
                st.markdown("- Follow the flow, don't fight it")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                if strength_info['level'] in ['Very Strong', 'Strong']:
                    st.success("**Risk:** MODERATE | **Reward:** HIGH")
                    st.markdown("- Entry: On breakout confirmation")
                else:
                    st.info("**Risk:** MODERATE-HIGH | **Reward:** MODERATE-HIGH")
                    st.markdown("- Entry: Wait for confirmation")
            
            if gamma_env['gamma_flip_level']:
                flip_level = gamma_env['gamma_flip_level']
                flip_distance = flip_level - current_price
                st.markdown(f"**🎯 Key Level to Watch: {flip_level:.0f}**")
                if flip_distance > 0:
                    st.markdown(f"- Breakout above {flip_level:.0f} could accelerate upward momentum")
                else:
                    st.markdown(f"- Breakdown below {flip_level:.0f} could accelerate downward momentum")
        
        with st.expander("📊 **Directional Options** - ⭐⭐⭐⭐ RECOMMENDED"):
            st.markdown("**Strategy:** Buy calls (bullish) or puts (bearish) to capture directional moves")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Why It Works:**")
                st.markdown("- Large moves more likely")
                st.markdown("- Volatility expansion helps")
                st.markdown("- Leverage momentum with options")
                st.markdown("- Defined risk with unlimited upside")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                st.success("**Risk:** LIMITED (premium paid) | **Reward:** HIGH")
                st.markdown("- Strike: ATM or slightly ITM")
                st.markdown("- Expiration: 30-60 DTE")
                st.markdown("- Size appropriately for volatility")
    
    with tab2:
        st.markdown("### Volatility Strategies")
        st.success("**FAVORABLE ENVIRONMENT** for volatility expansion")
        
        with st.expander("🌪️ **Long Straddles/Strangles** - ⭐⭐⭐⭐ RECOMMENDED"):
            st.markdown("**Strategy:** Buy ATM call + ATM put (straddle) or OTM versions (strangle)")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Why It Works:**")
                st.markdown("- Volatility likely to increase")
                st.markdown("- Large moves expected")
                st.markdown("- Profit from move in either direction")
                st.markdown("- Vega works in your favor")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                st.info("**Risk:** MODERATE (premium paid) | **Reward:** HIGH")
                st.markdown("- Best before major moves")
                st.markdown("- Need significant move to profit")
                st.markdown("- Consider IV levels before entry")
        
        with st.expander("📈 **Calendar Spreads (Reverse)** - ⭐⭐⭐"):
            st.markdown("**Strategy:** Sell longer-dated, buy shorter-dated options")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Why It Works:**")
                st.markdown("- Profit from near-term vol expansion")
                st.markdown("- Short-term gamma increases faster")
                st.markdown("- Defined risk strategy")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                st.info("**Risk:** LIMITED | **Reward:** MODERATE")
                st.markdown("- Best with upcoming catalysts")
                st.markdown("- Advanced strategy")
    
    with tab3:
        st.markdown("### Protection Strategies")
        st.error("**CRITICAL** - High priority for risk management")
        
        with st.expander("🛡️ **Protective Puts** - ⭐⭐⭐⭐⭐ ESSENTIAL", expanded=True):
            st.markdown("**Strategy:** Buy puts to protect long positions")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Why It's Critical:**")
                st.markdown("- High risk of sharp moves")
                st.markdown("- Downside can accelerate quickly")
                st.markdown("- Insurance is expensive but necessary")
                st.markdown("- Protect against gap risk")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                st.error("**Cost:** HIGH | **Protection:** ESSENTIAL")
                st.markdown("- Strike: 5-10% OTM")
                st.markdown("- Expiration: Match your time horizon")
                st.markdown("- Consider this mandatory insurance")
        
        with st.expander("⚠️ **Tight Stop Losses** - ⭐⭐⭐⭐⭐ ESSENTIAL"):
            st.markdown("**Strategy:** Use tighter stops than normal")
            
            st.markdown("**Why It's Critical:**")
            st.markdown("- Moves can accelerate quickly")
            st.markdown("- Market makers amplify momentum")
            st.markdown("- Small losses can become large fast")
            st.markdown("- Reduce position sizes accordingly")
    
    with tab4:
        st.markdown("### Strategies to Avoid")
        st.error("**HIGH RISK** in negative gamma environment")
        
        with st.expander("❌ **Covered Calls** - ⭐ AVOID OR USE DEFENSIVELY"):
            st.markdown("**Why Risky:**")
            st.markdown("- High assignment risk in momentum environment")
            st.markdown("- Upside can accelerate quickly")
            st.markdown("- Miss out on large moves")
            st.markdown("- If used: Sell far OTM (7-10%) or shorter duration")
        
        with st.expander("❌ **Short Premium Strategies** - ⭐ AVOID"):
            st.markdown("**Why Risky:**")
            st.markdown("- Volatility expansion works against you")
            st.markdown("- Large moves can cause max loss")
            st.markdown("- Iron condors/credit spreads dangerous")
            st.markdown("- Unlimited risk in some strategies")
        
        with st.expander("❌ **Mean Reversion Trades** - ⭐ AVOID"):
            st.markdown("**Why Risky:**")
            st.markdown("- Trends can persist longer than expected")
            st.markdown("- Fading momentum is dangerous")
            st.markdown("- 'Catching falling knives' mentality")
            st.markdown("- Wait for environment to change")

def render_neutral_gamma_strategies(current_price: float, gamma_env: dict, walls: dict, strength_info: dict):
    """Render strategy recommendations for neutral gamma environment"""
    
    st.subheader("⚖️ Recommended Strategies for Neutral Gamma")
    
    st.info("**BALANCED APPROACH** - Use standard options strategies with normal risk management")
    
    tab1, tab2 = st.tabs(["📊 Balanced Strategies", "⚠️ Risk Management"])
    
    with tab1:
        st.markdown("### Balanced Strategy Approach")
        
        with st.expander("🎯 **Diversified Options Portfolio** - ⭐⭐⭐⭐ RECOMMENDED", expanded=True):
            st.markdown("**Strategy:** Mix of different strategy types")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**✅ Recommended Mix:**")
                st.markdown("- 40% Premium selling (covered calls, CSPs)")
                st.markdown("- 30% Directional (calls/puts)")
                st.markdown("- 20% Spreads (verticals, iron condors)")
                st.markdown("- 10% Protection (hedges)")
            
            with col2:
                st.markdown("**📊 Risk/Reward:**")
                st.info("**Risk:** MODERATE | **Reward:** MODERATE")
                st.markdown("- Diversification reduces risk")
                st.markdown("- Adapt as environment changes")
                st.markdown("- Monitor gamma shifts closely")
        
        with st.expander("📈 **Standard Covered Calls** - ⭐⭐⭐"):
            st.markdown("**Strategy:** Moderate approach to premium collection")
            st.markdown("- Strike Selection: 3-5% OTM")
            st.markdown("- Risk: Moderate assignment risk")
            st.markdown("- Reward: Moderate premium collection")
        
        with st.expander("🦅 **Iron Condors (Wider)** - ⭐⭐⭐"):
            st.markdown("**Strategy:** Wider wings for safety")
            st.markdown("- Width: Wider than in positive gamma")
            st.markdown("- Risk: Moderate")
            st.markdown("- Reward: Lower but safer")
    
    with tab2:
        st.markdown("### Risk Management Focus")
        
        st.warning("**Key Principle:** Stay flexible and monitor for environment changes")
        
        with st.expander("⚠️ **Monitor Gamma Shifts**"):
            st.markdown("**Critical Actions:**")
            st.markdown("- Watch for environment changes daily")
            st.markdown("- Adjust strategies as gamma shifts")
            st.markdown("- Be ready to pivot quickly")
            st.markdown("- Don't over-commit to any strategy")
        
        with st.expander("📊 **Position Sizing**"):
            st.markdown("**Guidelines:**")
            st.markdown("- Use smaller position sizes")
            st.markdown("- Maintain higher cash reserves")
            st.markdown("- Diversify across strategies")
            st.markdown("- Don't concentrate risk")
        
        if gamma_env['gamma_flip_level']:
            flip_level = gamma_env['gamma_flip_level']
            with st.expander("🎯 **Watch Flip Level**"):
                st.markdown(f"**Gamma Flip Level: {flip_level:.0f}**")
                st.markdown("- Environment could change at this level")
                st.markdown("- Prepare strategy adjustments")
                st.markdown("- Increase monitoring near this level")

def render_export_section():
    """Render export section"""
    # COMMENTED OUT - Export functionality disabled
    pass
    # if not st.session_state.data_loaded or not st.session_state.gamma_exposures:
    #     return
    # 
    # st.header("💾 Export Data")
    # 
    # try:
    #     export_manager = ExportManager()
    #     
    #     col1, col2, col3 = st.columns(3)
    #     
    #     with col1:
    #         st.subheader("📊 Data Export")
    #         
    #         # Export gamma exposures
    #         if st.button("📈 Download Gamma Data (CSV)", type="secondary"):
    #             csv_data = export_manager.export_gamma_exposures_to_csv(
    #                 st.session_state.gamma_exposures
    #             )
    #             st.download_button(
    #                 label="💾 Download CSV",
    #                 data=csv_data,
    #                 file_name=f"gamma_exposures_{export_manager.get_export_timestamp().replace(':', '-').replace(' ', '_')}.csv",
    #                 mime="text/csv"
    #             )
    #     
    #     with col2:
    #         st.subheader("🧱 Walls Export")
    #         
    #         if st.session_state.walls and st.button("🏗️ Download Walls (CSV)", type="secondary"):
    #             csv_data = export_manager.export_walls_to_csv(st.session_state.walls)
    #             st.download_button(
    #                 label="💾 Download CSV",
    #                 data=csv_data,
    #                 file_name=f"walls_{export_manager.get_export_timestamp().replace(':', '-').replace(' ', '_')}.csv",
    #                 mime="text/csv"
    #             )
    #     
    #     with col3:
    #         st.subheader("📊 Chart Export")
    #         
    #         if hasattr(st.session_state, 'current_chart') and st.button("🖼️ Download Chart (PNG)", type="secondary"):
    #             try:
    #                 # Note: PNG export requires kaleido package
    #                 st.info("Chart export feature requires additional setup. Use browser's save image option for now.")
    #             except Exception as e:
    #                 st.error(f"Chart export error: {str(e)}")
    #     
    #     # Comprehensive export
    #     st.subheader("📦 Complete Package")
    #     if st.button("📦 Download Complete Analysis Package", type="primary"):
    #         st.info("Complete package export would include all data, metrics, and charts. Feature in development.")
    # 
    # except ExportError as e:
    #     st.error(f"❌ Export error: {str(e)}")

def main():
    """Main application function"""
    st.title("📊 Gamma Exposure Calculator")
    st.markdown("Calculate and visualize gamma exposure metrics for options trading")
    
    # Render sidebar
    current_price, risk_free_rate = render_sidebar()
    
    # Main content
    render_data_input_section()
    
    st.markdown("---")
    
    render_analysis_section(current_price, risk_free_rate)
    
    st.markdown("---")
    
    # Strategy recommendations section
    render_strategy_recommendations(current_price)
    
    # Export section commented out
    # st.markdown("---")
    # render_export_section()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Gamma Exposure Calculator** | "
        "Built with Streamlit | "
        f"Current Price: ${current_price:,.2f}"
    )

if __name__ == "__main__":
    main()
