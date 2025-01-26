import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, WilliamsRIndicator
from ta.trend import MACD
import time
import os
import sys
import webbrowser

ALPHA_VANTAGE_API = os.getenv("ALPHA_VANTAGE_KEY", "SRIT41YP8GIOTS9E")
FINHUB_API = os.getenv("FINHUB_API_KEY", "YOUR_FINHUB_KEY_HERE")
FMP_API_KEY = "spe982sd6xe99JtvhqJfMHSYWlbIn1w3"
AUTHOR = "Goutham Sankar"
VERSION = "4.2.2"
REDIRECT_URL = "https://www.instagram.com/gouth.ampvtt/"

BANNER = r"""
███████╗███████╗ ██████╗ █████╗ ██████╗ ███████╗                                                   
██╔════╝██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝                                                   
█████╗  ███████╗██║     ███████║██████╔╝█████╗                                                     
██╔══╝  ╚════██║██║     ██╔══██║██╔═══╝ ██╔══╝                                                     
███████╗███████║╚██████╗██║  ██║██║     ███████╗                                                   
╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚══════╝                                                   
                                    ████████╗██╗  ██╗███████╗                                      
                                    ╚══██╔══╝██║  ██║██╔════╝                                      
                                       ██║   ███████║█████╗                                        
                                       ██║   ██╔══██║██╔══╝                                        
                                       ██║   ██║  ██║███████╗                                      
                                       ╚═╝   ╚═╝  ╚═╝╚══════╝                                      
                                                    ███╗   ███╗ █████╗ ████████╗██████╗ ██╗██╗  ██╗
                                                    ████╗ ████║██╔══██╗╚══██╔══╝██╔══██╗██║╚██╗██╔╝
                                                    ██╔████╔██║███████║   ██║   ██████╔╝██║ ╚███╔╝ 
                                                    ██║╚██╔╝██║██╔══██║   ██║   ██╔══██╗██║ ██╔██╗ 
                                                    ██║ ╚═╝ ██║██║  ██║   ██║   ██║  ██║██║██╔╝ ██╗
                                                    ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
                                                                                                   
"""

TIME_FRAMES = {
    '1': {'interval': '1min', 'label': '1 Minute'},
    '2': {'interval': '5min', 'label': '5 Minutes'},
    '3': {'interval': '15min', 'label': '15 Minutes'},
    '4': {'interval': '30min', 'label': '30 Minutes'},
    '5': {'interval': '60min', 'label': '1 Hour'},
    '6': {'interval': 'daily', 'label': 'Daily'}
}

def get_stock_data(symbol, interval='daily'):
    try:
        function = 'TIME_SERIES_INTRADAY' if interval != 'daily' else 'TIME_SERIES_DAILY'
        url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&interval={interval}&apikey={ALPHA_VANTAGE_API}&datatype=csv"
        df = pd.read_csv(url)
        return df.iloc[::-1].reset_index(drop=True)
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None

def calculate_indicators(data):
    try:
        if 'close' not in data.columns:
            raise ValueError("'close' column not found in the data.")
        data['close'] = pd.to_numeric(data['close'], errors='coerce')
        data = data.dropna(subset=['close'])
        rsi_indicator = RSIIndicator(close=data['close'], window=14)
        data['rsi'] = rsi_indicator.rsi()
        data['sma'] = data['close'].rolling(window=14).mean()
        macd_indicator = MACD(close=data['close'], window_slow=26, window_fast=12, window_sign=9)
        data['macd'] = macd_indicator.macd()
        data['macd_signal'] = macd_indicator.macd_signal()
        data['macd_hist'] = macd_indicator.macd_diff()
        williams_indicator = WilliamsRIndicator(high=data['high'], low=data['low'], close=data['close'], lbp=14)
        data['williams_r'] = williams_indicator.williams_r()
        return data
    except Exception as e:
        print(f"Indicator calculation error: {str(e)}")
        return None

def get_final_recommendation(data):
    try:
        signals = []
        if 'rsi' in data.columns:
            if data['rsi'].iloc[-1] > 70:
                signals.append("RSI: Overbought")
            elif data['rsi'].iloc[-1] < 30:
                signals.append("RSI: Oversold")
        if 'sma' in data.columns:
            if data['close'].iloc[-1] > data['sma'].iloc[-1]:
                signals.append("Price Above SMA: Bullish")
            else:
                signals.append("Price Below SMA: Bearish")
        if 'macd_hist' in data.columns:
            if data['macd_hist'].iloc[-1] > 0:
                signals.append("MACD Histogram: Bullish")
            else:
                signals.append("MACD Histogram: Bearish")
        if 'williams_r' in data.columns:
            if data['williams_r'].iloc[-1] < -80:
                signals.append("Williams %R: Overbought")
            elif data['williams_r'].iloc[-1] > -20:
                signals.append("Williams %R: Oversold")
        
        buy_signals = signals.count("RSI: Oversold") + signals.count("Price Above SMA: Bullish") + signals.count("MACD Histogram: Bullish")
        sell_signals = signals.count("RSI: Overbought") + signals.count("Price Below SMA: Bearish") + signals.count("MACD Histogram: Bearish")
        
        if buy_signals > sell_signals:
            return "🤖💹 STRONG BUY", signals
        elif sell_signals > buy_signals:
            return "🤖🔻 STRONG SELL", signals
        else:
            return "🤖⚪️ HOLD", signals
    except Exception as e:
        print(f"Recommendation error: {str(e)}")
        return "🤖❌ ERROR", []

