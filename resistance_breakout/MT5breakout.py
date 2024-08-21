# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 11:21:11 2024

@author: user
"""

import MetaTrader5 as mt5
import os
import datetime as dt
import pandas as pd
import numpy as np
import time

def ATR(data_frame, window=20):
    df = data_frame.copy()
    df["H-L"] = df["High"] - df["Low"]
    df["abs H-pre_close"] = abs(df["High"] - df["Close"].shift(1))
    df["abs L-pre_close"] = abs(df["Low"] - df["Close"].shift(1))
    df["TR"] = df[["H-L", "abs H-pre_close", "abs L-pre_close"]].max(axis=1, skipna=False)
    df["ATR"] = df["TR"].ewm(span=window, min_periods=window).mean()
    return df["ATR"]

def get_positions():
    positions = mt5.positions_get()
    if len(positions) > 0:
        # 將持倉信息轉換為DataFrame
        pos_df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
        # 將時間欄位轉換為日期時間格式
        pos_df["time"] = pd.to_datetime(pos_df["time"], unit="s")
        # 刪除不必要的時間欄位
        pos_df.drop(["time_msc", "time_update", "time_update_msc", "external_id"], axis=1, inplace=True)
        pos_df["type"] = np.where(pos_df["type"]==0, 1, -1)
    else:
        pos_df = pd.DataFrame()
    
    return pos_df

def get_5m_candles(currency, lookback=10, bars=500):
    data = mt5.copy_rates_from(currency, mt5.TIMEFRAME_M5, dt.datetime.now() - dt.timedelta(10), 500)   
    data_df = pd.DataFrame(data) 
    data_df["time"] = pd.to_datetime(data_df["time"], unit="s")
    data_df.set_index("time", inplace=True)
    data_df.drop(["spread", "real_volume"], axis=1, inplace=True)
    data_df.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","tick_volume":"Volume"},inplace=True)
    return data_df

def strategy(DF):
    df = DF.copy()
    df["rollin_max"] = df["High"].rolling(20).max()
    df["rollin_min"] = df["Low"].rolling(20).min()
    df["rolling_max_vol"] = df["Volume"].rolling(20).max()
    df["ATR"] = ATR(df)
    df.dropna(inplace=True)
    return df

def place_market_order(symbol, vol, buy_sell):
    if buy_sell.capitalize()[0] == "B":
        direction = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
    else:
        direction = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": vol,
        "type": direction,
        "price": price,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    
    result = mt5.order_send(request)
    return result

def trade_signal(DF, l_s):
    signal = ""
    df = DF.copy()
    if l_s == "":
        if df["High"][-1] >= df["rollin_max"][-1] and df["Volume"][-1] >= 1.5 * df["rolling_max_vol"][-2]:
            signal = "buy"
        elif df["Low"][-1] <= df["rollin_min"][-1] and df["Volume"][-1] >= 1.5 * df["rolling_max_vol"][-1]:
            signal = "sell"
    elif l_s == "buy":
        if df["Low"][-1] < df["Close"][-2] - df["ATR"][-2]:
            signal = "close"
        elif df["Low"][-1] <= df["rollin_min"][-1] and df["Volume"][-1] >= 1.5 * df["rolling_max_vol"][-2]:
            signal = "close_sell"
    elif l_s == "sell":
        if df["High"][-1] > df["Close"][-2] + df["ATR"][-2]:
            signal = ""
        elif df["High"][-1] >= df["rollin_max"][-1] and df["Volume"][-1] >= 1.5 * df["rolling_max_vol"][-2]:
            signal = "buy"

    return signal

def main():
#    try:
        for currency in pairs:
            positions = get_positions()
            long_short = ""
            if len(positions) > 0:
                cur_pos = positions[positions["symbol"]==currency]
                if len(cur_pos)>0:
                    if (cur_pos["type"] * cur_pos["volume"]).sum() > 0:
                        long_short = "long"
                    elif (cur_pos["type"] * cur_pos["volume"]).sum() < 0:
                        long_short = "short"
                            
            ohlc = get_5m_candles(currency)
            signal = trade_signal(strategy(ohlc), long_short)
    
            if signal == "buy" or signal == "sell":
                place_market_order(currency, pos_size, signal)
                print(f"New {signal} position initiated for {currency}")
            elif signal == "close":
                tol_pos = (cur_pos["type"] * cur_pos["volume"]).sum()
                if tol_pos > 0:
                    place_market_order(currency, tol_pos, "sell")
                elif tol_pos < 0:
                    place_market_order(currency, abs(tol_pos), "buy")
                print("All positions closed for ", currency)
            elif signal == "close_buy":
                tol_pos = (cur_pos["type"] * cur_pos["volume"]).sum()
                place_market_order(currency, abs(tol_pos)+pos_size, "buy")
                print("Existing Short position closed for ", currency)
                print("New long position initiated for ", currency)
            elif signal == "close_sell":
                tol_pos = (cur_pos["type"] * cur_pos["volume"]).sum()
                place_market_order(currency, abs(tol_pos)+pos_size, "sell")
                print("Existing Long position closed for ", currency)
                print("New Short position initiated for ", currency)
                
#    except Exception as e:
#       print(e)
#       print("error encountered....skipping this iteration")
    
os.chdir(r"C:\Users\user\Desktop\trade\keys")

# 讀取MT5帳號信息
key = open("mt5_key.txt", "r").read().split()
path = r"C:\Program Files\MetaTrader 5\terminal64.exe"

# 初始化MT5並連接到交易伺服器
if mt5.initialize(path=path, login=int(key[0]), password=key[1], server=key[2]):
    print("成功連接到MT5")
    
pairs = [
    "EURUSD",  
    "USDJPY",   
    "AUDUSD",  
    "GBPUSD",  
    "USDRUB",
    "USDCHF"
]    
pos_size = 0.5    
    
starttime=time.time()
while True:
    try:
        print("passthrough at ",time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        main()
        time.sleep(30 - ((time.time() - starttime) % 30.0)) # 5 minute interval between each new execution
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        break          
    
    
    
    
