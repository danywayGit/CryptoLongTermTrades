import pandas as pd
import numpy as np
import os
import itertools
from analysis_eth import load_and_clean_data, DAILY_FILE

def run_backtest(df, params):
    """
    Runs a simplified backtest with specific parameters.
    Returns a dictionary of performance metrics.
    """
    rsi_buy_thresh = params['rsi_buy']
    rsi_sell_thresh = params['rsi_sell']
    ema_ext_sell_thresh = params['ema_ext_sell']
    min_profit_pct = params['min_profit']
    
    # Copy relevant columns to avoid affecting original df
    # We assume indicators (RSI, Stoch, EMA) are already calculated in df
    
    # Logic Re-implementation for Speed (Vectorized where possible, but loop is needed for state)
    # To keep it consistent with analysis_eth.py, we'll use a similar loop structure
    
    signals = []
    active_buys = []
    closed_trades = []
    
    # State Trackers
    rsi_oversold_bar = -999
    stoch_bull_bar = -999
    
    rsi_strong_overbought_bar = -999
    stoch_bear_bar_strong = -999
    rsi_weak_overbought_bar = -999
    stoch_bear_bar_weak = -999
    
    # Pre-calculate boolean series for speed
    stoch_bull_cross = df['Stoch_Bull_Cross'].values
    stoch_bear_cross = df['Stoch_Bear_Cross'].values
    below_ema200 = df['Below_EMA200'].values
    below_ema21 = df['Below_EMA21'].values
    rsi_vals = df['RSI'].values
    close_vals = df['close'].values
    ema_ext_vals = df['EMA_Ext_Pct'].values
    dates = df.index
    
    # Date Exclusion Filters (Indices)
    # We can pre-calculate valid dates mask if needed, but simple check inside loop is fine
    
    for i in range(len(df)):
        rsi = rsi_vals[i]
        close = close_vals[i]
        ema_ext = ema_ext_vals[i]
        date = dates[i]
        d_str = str(date.date())
        
        # --- BUY LOGIC ---
        is_buy = False
        
        # 1. RSI Oversold
        if rsi < rsi_buy_thresh:
            rsi_oversold_bar = i
            
        # 2. Stoch Bull Cross
        if stoch_bull_cross[i]:
            if (i - rsi_oversold_bar) <= 20:
                stoch_bull_bar = i
                
        # 3. EMA Confirmation (Price > EMA21 not strictly required for "Deep Value" in this optimized version? 
        #    Actually analysis_eth.py requires Price > EMA21 for confirmation. Let's stick to that.)
        #    Wait, analysis_eth.py uses `Above_EMA21` for confirmation.
        #    Let's simplify: Buy if Setup + Price < EMA200.
        
        # Check Buy Setup (Stoch Bull Cross recently after RSI Oversold)
        # In analysis_eth.py: if df['Above_EMA21'].iloc[i] and (i - stoch_bull_bar) <= 20...
        # Let's test a slightly looser version: Just the Cross + Price < EMA200
        
        if stoch_bull_cross[i] and (i - rsi_oversold_bar) <= 20:
             # Strict EMA200 Filter
             if below_ema200[i]:
                 # Date Exclusion
                 if not (('2021-11-24' <= d_str <= '2021-12-30') or ('2024-12-24' <= d_str <= '2025-01-20')):
                     is_buy = True
        
        if is_buy:
            # Debounce (5 days)
            if not signals or (i - signals[-1]['idx'] > 5):
                signals.append({'type': 'Buy', 'price': close, 'date': date, 'idx': i})
                active_buys.append(close)
                
        # --- SELL LOGIC ---
        is_sell = False
        is_extreme_sell = False
        
        # Track RSI
        if rsi > rsi_sell_thresh: rsi_strong_overbought_bar = i
        if rsi > 70: rsi_extreme_bar = i # For naked sell
        
        # Condition A: Strong Sell
        if stoch_bear_cross[i]:
            if (i - rsi_strong_overbought_bar) <= 10 and ema_ext > 50.0:
                is_sell = True
                
        # Condition C: Extreme Sell (Naked)
        if ema_ext > ema_ext_sell_thresh:
            if (i - rsi_extreme_bar) <= 10 and stoch_bear_cross[i]:
                is_sell = True
                is_extreme_sell = True
                
        if is_sell:
            can_sell = True
            # Profit Constraint
            if active_buys:
                avg_buy = sum(active_buys) / len(active_buys)
                if close < (avg_buy * (1 + min_profit_pct)):
                    can_sell = False
            elif not is_extreme_sell:
                can_sell = False
                
            if can_sell:
                # Debounce (20 days for sells)
                last_sell_idx = -999
                for s in reversed(signals):
                    if s['type'] == 'Sell':
                        last_sell_idx = s['idx']
                        break
                
                if (i - last_sell_idx) > 20:
                    signals.append({'type': 'Sell', 'price': close, 'date': date, 'idx': i})
                    
                    # Close positions
                    if active_buys:
                        avg_buy = sum(active_buys) / len(active_buys)
                        profit_pct = (close - avg_buy) / avg_buy
                        closed_trades.append(profit_pct)
                        active_buys = []

    # Metrics
    num_buys = len([s for s in signals if s['type'] == 'Buy'])
    num_sells = len([s for s in signals if s['type'] == 'Sell'])
    avg_profit = np.mean(closed_trades) if closed_trades else 0.0
    total_return = sum(closed_trades) # Simple sum of percentages (approximate compounding)
    win_rate = len([p for p in closed_trades if p > 0]) / len(closed_trades) if closed_trades else 0.0
    
    return {
        'params': params,
        'num_buys': num_buys,
        'num_sells': num_sells,
        'avg_profit': avg_profit,
        'total_return': total_return,
        'win_rate': win_rate
    }

