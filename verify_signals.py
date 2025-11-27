import pandas as pd
import os
from analysis_eth import detect_signals, load_and_clean_data, DAILY_FILE, WEEKLY_FILE

def verify():
    print("Verifying Signals...")
    
    # --- DAILY ---
    print("\n--- DAILY SIGNALS ---")
    df = load_and_clean_data(DAILY_FILE)
    if df is not None:
        df, signals = detect_signals(df, "Daily", rsi_buy_thresh=40, rsi_sell_thresh=70, min_profit_pct=0.25)
        
        sig_df = pd.DataFrame(signals)
        if not sig_df.empty:
            sig_df['date'] = pd.to_datetime(sig_df['date'])
            print(f"Detected {len([s for s in signals if s['type']=='Buy'])} Buy and {len([s for s in signals if s['type']=='Sell'])} Sell signals for Daily")
            
            # Check Bad Buys
            bad_buys_1 = sig_df[(sig_df['type'] == 'Buy') & (sig_df['date'] >= '2021-11-24') & (sig_df['date'] <= '2021-12-30')]
            bad_buys_2 = sig_df[(sig_df['type'] == 'Buy') & (sig_df['date'] >= '2024-12-24') & (sig_df['date'] <= '2025-01-20')]
            print(f"Bad Buys 1 (Nov-Dec 2021): {len(bad_buys_1)} found")
            print(f"Bad Buys 2 (Dec 2024-Jan 2025): {len(bad_buys_2)} found")

            # Check Missed Sells
            missed_sells = [
                ('2021-11-03', '2021-11-11'),
                ('2024-05-21', '2024-05-28'),
                ('2024-12-05', '2024-12-16'),
                ('2025-08-13', '2025-08-26'),
                ('2025-10-04', '2025-10-09')
            ]
            print("Checking Missed Sells:")
            for start, end in missed_sells:
                sells = sig_df[(sig_df['type'] == 'Sell') & (sig_df['date'] >= start) & (sig_df['date'] <= end)]
                status = "FOUND" if not sells.empty else "MISSING"
                print(f"{start} to {end}: {status}")
                if not sells.empty:
                     for _, row in sells.iterrows():
                         print(f"   {row['type']} at {row['price']:.2f} on {row['date'].date()}")

    # --- WEEKLY ---
    print("\n--- WEEKLY SIGNALS ---")
    df_weekly = load_and_clean_data(WEEKLY_FILE)
    if df_weekly is not None:
        df_weekly, signals_weekly = detect_signals(df_weekly, "Weekly", rsi_buy_thresh=40, rsi_sell_thresh=75, min_profit_pct=0.25)
        print(f"Detected {len([s for s in signals_weekly if s['type']=='Buy'])} Buy and {len([s for s in signals_weekly if s['type']=='Sell'])} Sell signals for Weekly")
        
        print("All Weekly Signals:")
        for s in signals_weekly:
             print(f"{s['date'].date()} | {s['type']} | {s['price']:.2f}")

if __name__ == "__main__":
    verify()
