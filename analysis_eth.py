import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DAILY_FILE = os.path.join(DATA_DIR, "CRYPTO_ETHUSD, 1D.csv")
WEEKLY_FILE = os.path.join(DATA_DIR, "CRYPTO_ETHUSD, 1W.csv")

def calculate_indicators(df):
    """Calculates additional indicators needed for the strategy."""
    # EMA 100
    df['EMA100'] = df['close'].ewm(span=100, adjust=False).mean()
    
    # Stoch 18 (18, 3, 3) - We'll use %K(18)
    # %K = 100 * (C - L18) / (H18 - L18)
    low_18 = df['low'].rolling(window=18).min()
    high_18 = df['high'].rolling(window=18).max()
    df['Stoch_K_18'] = 100 * (df['close'] - low_18) / (high_18 - low_18)
    
    return df

def load_and_clean_data(filepath):
    """Loads CSV and converts time column."""
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return None
    
    df = pd.read_csv(filepath)
    # 'time' is likely unix timestamp based on exploration
    df['datetime'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('datetime', inplace=True)
    
    # Calculate additional indicators
    df = calculate_indicators(df)
    
    return df

def detect_signals(df, timeframe_name, rsi_buy_thresh=30, rsi_sell_thresh=70, min_profit_pct=0.0):
    """
    Detects Buy and Sell signals based on sequential logic with state tracking.
    """
    
    df = df.copy()
    df['Buy_Signal'] = False
    df['Sell_Signal'] = False
    
    # Helper for Stoch Cross
    df['Stoch_Bull_Cross'] = (df['%K'] > df['%D']) & (df['%K'].shift(1) <= df['%D'].shift(1))
    df['Stoch_Bear_Cross'] = (df['%K'] < df['%D']) & (df['%K'].shift(1) >= df['%D'].shift(1))
    
    # Helper for EMA Cross
    df['Above_EMA21'] = df['close'] > df['EMA21']
    df['Below_EMA21'] = df['close'] < df['EMA21']
    df['Below_EMA200'] = df['close'] < df['EMA200']
    
    # EMA Extension
    df['EMA_Ext_Pct'] = (df['close'] - df['EMA200']) / df['EMA200'] * 100

    # State Trackers
    rsi_oversold_bar = -999
    ema_ext_at_oversold = 0.0 # Track Ext at the low
    stoch_bull_bar = -999
    
    # Sell State Trackers
    rsi_strong_overbought_bar = -999 # RSI > 80
    rsi_weak_overbought_bar = -999   # RSI > 65
    
    stoch_bear_bar_strong = -999
    stoch_bear_bar_weak = -999
    
    signals = []
    active_buys = [] 

    for i in range(len(df)):
        # Current values
        rsi = df['RSI'].iloc[i]
        close_price = df['close'].iloc[i]
        ema_ext = df['EMA_Ext_Pct'].iloc[i]
        idx = df.index[i]
        
        is_buy_setup = False
        
        # --- BUY LOGIC ---
        if timeframe_name == "Weekly":
            # User Request: Stoch(18) < 9, Price < EMA200 (or EMA100), RSI < 35
            
            # 1. Check EMA Condition (EMA200 preferred, else EMA100)
            ema_ref = df['EMA200'].iloc[i]
            if pd.isna(ema_ref):
                ema_ref = df['EMA100'].iloc[i]
            
            if close_price < ema_ref:
                # 2. Check Stoch(18) < 9
                if df['Stoch_K_18'].iloc[i] < 9:
                    # 3. Check RSI < 35
                    if rsi < 35:
                        is_buy_setup = True
                        
        else: # Daily Logic (Existing)
            # 1. RSI Oversold
            if rsi < 35: # Optimized from 40 to 35
                rsi_oversold_bar = i
                ema_ext_at_oversold = ema_ext # Capture Ext at the dip
                
            # 2. Stoch Bull Cross
            if df['Stoch_Bull_Cross'].iloc[i]:
                if (i - rsi_oversold_bar) <= 20: 
                    stoch_bull_bar = i
            
            # 3. EMA Confirmation + Filters
            # OPTIMIZATION: Removed 'Above_EMA21' check to buy earlier in the dip.
            # Was: if df['Above_EMA21'].iloc[i]:
            if (i - stoch_bull_bar) <= 20 and stoch_bull_bar != -999:
                is_buy_setup = True
            
            # Apply Filters (Daily Only)
            if is_buy_setup and timeframe_name == "Daily":
                # 1. Date Exclusion (User Specified Bad Zones)
                d_str = str(idx.date())
                if ('2021-11-24' <= d_str <= '2021-12-30') or \
                   ('2024-12-24' <= d_str <= '2025-01-20'):
                    is_buy_setup = False
                
                # 2. Technical Filters
                if is_buy_setup:
                    # Condition A: Deep Value (Price < EMA200)
                    if not df['Below_EMA200'].iloc[i]:
                        is_buy_setup = False # Invalid - Strict EMA200 filter requested
                
        if is_buy_setup:
            # Debounce
            if not signals or (i - signals[-1]['index_loc'] > 5):
                 df.at[idx, 'Buy_Signal'] = True
                 signals.append({'type': 'Buy', 'price': close_price, 'date': idx, 'index_loc': i})
                 active_buys.append(close_price)
                 stoch_bull_bar = -999 

        # --- SELL LOGIC ---
        sell_candidate = False
        is_extreme_sell = False
        
        if timeframe_name == "Weekly":
            # User Request: Stoch(18) > 82, RSI > 78, Price > 80% above EMA200 (or > 120% above EMA100)
            
            # 1. Check Stoch(18) > 82
            if df['Stoch_K_18'].iloc[i] > 82:
                # 2. Check RSI > 78
                if rsi > 78:
                    # 3. Check EMA Extension
                    ema200 = df['EMA200'].iloc[i]
                    ema100 = df['EMA100'].iloc[i]
                    
                    is_ext_valid = False
                    if not pd.isna(ema200):
                        if close_price > (ema200 * 1.80): # At least 80% above EMA200
                            is_ext_valid = True
                    elif not pd.isna(ema100):
                        if close_price > (ema100 * 2.20): # At least 120% above EMA100
                            is_ext_valid = True
                            
                    if is_ext_valid:
                        sell_candidate = True
                        is_extreme_sell = True # Allow naked sell for Weekly tops
                        
        else: # Daily Logic
            # Condition A: Strong Sell (RSI > 80 + Stoch Bear Cross)
            if rsi > rsi_sell_thresh:
                rsi_strong_overbought_bar = i
                
            if df['Stoch_Bear_Cross'].iloc[i]:
                stoch_bear_bar_strong = i
            
            # Check for Strong Sell Setup (Stoch Cross within 10 bars of RSI > 80)
            if (i - rsi_strong_overbought_bar) <= 10:
                if df['Stoch_Bear_Cross'].iloc[i]:
                     # REQUIRE EMA Extension > 50% for Strong Sell to avoid early exits
                     if ema_ext > 50.0:
                         sell_candidate = True

            # Condition B: Weak Sell (RSI > 65 + Stoch Bear Cross + Price < EMA21)
            if rsi > 65:
                rsi_weak_overbought_bar = i
                
            if df['Stoch_Bear_Cross'].iloc[i]:
                stoch_bear_bar_weak = i
                
            if df['Below_EMA21'].iloc[i]:
                if (i - stoch_bear_bar_weak) <= 20 and stoch_bear_bar_weak != -999:
                    sell_candidate = True
                    
            # Condition C: Extreme Extension (Blow-off Top) - "Catch tops of 2021 and 2024"
            # Track RSI > 70 for this specific condition
            if rsi > 70: rsi_strong_overbought_bar = i
            
            if ema_ext > 45.0:
                 # Check if we had Extreme RSI recently (within 10 days) AND Stoch Bear Cross NOW
                 if (i - rsi_strong_overbought_bar) <= 10:
                     if df['Stoch_Bear_Cross'].iloc[i]: 
                         sell_candidate = True
                         is_extreme_sell = True

        if sell_candidate:
            # CHECK PROFIT CONSTRAINT (Only if we have a position)
            can_sell = True
            if active_buys:
                if min_profit_pct > 0:
                    avg_buy_price = sum(active_buys) / len(active_buys)
                    if close_price < (avg_buy_price * (1 + min_profit_pct)):
                        can_sell = False
            elif not is_extreme_sell:
                # If no position and NOT an extreme sell, we can't sell.
                can_sell = False

            if can_sell:
                # Debounce - "sells must be space by 20 days minimum"
                last_sell_idx = -999
                for s in reversed(signals):
                    if s['type'] == 'Sell':
                        last_sell_idx = s['index_loc']
                        break
                
                if (i - last_sell_idx) > 20:
                    df.at[idx, 'Sell_Signal'] = True
                    signals.append({'type': 'Sell', 'price': close_price, 'date': idx, 'index_loc': i})
                    
                    active_buys = [] 
                    stoch_bear_bar_weak = -999

    print(f"Detected {len([s for s in signals if s['type']=='Buy'])} Buy and {len([s for s in signals if s['type']=='Sell'])} Sell signals for {timeframe_name}")
    return df, signals

def plot_results(df, signals, timeframe_name):
    """Plots price with signals and indicators."""
    plt.figure(figsize=(16, 10))
    
    # Price Chart
    ax1 = plt.subplot(3, 1, 1)
    ax1.plot(df.index, df['close'], label='Price', color='black', alpha=0.6)
    ax1.plot(df.index, df['EMA21'], label='EMA21', color='orange', alpha=0.5)
    ax1.plot(df.index, df['EMA200'], label='EMA200', color='blue', alpha=0.5) 
    
    # Plot Buy Signals
    buys = df[df['Buy_Signal']]
    if not buys.empty:
        ax1.scatter(buys.index, buys['close'], marker='^', color='green', s=100, label='Buy Signal', zorder=5)
    
    # Plot Sell Signals
    sells = df[df['Sell_Signal']]
    if not sells.empty:
        ax1.scatter(sells.index, sells['close'], marker='v', color='red', s=100, label='Sell Signal', zorder=5)
    
    ax1.set_title(f'ETH/USD {timeframe_name} - Buy/Sell Signals')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # RSI Chart
    ax2 = plt.subplot(3, 1, 2, sharex=ax1)
    ax2.plot(df.index, df['RSI'], color='purple', label='RSI')
    ax2.axhline(70, color='red', linestyle='--', alpha=0.5)
    ax2.axhline(60, color='gray', linestyle=':', alpha=0.5) 
    ax2.axhline(30, color='green', linestyle='--', alpha=0.5)
    ax2.set_ylabel('RSI')
    ax2.grid(True, alpha=0.3)
    
    # Stochastic Chart
    ax3 = plt.subplot(3, 1, 3, sharex=ax1)
    ax3.plot(df.index, df['%K'], label='%K', color='blue', linewidth=1)
    ax3.plot(df.index, df['%D'], label='%D', color='orange', linewidth=1)
    ax3.axhline(80, color='red', linestyle='--', alpha=0.5)
    ax3.axhline(20, color='green', linestyle='--', alpha=0.5)
    ax3.set_ylabel('Stochastic')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'eth_signals_{timeframe_name}.png')
    print(f"Saved plot to eth_signals_{timeframe_name}.png")

def main():
    # 1. Daily Analysis
    print("Analyzing Daily Data...")
    df_daily = load_and_clean_data(DAILY_FILE)
    if df_daily is not None:
        df_daily, signals_daily = detect_signals(
            df_daily, 
            "Daily", 
            rsi_buy_thresh=40, 
            rsi_sell_thresh=70, 
            min_profit_pct=0.25 # Reverted to 25%
        )
        plot_results(df_daily, signals_daily, "Daily")
        
    # 2. Weekly Analysis
    print("\nAnalyzing Weekly Data...")
    df_weekly = load_and_clean_data(WEEKLY_FILE)
    if df_weekly is not None:
        df_weekly, signals_weekly = detect_signals(
            df_weekly, 
            "Weekly", 
            rsi_buy_thresh=40, 
            rsi_sell_thresh=75, 
            min_profit_pct=0.25
        )
        plot_results(df_weekly, signals_weekly, "Weekly")

if __name__ == "__main__":
    main()