def display_stock_analysis(symbol, df):
    try:
        print(f"\n📊 Advanced Stock Analysis for {symbol}")
        print(f"📅 Last Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n📈 Price Data:")
        print(df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail(3))
        
        if 'rsi' in df.columns:
            print(f"\n📉 RSI (14): {df['rsi'].iloc[-1]:.2f}")
            if df['rsi'].iloc[-1] > 70:
                print("⚠️ Overbought Territory")
            elif df['rsi'].iloc[-1] < 30:
                print("⚠️ Oversold Territory")
            else:
                print("✅ Neutral Range")
        
        if 'sma' in df.columns:
            print(f"\n📊 SMA (14): {df['sma'].iloc[-1]:.5f}")
            if df['close'].iloc[-1] > df['sma'].iloc[-1]:
                print("📌 Price Above SMA: Bullish Signal")
            else:
                print("📌 Price Below SMA: Bearish Signal")
        
        if 'macd' in df.columns:
            print(f"\n📈 MACD: {df['macd'].iloc[-1]:.5f}")
            print(f"📈 MACD Signal: {df['macd_signal'].iloc[-1]:.5f}")
            print(f"📈 MACD Histogram: {df['macd_hist'].iloc[-1]:.5f}")
            if df['macd_hist'].iloc[-1] > 0:
                print("📌 MACD Histogram Positive: Bullish Signal")
            else:
                print("📌 MACD Histogram Negative: Bearish Signal")
        
        if 'williams_r' in df.columns:
            print(f"\n📉 Williams %R: {df['williams_r'].iloc[-1]:.2f}")
            if df['williams_r'].iloc[-1] < -80:
                print("⚠️ Overbought Territory")
            elif df['williams_r'].iloc[-1] > -20:
                print("⚠️ Oversold Territory")
            else:
                print("✅ Neutral Range")
        
        recommendation, signals = get_final_recommendation(df)
        print(f"\n📌 Final Recommendation: {recommendation}")
        print("\n🔍 Detected Signals:")
        for signal in signals:
            print(f"  • {signal}")
        print("="*50)
    except Exception as e:
        print(f"Display error: {str(e)}")

def get_fmp_indicators(symbol, interval='daily'):
    try:
        indicators = ['rsi', 'sma', 'macd', 'wma', 'tema', 'williams', 'adx']
        results = {}
        for indicator in indicators:
            url = f"https://financialmodelingprep.com/api/v3/technical_indicator/{interval}/{symbol}?type={indicator}&period=10&apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    results[indicator] = data[0]
                else:
                    results[indicator] = None
            else:
                results[indicator] = None
        return results
    except Exception as e:
        print(f"❌ FMP API Error: {str(e)}")
        return None

def analyze_fmp_indicators(data):
    try:
        if not data:
            return "🔴 No Data", []
        signals = []
        rsi = data.get('rsi', {}).get('rsi', 50) if data.get('rsi') else 50
        macd = data.get('macd', {}).get('macd', 0) if data.get('macd') else 0
        sma = data.get('sma', {}).get('sma', 0) if data.get('sma') else 0
        wma = data.get('wma', {}).get('wma', 0) if data.get('wma') else 0
        tema = data.get('tema', {}).get('tema', 0) if data.get('tema') else 0
        williams = data.get('williams', {}).get('williams', 0) if data.get('williams') else 0
        adx = data.get('adx', {}).get('adx', 0) if data.get('adx') else 0
        
        if rsi > 70: signals.append("RSI: Overbought")
        elif rsi < 30: signals.append("RSI: Oversold")
        else: signals.append("RSI: Neutral")
        
        if macd > 0: signals.append("MACD: Bullish")
        else: signals.append("MACD: Bearish")
        
        if sma > data.get('rsi', {}).get('close', 0): signals.append("SMA: Price Below SMA (Bearish)")
        else: signals.append("SMA: Price Above SMA (Bullish)")
        
        if wma > data.get('rsi', {}).get('close', 0): signals.append("WMA: Price Below WMA (Bearish)")
        else: signals.append("WMA: Price Above WMA (Bullish)")
        
        if tema > data.get('rsi', {}).get('close', 0): signals.append("TEMA: Price Below TEMA (Bearish)")
        else: signals.append("TEMA: Price Above TEMA (Bullish)")
        
        if williams < -80: signals.append("Williams %R: Overbought")
        elif williams > -20: signals.append("Williams %R: Oversold")
        else: signals.append("Williams %R: Neutral")
        
        if adx > 25: signals.append("ADX: Strong Trend")
        elif adx < 20: signals.append("ADX: Weak Trend")
        else: signals.append("ADX: Neutral Trend")
        
        if "RSI: Oversold" in signals and "MACD: Bullish" in signals and "SMA: Price Above SMA (Bullish)" in signals:
            recommendation = "🤖💹 STRONG BUY"
        elif "RSI: Overbought" in signals and "MACD: Bearish" in signals and "SMA: Price Below SMA (Bearish)" in signals:
            recommendation = "🤖🔻 STRONG SELL"
        elif "RSI: Oversold" in signals or "MACD: Bullish" in signals:
            recommendation = "🤖🟢 BUY"
        elif "RSI: Overbought" in signals or "MACD: Bearish" in signals:
            recommendation = "🤖🔻 SELL"
        else:
            recommendation = "🤖⚪️ HOLD"
        return recommendation, signals
    except Exception as e:
        print(f"Analysis Error: {str(e)}")
        return "🤖❌ ERROR", []