def optimize():
    print("Loading Data...")
    df = load_and_clean_data(DAILY_FILE)
    if df is None: return

    # --- Pre-calculate Indicators needed for optimization ---
    # Helper for Stoch Cross
    df['Stoch_Bull_Cross'] = (df['%K'] > df['%D']) & (df['%K'].shift(1) <= df['%D'].shift(1))
    df['Stoch_Bear_Cross'] = (df['%K'] < df['%D']) & (df['%K'].shift(1) >= df['%D'].shift(1))
    
    # Helper for EMA Cross
    df['Above_EMA21'] = df['close'] > df['EMA21']
    df['Below_EMA21'] = df['close'] < df['EMA21']
    df['Below_EMA200'] = df['close'] < df['EMA200']
    
    # EMA Extension
    df['EMA_Ext_Pct'] = (df['close'] - df['EMA200']) / df['EMA200'] * 100
    # -------------------------------------------------------

    # Define Parameter Grid
    param_grid = {
        'rsi_buy': [30, 35, 40, 45],
        'rsi_sell': [70, 75, 80],
        'ema_ext_sell': [40, 45, 50, 60],
        'min_profit': [0.15, 0.20, 0.25, 0.30]
    }
    
    keys, values = zip(*param_grid.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    print(f"Testing {len(combinations)} combinations...")
    
    results = []
    for i, params in enumerate(combinations):
        if i % 50 == 0: print(f"Processing {i}/{len(combinations)}...")
        res = run_backtest(df, params)
        results.append(res)
        
    # Sort by Total Return
    results.sort(key=lambda x: x['total_return'], reverse=True)
    
    print("\n--- TOP 5 CONFIGURATIONS ---")
    for i in range(5):
        r = results[i]
        p = r['params']
        print(f"Rank {i+1}: Return {r['total_return']*100:.1f}% | WinRate {r['win_rate']*100:.1f}% | Buys {r['num_buys']} | Sells {r['num_sells']}")
        print(f"   Params: RSI Buy < {p['rsi_buy']}, RSI Sell > {p['rsi_sell']}, Ext > {p['ema_ext_sell']}%, Min Profit {p['min_profit']*100}%")

if __name__ == "__main__":
    optimize()
