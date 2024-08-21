# -*- coding: utf-8 -*-
"""
Created on Wed Jul 31 01:13:58 2024

@author: user
"""

import numpy as np
import pandas as pd
import yfinance as yf

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

def get_risk_free_rate():
    # 使用 'TNX' 獲取 10 年期美國國債收益率 (數據來自雅虎財經)
    ticker = "^TNX"
    data = yf.download(ticker, period="1d")
    
    # 將收益率從百分比轉換為小數形式
    risk_free_rate = data['Close'].iloc[-1] / 100
    return risk_free_rate

pairs = [
    "EURUSD=X",  
    "JPYUSD=X",   
    "AUDUSD=X",  
    "GBPUSD=X",  
    "CADUSD=X",
    "CNYUSD=X",
    "CHFUSD=X",
    "KRWUSD=X"
]
ohlc_data = {}

for ticker in pairs:
    temp = yf.download(ticker, interval="5m")
    temp.dropna(how="any", inplace=True)
    ohlc_data[ticker] = temp

pairs = ohlc_data.keys()
ohlc_df = ohlc_data.copy()
signal = {}
ret = {}
for ticker in pairs:
    ohlc_df[ticker]["rollin_max"] = ohlc_df[ticker]["High"].rolling(20).max()
    ohlc_df[ticker]["rollin_min"] = ohlc_df[ticker]["Low"].rolling(20).min()
    ohlc_df[ticker]["rolling_max_vol"] = ohlc_df[ticker]["Volume"].rolling(20).max()
    ohlc_df[ticker]["ATR"] = ATR(ohlc_df[ticker])
    ohlc_df[ticker].dropna(inplace=True)
    signal[ticker] = ""
    ret[ticker] = []

# buy/sell: price > max/price < min and vol > 1.5 * max_vol
# stop loss: price < pre_close - ATR / price > pre_close + ATR 

for ticker in pairs:
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
for ticker in pairs:
    strategy_ret[ticker] = ohlc_df[ticker]["ret"]
strategy_ret["ret"] = strategy_ret.mean(axis=1)
cagr = get_CAGR(strategy_ret)
sharpe_ratio = get_sharpe(strategy_ret, rf)
MDD = get_MDD(strategy_ret) 

(1+strategy_ret["ret"]).cumprod().plot()

cagr_all = {}
sharpe_all = {}
MDD_all = {}
for ticker in pairs:
    cagr_all[ticker] = get_CAGR(ohlc_df[ticker])
    sharpe_all[ticker] = get_sharpe(ohlc_df[ticker], rf)
    MDD_all[ticker] = get_MDD(ohlc_df[ticker])
    
KPI_df = pd.DataFrame([cagr_all,sharpe_all,MDD_all],index=["Return","Sharpe Ratio","Max Drawdown"])         
KPI_df = KPI_df.T.sort_values(by="Return")
    