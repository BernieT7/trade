# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 01:13:58 2024

@author: user
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

def get_CAGR(DF):
    df = DF.copy()  # 複製數據
    df["cum return"] = (1 + df["ret"]).cumprod()  # 計算累積收益率
    n = len(df) / 252*75  # 計算年份數（假設一年有 252 個交易日）
    CAGR = (df["cum return"].iloc[-1])**(1/n) - 1  # 計算 CAGR
    return CAGR

def get_volatility(DF):
    df = DF.copy()  # 複製數據
    vol = df["ret"].std() * np.sqrt(252*75)  # 計算年度波動率
    return vol

def ATR(data_frame, window=20):
    df = data_frame.copy()
    df["H-L"] = df["High"] - df["Low"]
    df["abs H-pre_close"] = abs(df["High"] - df["Adj Close"].shift(1))
    df["abs L-pre_close"] = abs(df["Low"] - df["Adj Close"].shift(1))
    df["TR"] = df[["H-L", "abs H-pre_close", "abs L-pre_close"]].max(axis=1, skipna=False)
    df["ATR"] = df["TR"].ewm(span=window, min_periods=window).mean()
    return df["ATR"]

def get_sharpe(DF, rf):
    df = DF.copy()
    sharpe = (get_CAGR(df) - rf) / get_volatility(df)  # 計算夏普比率
    return sharpe

def get_MDD(DF):    
    df = DF.copy()
    df["cum return"] = (1 + df["ret"]).cumprod()  # 計算累積收益率
    df["max cum return"] = df["cum return"].cummax()  # 計算累積收益率中的最大值
    df["drawdown"] = df["max cum return"] - df["cum return"]  # 計算回撤
    MDD = (df["drawdown"]/df["max cum return"]).max()  # 計算最大回撤
    return MDD

def get_calmar(DF):
    df = DF.copy()
    cal = get_CAGR(df) / get_MDD(df)  # 卡馬比率 = CAGR / 最大回撤
    return cal

def get_risk_free_rate():
    # 使用 'TNX' 獲取 10 年期美國國債收益率 (數據來自雅虎財經)
    ticker = "^TNX"
    data = yf.download(ticker, period="1d")
    
    # 將收益率從百分比轉換為小數形式
    risk_free_rate = data['Close'].iloc[-1] / 100
    return risk_free_rate

stocks = [
    "MMM",  # 3M
    "AMGN",  # American Express
    "AAPL", # Apple
    "AXP",   # Boeing
    "AMZN",  # Caterpillar
    "BA",  # Chevron
    "CAT", # Cisco Systems
    "CVX",   # Coca-Cola
    "CSCO",  # Dow Inc.
    "KO",  # ExxonMobil
    "GS",   # Goldman Sachs
    "HD",   # Home Depot
    "DOW",  # IBM
    "INTC", # Intel
    "JNJ",  # Johnson & Johnson
    "JPM",  # JPMorgan Chase
    "HON",  # McDonald's
    "IBM",  # Merck & Co.
    "MSFT", # Microsoft
    "MCD",  # Nike
    "MRK",  # Pfizer
    "PG",   # Procter & Gamble
    "TRV",  # Travelers Companies
    "UNH",  # UnitedHealth Group
    "VZ",   # Verizon
    "V",    # Visa
    "NKE",  # Walgreens Boots Alliance
    "WMT",  # Walmart
    "DIS",  # Walt Disney
    "TRV",  # Travelers
    "CRM",  # Salesforce.com
]

ohlc_data = {}

for ticker in stocks:
    temp = yf.download(ticker, period="60d", interval="5m")
    temp.dropna(how="any", inplace=True)
    ohlc_data[ticker] = temp

stocks = ohlc_data.keys()
ohlc_df = ohlc_data.copy()
signal = {}
ret = {}
for ticker in stocks:
    ohlc_df[ticker]["rollin_max"] = ohlc_df[ticker]["High"].rolling(20).max()
    ohlc_df[ticker]["rollin_min"] = ohlc_df[ticker]["Low"].rolling(20).min()
    ohlc_df[ticker]["rolling_max_vol"] = ohlc_df[ticker]["Volume"].rolling(20).max()
    ohlc_df[ticker]["ATR"] = ATR(ohlc_df[ticker])
    ohlc_df[ticker].dropna(inplace=True)
    signal[ticker] = ""
    ret[ticker] = []

