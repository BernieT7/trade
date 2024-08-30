# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 16:30:39 2024

@author: user
"""

import yfinance as yf  # 引入 yfinance 庫，用於下載股票數據
import numpy as np  # 引入 numpy 庫，用於數值計算
import pandas as pd  # 引入 pandas 庫，用於數據處理
import datetime as dt
import matplotlib.pyplot as plt

# 定義計算年複合增長率（CAGR）的函數
def get_CAGR(DF):
    df = DF.copy()
    df["cum return"] = (1 + df["mon_return"]).cumprod()  # 計算累積收益率
    n = len(df)/12
    CAGR = (df["cum return"].iloc[-1])**(1/n) - 1  # 計算 CAGR
    return CAGR    

# 定義計算年度波動率的函數
def get_volatility(DF):
    df = DF.copy()  # 複製數據
    vol = df["mon_return"].std() * np.sqrt(12)  # 計算年度波動率
    return vol

# 定義計算夏普比率（Sharpe Ratio）的函數
def get_sharpe(DF, rf):
    df = DF.copy()
    sharpe = (get_CAGR(df) - rf) / get_volatility(df)  # 計算夏普比率
    return sharpe

# 定義計算最大回撤（MDD）的函數
def get_MDD(DF):    
    df = DF.copy()
    df["cum return"] = (1 + df["mon_return"]).cumprod()  # 計算累積收益率
    df["max cum return"] = df["cum return"].cummax()  # 計算累積收益率中的最大值
    df["drawdown"] = df["max cum return"] - df["cum return"]  # 計算回撤
    MDD = (df["drawdown"]/df["max cum return"]).max()  # 計算最大回撤
    return MDD

# 定義計算卡馬比率（Calmar Ratio）的函數
def get_calmar(DF):
    df = DF.copy()
    cal = get_CAGR(df) / get_MDD(df)  # 卡馬比率 = CAGR / 最大回撤
    return cal

stocks = [          # 參考DJIA
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

ohlc_data = {}  # 初始化空字典，用於存儲OHLC數據
start = dt.datetime.today() - dt.timedelta(1825)  # 設定開始日期，五年(1825天)前
end = dt.datetime.today()  # 設定結束日期，今天

# 循環下載所有股票的數據
for ticker in stocks:
    temp = yf.download(ticker, start=start, end=end, interval="1mo")  # 下載股票數據，間隔為1個月
    temp.dropna(how="any", inplace=True)  # 刪除包含NA的行
    ohlc_data[ticker] = temp  # 將數據存入字典

tickers = ohlc_data.keys()  # 獲取所有股票代碼

return_df = pd.DataFrame()  # 初始化空的DataFrame，用於存儲收益率數據
for ticker in stocks:
    return_df[ticker] = ohlc_data[ticker]["Adj Close"].pct_change()  # 計算每個股票的收益率
df = return_df 
# 定義投資組合再平衡函數
def portfolio_rebalancing(DF, pos_num, x):
    df = DF.copy()  # 複製數據
    portfolios = []  # 初始化空列表，用於存儲投資組合
    monthly_return = [0]  # 初始化月收益率列表
    for i in range(len(df)):  # 遍歷每個月
        if len(portfolios) != 0:  # 如果投資組合不為空
            monthly_return.append(df[portfolios].iloc[i, :].mean())  # 計算當月投資組合的平均收益率
            bad_stocks = df[portfolios].iloc[i, :].sort_values()[:x].index.values.tolist()  # 找出表現最差的股票
            portfolios = [t for t in portfolios if t not in bad_stocks]  # 從投資組合中移除表現最差的股票
        fill = pos_num - len(portfolios)  # 計算需要補充的股票數量
        none_selected = [t for t in stocks if t not in portfolios]  # 找出未被選中的股票
        good_stocks = df[none_selected].iloc[i, :].sort_values(ascending=False)[:fill].index.values.tolist()  # 找出表現最好的股票
        portfolios = portfolios + good_stocks  # 將表現最好的股票加入投資組合
    monthly_return_df = pd.DataFrame(np.array(monthly_return), columns=["mon_return"])  # 將月收益率列表轉換為DataFrame
    return monthly_return_df  # 返回月收益率DataFrame

def get_risk_free_rate():
    # 使用 'TNX' 獲取 10 年期美國國債收益率 (數據來自雅虎財經)
    ticker = "^TNX"
    data = yf.download(ticker, period="1d")
    
    # 將收益率從百分比轉換為小數形式
    risk_free_rate = data['Close'].iloc[-1] / 100
    return risk_free_rate

pos_num = 6  # 設定投資組合中股票的數量
x = 3  # 設定需要剔除的表現最差的股票數量
rf = get_risk_free_rate()  # 設定無風險收益率

# 計算投資組合的CAGR、Sharpe Ratio、MDD和Calmar Ratio
print(get_CAGR(portfolio_rebalancing(return_df, pos_num, x)))
print(get_sharpe(portfolio_rebalancing(return_df, pos_num, x), rf))
print(get_MDD(portfolio_rebalancing(return_df, pos_num, x)))
print(get_calmar(portfolio_rebalancing(return_df, pos_num, x)))


DJI = yf.download("^DJI", start=start, end=end, interval="1mo")  # 下載道瓊指數數據
DJI["mon_return"] = DJI["Adj Close"].pct_change().fillna(0)  # 計算道瓊指數的月收益率並填充NA
# 計算道瓊指數的CAGR、Sharpe Ratio、MDD和Calmar Ratio
print()
print(get_CAGR(DJI))
print(get_sharpe(DJI, rf))
print(get_MDD(DJI))
print(get_calmar(DJI))

fig, ax = plt.subplots()  # 創建圖表
plt.plot((1+portfolio_rebalancing(return_df, pos_num, x)).cumprod())  # 繪製投資組合的累積收益率
plt.plot((1+DJI["mon_return"].reset_index(drop=True)).cumprod())  # 繪製道瓊指數的累積收益率
plt.title("Index Return vs Strategy Return(Portfolios Rebalancing)")  # 設置圖表標題
plt.ylabel("cumulative return")  # 設置Y軸標籤
plt.xlabel("months")  # 設置X軸標籤
ax.legend(["Strategy Return","Index Return"])  # 添加圖例
plt.savefig('portfolios_rebalancing.png')