def display_fmp_analysis(symbol, recommendation, signals, data, interval):
    try:
        print(f"\n📊 FMP Indicator Analysis: {symbol} ({TIME_FRAMES[interval]['label']})")
        print(f"⏱ Last Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if data:
            print("\n📈 Latest Indicator Values:")
            for indicator, values in data.items():
                if values:
                    print(f"  {indicator.upper()}: {values.get(indicator, 'N/A')}")
        print("\n🔍 Detected Signals:")
        for signal in signals:
            print(f"  • {signal}")
        print(f"\n📌 Recommendation: {recommendation}")
        print("="*50)
    except Exception as e:
        print(f"Display Error: {str(e)}")

def show_support():
    print("\n📚 Support & Documentation:")
    print("Official Documentation: https://your-docs.url")
    print("Bug Reports: https://github.com/sword-saint69/ESCAPE-THE-MATRIX/issues")
    print("Community Forum: https://DEV.TO/SWORD-SAINT")
    print("\n🛠 Troubleshooting Guide:")
    print("1. Ensure valid API keys are set")
    print("2. Check internet connection")
    print("3. Verify stock symbols are valid")

def show_author_info():
    print("\n🦸♂️ Author Information:")
    print(f"Name: {AUTHOR}")
    print(f"Version: {VERSION}")
    print("Specialization: AI & Algorithmic Trading Systems")
    print("Contact: gouthamsankar@aol.com")
    print("GitHub: github.com/Sword-saint69")

def main_menu():
    try:
        print("\n" + BANNER)
        print(f"\n🚀 ESCAPE THE MATRIX {VERSION}")
        print("[1] Advanced Stock Analysis by Alpha Vantage")
        print("[2] Finhub AI Bot")
        print("[3] FMP Indicator Analysis")
        print("[4] Support and Documentation")
        print("[5] Author Information")
        print("[6] Exit System")
        return input("\n🔍 Select option (1-6): ").strip()
    except Exception as e:
        print(f"Menu error: {str(e)}")
        return '6'

if __name__ == "__main__":
    try:
        webbrowser.open_new_tab(REDIRECT_URL)
        print(f"🔗 Opening documentation: {REDIRECT_URL}")
        time.sleep(1)
    except Exception as e:
        print(f"⚠️ Could not open browser: {str(e)}")
    
    while True:
        try:
            choice = main_menu()
            
            if choice == '1':
                symbol = input("Enter stock symbol (e.g., AAPL): ").strip().upper()
                df = get_stock_data(symbol)
                if df is not None:
                    df = calculate_indicators(df)
                    display_stock_analysis(symbol, df)
            
            elif choice == '2':
                symbol = input("Enter stock symbol: ").strip().upper()
                finhub_data = get_finhub_insights(symbol)
                if finhub_data:
                    recommendation, signals = analyze_finhub_data(finhub_data)
                    display_finhub_analysis(symbol, recommendation, signals, finhub_data)
                else:
                    print("❌ Failed to fetch Finhub data")
            
            elif choice == '3':
                symbol = input("Enter stock symbol: ").strip().upper()
                print("\n📅 Select Time Frame:")
                for key, value in TIME_FRAMES.items():
                    print(f"[{key}] {value['label']}")
                tf_choice = input("\nChoose timeframe (1-6): ").strip()
                interval = TIME_FRAMES.get(tf_choice, {}).get('interval', 'daily')
                fmp_data = get_fmp_indicators(symbol, interval)
                if fmp_data:
                    recommendation, signals = analyze_fmp_indicators(fmp_data)
                    display_fmp_analysis(symbol, recommendation, signals, fmp_data, tf_choice)
                else:
                    print("❌ Failed to fetch FMP data")
            
            elif choice == '4':
                show_support()
            
            elif choice == '5':
                show_author_info()
            
            elif choice == '6':
                print("\n👋 Exiting system...")
                sys.exit()
            
            else:
                print("\n❌ Invalid option. Please try again.")
            
            time.sleep(2)
        
        except KeyboardInterrupt:
            print("\n⏹ Operation cancelled by user")
            sys.exit()
        except Exception as e:
            print(f"\n❌ Critical System Error: {str(e)}")
            time.sleep(2)