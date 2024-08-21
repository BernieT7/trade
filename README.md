# __Trading Strategy__
## Strategies
1. Portfolios rebalancing
2. Renko & MACD
3. Renko & OBV
4. resistance breakout
## Introduction
### 1. Portfolios rebalancing
策略說明：
    
    1.目標是擊敗道瓊工業平均指數的長期交易策略, DJI。
    
    2. 選取DJI中30支成分股作為主要買賣標的
    
    3. 設定投資組合最高持有6張不同股票
    
    4. 每個月計算DJI所有成分股月收益率
    
    5. 每個月調整投資組合，將投資組合中表現最差的3檔股票剃除，並加入其餘表現最好的3檔股票

回測：
    
    選取過去五年DJI成分股的股價資訊作為回測資料，比較此投資策略是否勝過DJI，我會以Compound Annual Growth Rate(CAGR), Sharpe ratio(SR), 
    Calmar ratio(CR)比較兩者的差異 
    
    回測結果：
        
        |标题1|strategy|DJI|
        |-------|-------|-------|
        |CAGR|10.94%|8.69%|
        |SR|0.3627|0.2735|
        |CR|0.3909|0.3747|
        
### 2. Renko & MACD
策略說明：
    
    1. Renko chart：

        Renko chart, 磚形圖，與平常的K線圖不同的是會以固定大小磚塊替代candles，磚的大小由自己設定，當價格突破了一個磚的大小才會形成新的磚，
        新的磚只會再原磚的45度角處生成；由於需要價格突破了一個磚的大小才會形成磚，而每次價格的突破所需時間皆不同，因此每塊磚之間的時間長度也
        不固定。磚形圖的優勢在於排除了其他因素，只專注於價格因子。
    
    2. MACD :

        在了解MACD之前必須先了解exponential moving average, EMA，EMA為指數加權平均，越靠近當前的數據全中相對高，而越遠離當前的數據權重相
        對低，EMA<sub>t</sub> = a*P<sub>t</sub> + (1-a)EMA<sub>t-1</sub>, a=2/(1+N), N為窗口大小
    
    3. 設定投資組合最高持有6張不同股票
    
    4. 每個月計算DJI所有成分股月收益率
    
    5. 每個月調整投資組合，將投資組合中表現最差的3檔股票剃除，並加入其餘表現最好的3檔股票

回測：
    
    選取過去五年DJI成分股的股價資訊作為回測資料，比較此投資策略是否勝過DJI
    
    回測結果：
        
        1. Compound Annual Growth Rate:            
        
        2. Sharpe ratio:
        
        3. Calmar ratio:
