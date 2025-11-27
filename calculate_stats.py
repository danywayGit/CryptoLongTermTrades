import pandas as pd
import numpy as np
from analysis_eth import load_and_clean_data, detect_signals, DAILY_FILE

def calculate_detailed_stats():
    print("Loading Data...")
    df = load_and_clean_data(DAILY_FILE)
    if df is None: return

    print("Running Optimized Strategy...")
    # Run with optimized parameters: RSI Buy < 35, RSI Sell > 70
    # Note: detect_signals inside analysis_eth.py is ALREADY updated with these hardcoded optimized logic
    # so we just call it directly.
    df, signals = detect_signals(df, "Daily", rsi_buy_thresh=35, rsi_sell_thresh=70, min_profit_pct=0.25)
    
    # Process Trades
    trades = []
    active_buys = []
    
    # We need to simulate the PnL properly
    # analysis_eth.py logic: 
    # Buys accumulate. Sells close ALL active buys.
    
    equity_curve = []
    initial_capital = 10000
    cash = initial_capital
    coins = 0
    
    trade_log = []
    
    for s in signals:
        price = s['price']
        date = s['date']
        
        if s['type'] == 'Buy':
            # Invest fixed amount or remaining cash? 
            # Let's simulate: Buy 1 ETH for simplicity to track points, 
            # OR simulate full portfolio.
            # Let's simulate: Invest 10% of current equity per buy? 
            # Or just track % gain per trade cycle.
            
            # Simple Cycle Analysis:
            # A "Cycle" is defined as: Accumulating Buys -> Sell Event (Close All)
            pass
            
    # Let's look at "Round Trip" Trades
    # Since we accumulate, we can treat a Sell as closing the weighted average of all open buys.
    
    cycles = []
    current_cycle_buys = []
    
    for s in signals:
        if s['type'] == 'Buy':
            current_cycle_buys.append(s['price'])
        elif s['type'] == 'Sell':
            if current_cycle_buys:
                avg_entry = sum(current_cycle_buys) / len(current_cycle_buys)
                exit_price = s['price']
                profit_pct = (exit_price - avg_entry) / avg_entry
                
                cycles.append({
                    'entry_date': 'Various', # Simplified
                    'exit_date': s['date'],
                    'avg_entry': avg_entry,
                    'exit_price': exit_price,
                    'profit_pct': profit_pct,
                    'num_buys': len(current_cycle_buys)
                })
                current_cycle_buys = [] # Reset
            else:
                # Naked Sell (No position)
                pass

    # Calculate Stats
    if not cycles:
        print("No completed cycles found.")
        return

    profits = [c['profit_pct'] for c in cycles]
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p <= 0]
    
    win_rate = len(wins) / len(cycles) * 100
    avg_profit = np.mean(profits) * 100
    total_return = sum(profits) * 100 # Simple sum (approx)
    
    # Compound Return Simulation
    account = 10000
    for p in profits:
        account = account * (1 + p)
    compound_return = (account - 10000) / 10000 * 100
    
    print("\n--- DETAILED STRATEGY STATISTICS (DAILY) ---")
    print(f"Total Completed Trade Cycles: {len(cycles)}")
    print(f"Win Rate:                     {win_rate:.2f}%")
    print(f"Average Profit per Cycle:     {avg_profit:.2f}%")
    print(f"Best Cycle:                   {max(profits)*100:.2f}%")
    print(f"Worst Cycle:                  {min(profits)*100:.2f}%")
    print(f"Compounded Return (Simulated):{compound_return:.2f}%")
    print(f"Profit Factor:                {sum(wins) / abs(sum(losses)) if losses else 'Infinite'}")
    
    print("\n--- CYCLE LOG ---")
    for i, c in enumerate(cycles):
        print(f"Cycle {i+1}: Exit {c['exit_date'].date()} | Avg Entry ${c['avg_entry']:.0f} -> Exit ${c['exit_price']:.0f} | Profit: {c['profit_pct']*100:.2f}% ({c['num_buys']} buys)")

if __name__ == "__main__":
    calculate_detailed_stats()
