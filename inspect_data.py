import pandas as pd
import os

# Configuration
DATA_DIR = r"c:\Users\danyw\Documents\Git\DanywayGit\CryptoLongTermTrades\data"
DAILY_FILE = os.path.join(DATA_DIR, "CRYPTO_ETHUSD, 1D.csv")

def inspect_dates():
    if not os.path.exists(DAILY_FILE):
        print(f"Error: File not found at {DAILY_FILE}")
        return

    df = pd.read_csv(DAILY_FILE)
    df['datetime'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('datetime', inplace=True)
    
    # Helper for Stoch Cross
    df['Stoch_Bull_Cross'] = (df['%K'] > df['%D']) & (df['%K'].shift(1) <= df['%D'].shift(1))
    df['Stoch_Bear_Cross'] = (df['%K'] < df['%D']) & (df['%K'].shift(1) >= df['%D'].shift(1))
    df['Below_EMA200'] = df['close'] < df['EMA200']

    dates_of_interest = [
        # Missed Sells
        ('2021-11-03', '2021-11-11', 'Missed Sell'),
        ('2024-05-21', '2024-05-28', 'Missed Sell'),
        ('2024-12-05', '2024-12-16', 'Missed Sell'),
        ('2025-08-13', '2025-08-26', 'Missed Sell'),
        ('2025-10-04', '2025-10-09', 'Missed Sell'),
        
        # Bad Buys (Don't buy)
        ('2021-11-24', '2021-12-30', 'Bad Buy Zone'),
        ('2024-12-24', '2025-01-20', 'Bad Buy Zone')
    ]

    with open("detailed_inspection.txt", "w") as f:
        # User wants to analyze May 10, 2021 to April 12, 2022
        start = '2021-05-10'
        end = '2022-04-12'
        label = "Target Sell Zone"
        
        f.write(f"\n=== {label} ({start} to {end}) ===\n")
        mask = (df.index >= start) & (df.index <= end)
        subset = df.loc[mask]
        
        if subset.empty:
            f.write("No data found\n")
            return

        # Calculate EMA Extension
        subset = subset.copy()
        subset['EMA_Ext'] = (subset['close'] - subset['EMA200']) / subset['EMA200'] * 100
        
        # Print header
        f.write(f"{'Date':<12} | {'Close':<8} | {'RSI':<6} | {'EMA200':<8} | {'Ext%':<6} | {'Stoch Bear':<10}\n")
        f.write("-" * 80 + "\n")
        
        for idx, row in subset.iterrows():
            date_str = str(idx.date())
            stoch_bear = "YES" if row['Stoch_Bear_Cross'] else ""
            f.write(f"{date_str:<12} | {row['close']:<8.2f} | {row['RSI']:<6.2f} | {row['EMA200']:<8.2f} | {row['EMA_Ext']:<6.2f} | {stoch_bear:<10}\n")

    print("Detailed results written to detailed_inspection.txt")

if __name__ == "__main__":
    inspect_dates()
