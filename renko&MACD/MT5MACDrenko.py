# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 19:29:10 2024

@author: user
"""

import MetaTrader5 as mt5
import os
import datetime as dt
import pandas as pd
import numpy as np
from stocktrends import Renko
import copy
import time

def renko_DF(data_frame):
    df = data_frame.copy()
    # 重設索引並更改列名稱以匹配Renko要求
    df.drop("Close", axis=1, inplace=True)  # 刪除不必要的列
    df.reset_index(inplace=True)
    df.columns = ["date", "open", "high", "low", "close", "volume"]
    
    # 初始化Renko圖表並設置brick_size
    df_2 = Renko(df)
    df_2.brick_size = round(ATR(data_frame, 120).iloc[-1], 4)  # 設置brick_size
    
    renko_df = df_2.get_ohlc_data()
    renko_df["bar_num"] = np.where(renko_df["uptrend"] == True, 1, np.where(renko_df["uptrend"] == False, -1, 0))
    for i in range(1, len(renko_df["bar_num"])):
        if renko_df["bar_num"][i] > 0 and renko_df["bar_num"][i-1] > 0:
            renko_df["bar_num"][i] += renko_df["bar_num"][i-1]
        elif renko_df["bar_num"][i] < 0 and renko_df["bar_num"][i-1] < 0:
            renko_df["bar_num"][i] += renko_df["bar_num"][i-1]
    renko_df.drop_duplicates(subset="date",keep="last",inplace=True)
    return renko_df

def MACD(data_frame, slow_window=26, fast_window=12, signal_window=9):
    df = data_frame.copy()
    df["slow_ema"] = df["Close"].ewm(span=slow_window, min_periods=slow_window).mean()
    df["fast_ema"] = df["Close"].ewm(span=fast_window, min_periods=fast_window).mean()
    df["macd"] = df["fast_ema"] - df["slow_ema"]
    df["signal"] = df["macd"].ewm(span=signal_window, min_periods=signal_window).mean()
    df.dropna(inplace=True)
    return df.loc[:, ["macd", "signal"]]

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

def get_5m_candles(currency, lookback=10, bars=250):
    data = mt5.copy_rates_from(currency, mt5.TIMEFRAME_M5, dt.datetime.now() - dt.timedelta(10), 250)   
    data_df = pd.DataFrame(data) 
    data_df["time"] = pd.to_datetime(data_df["time"], unit="s")
    data_df.set_index("time", inplace=True)
    data_df.drop(["spread", "real_volume"], axis=1, inplace=True)
    data_df.rename(columns={"time": "date", "open":"Open","high":"High","low":"Low","close":"Close","tick_volume":"Volume"},inplace=True)
    return data_df

def renko_merge(DF):
    df = DF.copy()
    df = copy.deepcopy(DF)
    df["Date"] = df.index
    renko = renko_DF(df)
    renko.columns = ["Date","open","high","low","close","uptrend","bar_num"]
    merged_df = df.merge(renko.loc[:,["Date","bar_num"]],how="outer",on="Date")
    merged_df["bar_num"].fillna(method='ffill',inplace=True)
    merged_df[["MACD", "Signal"]] = MACD(merged_df)
    return merged_df

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

def trade_signal(merged_df, l_s):
    signal = ""
    df = merged_df.copy()
    if l_s == "":
        if df["bar_num"].tolist()[-1] >= 2 and df["MACD"].tolist()[-1] > df["Signal"].tolist()[-1]:
            signal = "buy"
        elif df["bar_num"].tolist()[-1] <= -2 and df["MACD"].tolist()[-1] < df["Signal"].tolist()[-1]:
            signal = "sell"
    elif l_s == "buy":
        if df["MACD"].tolist()[-1] < df["Signal"].tolist()[-1] and df["MACD"].tolist()[-2] > df["Signal"].tolist()[-2]:
            signal = "close"
        elif df["bar_num"].tolist()[-1] <= -2 and df["MACD"].tolist()[-1] < df["Signal"].tolist()[-1]:
            signal = "close_sell"
    elif l_s == "sell":
        if df["MACD"].tolist()[-1] > df["Signal"].tolist()[-1] and df["MACD"].tolist()[-2] < df["Signal"].tolist()[-2]:
            signal = "close"
        elif df["bar_num"].tolist()[-1] >= 2 and df["MACD"].tolist()[-1] > df["Signal"].tolist()[-1]:
            signal = "close_buy"

    return signal


# 切換當前工作目錄
os.chdir(r"C:\Users\user\Desktop\trade\keys")

# 讀取MT5帳號信息
key = open("mt5_key.txt", "r").read().split()
path = r"C:\Program Files\MetaTrader 5\terminal64.exe"

# 初始化MT5並連接到交易伺服器
if mt5.initialize(path=path, login=int(key[0]), password=key[1], server=key[2]):
    print("成功連接到MT5")
    
pairs = ['EURUSD','GBPUSD','USDCHF','AUDUSD','USDCAD']     
pos_size = 0.5
    
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
            signal = trade_signal(renko_merge(ohlc), long_short)
            
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
#   except Exception as e:
#       print(e)
#       print("error encountered....skipping this iteration")
            
starttime=time.time()
timeout = time.time() + 60*60*1  # 60 seconds times 60 meaning the script will run for 1 hr
while time.time() <= timeout:
    try:
        print("passthrough at ",time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        main()
        time.sleep(150 - ((time.time() - starttime) % 150.0)) # 5 minute interval between each new execution
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        break      
   