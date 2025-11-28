# Implementation Plan - ETH Long-Term Trading Signal Analysis

## Goal Description
Analyze ETH/USD Daily and Weekly data to identify optimal buy (market bottom) and sell (market top) signal combinations using technical indicators. The focus is on sequential patterns suitable for long-term swing/position trading.

## User Review Required
- **Indicators**: Confirm if specific parameters for RSI, Stochastic, etc., are preferred (defaulting to standard 14-period, etc., if not specified).
- **BBWP**: Bollinger Band Width Percentile might need custom implementation as it's less standard in basic libraries.
- **Definition of "Optimal"**: Will define "optimal" based on capturing major price swings (profitability and drawdown).

## Proposed Changes

### Analysis Scripts
#### [NEW] [analysis_eth.py](file:///C:/Users/danyw/Documents/Git/DanywayGit/CryptoLongTermTrades/analysis_eth.py)
- **Libraries**: `pandas`, `pandas_ta` (if available, else manual calculation), `matplotlib` for plotting.
- **Functionality**:
    1.  Load CSV data.
    2.  Clean and preprocess (handle dates, numeric conversions).
    3.  **Data Preprocessing**:
        -   Load CSV data.
        -   Convert `time` to datetime.
        -   Verify pre-calculated columns: `RSI`, `%K`, `%D`, `BBWP`, `EMA21`, `EMA55`, `EMA200`.
    4.  **Signal Logic Implementation**:
        -   Develop a `SignalDetector` class to evaluate sequential conditions.
        -   **Entry Logic (Buy)**:
            -   Primary: RSI < 30 (Oversold).
            -   Confirmation: Stochastic Bullish Cross (within N bars of RSI oversold).
            -   Trigger: Price closes above EMA21 (or specific reversal candle).
            -   Filter: BBWP > Threshold (High volatility exhaustion) or < Threshold (Squeeze breakout).
        -   **Exit Logic (Sell)**:
            -   Primary: RSI > 70 (Overbought).
            -   Confirmation: Stochastic Bearish Cross.
            -   Trigger: Price closes below EMA21.
    5.  **Backtesting/Scanning**:
        -   Run the logic over the entire dataset.
        -   Calculate "Forward Returns" (e.g., 30-day, 90-day return after signal) to quantify quality.
        -   Compare signals against `Extreme Lo` / `Extreme Hi` columns if they represent ground truth pivots.
    6.  **Visualization**:
        -   Plot Price with Buy/Sell markers.
        -   Overlay EMAs.
        -   Subplots for RSI, Stoch, BBWP to show conditions at signal time.

## Verification Plan
### Automated Tests
- Run the script and check for output charts and text summary.
- Verify that signals align with historical major bottoms (e.g., 2018 bottom, 2020 crash, 2022 bottom) and tops (2017 peak, 2021 peaks).

### Manual Verification
- Inspect generated plots to ensure signals make visual sense.
- Review the logic of the "sequential" detection to ensure it respects the "within N candles" constraint.
