import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DAILY_FILE = os.path.join(DATA_DIR, "CRYPTO_ETHUSD, 1D.csv")

def load_data(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return None
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('datetime', inplace=True)
    df.sort_index(inplace=True)
    return df

def run_strategy(df):
    # Calculate Indicators
    df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # Strategy Parameters
    initial_cash = 10000.0
    cash = initial_cash
    coins = 0.0
    
    buy_threshold_pct = 0.70 # Price < 70% of EMA200 (30% below)
    sell_threshold_pct = 1.40 # Price > 140% of EMA200 (40% above)
    min_profit_pct = 0.25 # 25% profit
    
    # Portfolio Rules
    cash_reserve_ratio = 0.30 # Keep 30% of cash when buying
    coin_retention_ratio = 0.25 # Keep 25% of coins when selling
    
    trades = []
    portfolio_history = []
    
    last_buy_price = 0.0
    last_sell_price = 0.0
    
    # We need a way to prevent buying every single day in the dip. 
    # Let's enforce a cooldown or "lower than last buy" rule.
    last_trade_idx = -999
    
    for i in range(len(df)):
        if i < 200: continue # Skip until EMA200 is valid
        
        price = df['close'].iloc[i]
        ema200 = df['EMA200'].iloc[i]
        date = df.index[i]
        
        # Portfolio Value
        portfolio_value = cash + (coins * price)
        portfolio_history.append({'date': date, 'value': portfolio_value, 'price': price})
        
        # BUY LOGIC
        # Rule: Price < EMA200 * 0.7
        if price < (ema200 * buy_threshold_pct):
            # Check if we have cash (and respect reserve)
            investable_cash = cash * (1 - cash_reserve_ratio)
            
            if investable_cash > 10: # Minimum trade size
                # Filter: Don't buy every day. 
                # Buy if we have no coins OR price is significantly lower than last buy (DCA)
                # OR if it's been a while (e.g. 30 days) and we are still in the zone.
                should_buy = False
                if coins == 0:
                    should_buy = True
                elif price < (last_buy_price * 0.90): # Buy if 10% lower (Aggressive DCA)
                     should_buy = True
                elif (i - last_trade_idx) > 30: # Buy every 30 days if condition persists (Accumulation)
                     should_buy = True
                
                if should_buy:
                    buy_amount = investable_cash / price
                    coins += buy_amount
                    cash -= investable_cash
                    last_buy_price = price
                    last_trade_idx = i
                    trades.append({
                        'date': date, 'type': 'BUY', 'price': price, 
                        'amount': buy_amount, 'value': investable_cash,
                        'reason': f'Price {price:.2f} < 0.7*EMA {ema200:.2f}'
                    })
                    print(f"[{date.date()}] BUY  @ {price:.2f} | EMA200: {ema200:.2f} | Invested: ${investable_cash:.2f}")

        # SELL LOGIC
        # Rule: Price > EMA200 * 1.4 AND Profit > 25%
        elif price > (ema200 * sell_threshold_pct):
            if coins > 0:
                # Check Profit Constraint
                if price > (last_buy_price * (1 + min_profit_pct)):
                    # Filter: Only sell if price is higher than last sell (to avoid selling out early)
                    should_sell = False
                    if last_sell_price == 0:
                        should_sell = True
                    elif price > (last_sell_price * 1.10): # Sell if 10% higher than last sell
                        should_sell = True
                    
                    # Reset last_sell_price if we are in a new cycle? 
                    # If price dropped below EMA200 since last sell?
                    # For now, simple "higher than last sell" is good for a single bull run.
                    # But if we had a bear market in between, last_sell_price might be from 4 years ago (high).
                    # So we should reset last_sell_price if we bought in between.
                    if len(trades) > 0 and trades[-1]['type'] == 'BUY':
                        last_sell_price = 0.0
                        should_sell = True
                        
                    if should_sell:
                        # Sell 10% of coins (Scaling out slowly)
                        sell_coins = coins * 0.10 
                        
                        # Ensure we don't go below 25% of "max coins ever held"? 
                        # That's hard to track. 
                        # User said "keep 25% of coins". 
                        # If we just sell 10% of *current*, we never reach 0.
                        # But we might get very small.
                        
                        if sell_coins > 0:
                            sell_value = sell_coins * price
                            cash += sell_value
                            coins -= sell_coins
                            last_sell_price = price
                            last_trade_idx = i
                            trades.append({
                                'date': date, 'type': 'SELL', 'price': price, 
                                'amount': sell_coins, 'value': sell_value,
                                'reason': f'Price {price:.2f} > 1.4*EMA {ema200:.2f} & Profit'
                            })
                            print(f"[{date.date()}] SELL @ {price:.2f} | EMA200: {ema200:.2f} | Sold: ${sell_value:.2f}")

    # Final Stats
    final_value = cash + (coins * df['close'].iloc[-1])
    print(f"\nInitial Value: ${initial_cash:.2f}")
    print(f"Final Value:   ${final_value:.2f}")
    print(f"Return:        {((final_value - initial_cash) / initial_cash) * 100:.2f}%")
    print(f"Total Trades:  {len(trades)}")
    
    print("\n--- Trade Log (First 5 and Last 5) ---")
    for t in trades[:5]:
        print(f"{t['date'].date()} {t['type']} @ {t['price']:.2f}")
    print("...")
    for t in trades[-5:]:
        print(f"{t['date'].date()} {t['type']} @ {t['price']:.2f}")
    
    # Plotting
    plt.figure(figsize=(12, 8))
    
    # Subplot 1: Price and EMA
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(df.index, df['close'], label='Price', color='black', alpha=0.6)
    ax1.plot(df.index, df['EMA200'], label='EMA200', color='blue', alpha=0.6)
    ax1.plot(df.index, df['EMA200'] * 0.7, label='Buy Zone (<70%)', color='green', linestyle='--', alpha=0.4)
    ax1.plot(df.index, df['EMA200'] * 1.4, label='Sell Zone (>140%)', color='red', linestyle='--', alpha=0.4)
    
    # Plot Trades
    buy_dates = [t['date'] for t in trades if t['type'] == 'BUY']
    buy_prices = [t['price'] for t in trades if t['type'] == 'BUY']
    sell_dates = [t['date'] for t in trades if t['type'] == 'SELL']
    sell_prices = [t['price'] for t in trades if t['type'] == 'SELL']
    
    ax1.scatter(buy_dates, buy_prices, marker='^', color='green', s=50, label='Buy', zorder=5)
    ax1.scatter(sell_dates, sell_prices, marker='v', color='red', s=50, label='Sell', zorder=5)
    
    ax1.set_yscale('log')
    ax1.set_title('ETH Long Term Strategy - Buy/Sell Points')
    ax1.legend()
    ax1.grid(True, which="both", ls="-", alpha=0.2)
    
    # Subplot 2: Portfolio Value
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    portfolio_df = pd.DataFrame(portfolio_history)
    ax2.plot(portfolio_df['date'], portfolio_df['value'], label='Portfolio Value', color='purple')
    ax2.set_title('Portfolio Value Over Time')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('strategy_results.png')
    print("Saved plot to strategy_results.png")

    return trades, pd.DataFrame(portfolio_history)

if __name__ == "__main__":
    df = load_data(DAILY_FILE)
    if df is not None:
        run_strategy(df)
