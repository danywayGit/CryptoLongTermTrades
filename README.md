# ETH Long-Term Trading Strategy

Automated trading signal analysis for Ethereum (ETH) using technical indicators across Daily and Weekly timeframes.

## Quick Start

1. **Setup Environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Run Analysis**
   ```bash
   python analysis_eth.py
   ```

## Project Structure

### Core Scripts
- **`analysis_eth.py`** - Main analysis script (Daily + Weekly signals)
- **`verify_signals.py`** - Validates generated signals against constraints
- **`calculate_stats.py`** - Detailed performance metrics and cycle analysis

### Optimization & Research
- **`optimize_daily_eth.py`** - Parameter optimization (grid search)
- **`strategy_optimization.py`** - Alternative portfolio simulation approach
- **`inspect_data.py`** - Data inspection utility

### Documentation
- **`walkthrough.md`** - Strategy methodology and results
- **`implementation_plan.md`** - Technical implementation details
- **`task.md`** - Project task checklist
- **`copilot.instruction.md`** - AI assistant guidelines

### Data
- **`data/`** - CSV files with OHLCV + indicators

## Strategy Overview

### Daily Timeframe (Optimized)
- **Buys**: RSI < 35 + Stoch Bull Cross + Price < EMA200
- **Sells**: Multiple conditions including "Naked" extreme sells for major tops
- **Performance**: ~1900% compounded return, 100% win rate (7 cycles)

### Weekly Timeframe
- **Buys**: Stoch(18) < 9 + Price < EMA200 + RSI < 35
- **Sells**: Stoch(18) > 82 + RSI > 78 + Price > 80% above EMA200

## Key Features
- ✅ Strict EMA200 filter (no buys above 200 EMA)
- ✅ Date-based exclusions for known "bad buy" zones
- ✅ 25% minimum profit constraint
- ✅ 20-day minimum spacing between sells
- ✅ "Naked" extreme sell signals (visualize tops without position)

## Results
- **82 Daily Buy Signals** (deep value accumulation)
- **26 Daily Sell Signals** (including major 2021/2024 tops)
- **4 Weekly Buy Signals** (high conviction bottoms)
- **6 Weekly Sell Signals** (extreme tops)

See `walkthrough.md` for detailed results and analysis.
