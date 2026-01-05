"""Configuration constants for Gamma Exposure Calculator"""

# Option contract specifications
SPX_CONTRACT_MULTIPLIER = 100
DEFAULT_RISK_FREE_RATE = 0.05
DEFAULT_VOLATILITY = 0.20

# Chart configuration
CHART_HEIGHT = 600
CHART_WIDTH = 1000
CALL_WALL_COLOR = '#FF6B6B'
PUT_WALL_COLOR = '#4ECDC4'
CURRENT_PRICE_COLOR = '#FFE66D'

# File upload limits
MAX_FILE_SIZE_MB = 50
SUPPORTED_FILE_TYPES = ['csv', 'xlsx', 'xls']

# Calculation parameters
MIN_TIME_TO_EXPIRY = 1/365.25  # 1 day minimum (accounts for leap years)
MAX_TIME_TO_EXPIRY = 5.0       # 5 years maximum
MIN_VOLATILITY = 0.01       # 1% minimum
MAX_VOLATILITY = 2.0        # 200% maximum