# buy/sell: price > max/price < min and vol > 1.5 * max_vol
# stop loss: price < pre_close - ATR / price > pre_close + ATR 

for ticker in stocks:
    for i in range(len(ohlc_df[ticker])):
        if signal[ticker] == "":
            ret[ticker].append(0)
            if ohlc_df[ticker]["High"][i] >= ohlc_df[ticker]["rollin_max"][i] and \
            ohlc_df[ticker]["Volume"][i] >= 1.5 * ohlc_df[ticker]["rolling_max_vol"][i-1]:
                signal[ticker] = "buy"
            elif ohlc_df[ticker]["Low"][i] <= ohlc_df[ticker]["rollin_min"][i] and \
            ohlc_df[ticker]["Volume"][i] >= 1.5 * ohlc_df[ticker]["rolling_max_vol"][i-1]:
                signal[ticker] = "sell"
        elif signal[ticker] == "buy":
            if ohlc_df[ticker]["Low"][i] < ohlc_df[ticker]["Close"][i-1] - ohlc_df[ticker]["ATR"][i-1]:
                signal[ticker] = ""
                ret[ticker].append((ohlc_df[ticker]["Close"][i-1] - ohlc_df[ticker]["ATR"][i-1])/(ohlc_df[ticker]["Close"][i-1])-1)
            elif ohlc_df[ticker]["Low"][i] <= ohlc_df[ticker]["rollin_min"][i] and \
            ohlc_df[ticker]["Volume"][i] >= 1.5 * ohlc_df[ticker]["rolling_max_vol"][i-1]:
                signal[ticker] = "sell"
                ret[ticker].append((ohlc_df[ticker]["Close"][i]/ohlc_df[ticker]["Close"][i-1]) - 1)
            else:
                ret[ticker].append((ohlc_df[ticker]["Close"][i]/ohlc_df[ticker]["Close"][i-1]) - 1)
        elif signal[ticker] == "sell":
            if ohlc_df[ticker]["High"][i] > ohlc_df[ticker]["Close"][i-1] + ohlc_df[ticker]["ATR"][i-1]:
                signal[ticker] = ""
                ret[ticker].append((ohlc_df[ticker]["Close"][i-1] + ohlc_df[ticker]["ATR"][i-1])/(ohlc_df[ticker]["Close"][i-1])-1)
            elif ohlc_df[ticker]["High"][i] >= ohlc_df[ticker]["rollin_max"][i] and \
            ohlc_df[ticker]["Volume"][i] >= 1.5 * ohlc_df[ticker]["rolling_max_vol"][i-1]:
                signal[ticker] = "buy"
                ret[ticker].append((ohlc_df[ticker]["Close"][i]/ohlc_df[ticker]["Close"][i-1]) - 1)
            else:
                ret[ticker].append((ohlc_df[ticker]["Close"][i]/ohlc_df[ticker]["Close"][i-1]) - 1)

    ohlc_df[ticker]["ret"] = np.array(ret[ticker])

rf = get_risk_free_rate()  # 設定無風險收益率
strategy_ret = pd.DataFrame()
for ticker in stocks:
    strategy_ret[ticker] = ohlc_df[ticker]["ret"]
strategy_ret["ret"] = strategy_ret.mean(axis=1)
cagr = get_CAGR(strategy_ret)
sharpe_ratio = get_sharpe(strategy_ret, rf)
CR = get_calmar(strategy_ret) 

DJI = yf.download("^DJI", period="60d", interval="5m")  # 下載道瓊指數數據
DJI["ret"] = DJI["Adj Close"].pct_change() 

fig, ax = plt.subplots()  # 創建圖表
plt.plot((1+strategy_ret["ret"]).cumprod())  # 繪製投資組合的累積收益率
plt.plot((1+DJI["ret"]).cumprod())  # 繪製道瓊指數的累積收益率
plt.title("Index Return vs Strategy Return")  # 設置圖表標題
plt.ylabel("cumulative return")  # 設置Y軸標籤
plt.xlabel("time")  # 設置X軸標籤
ax.legend(["Strategy Return","DJI Return"])
