# __Trading with Python__
## 研究目的
1.程式交易能避免人手動交易的不理性，只要符合判斷條件(進場、出場)就會執行

2.無須盯盤

3.計算快速，相較於手動交易有效率許多
## 交易策略說明
### 1. Portfolios rebalancing
#### Target:
    擊敗道瓊工業平均指數的長期交易策略, DJI。
#### Tool:
    
    衡量表現的指標:
       
        1. Compound Annual Growth Rate, CAGR:
        
        2. Sharpe ratio, SR:
        
        3. Calmar ratio, CR:
#### Data:
        
        使用道瓊工業平均指數DJI過去五年(2019/8/20~2019/8/20)的股價資訊
        
#### 策略說明：
    
    1. 選取DJI中30支成分股作為主要買賣標的
    
    2. 設定投資組合最高持有6張不同DJI的成分股股票
    
    3. 每個月計算DJI所有成分股月收益率
    
    4. 每個月調整投資組合，將投資組合中表現最差的3檔股票剃除，並加入其餘表現最好的3檔股票

#### 回測：

    回測結果如下表：
        
||strategy|DJI|
|:---:|:---:|:---:|
|CAGR|10.94%|8.69%|
|SR|0.3627|0.2735|
|CR|0.3909|0.3747|

#### 結論
    Monthly portfolios rebalancing的策略在2019/8/20~2024/8/20的整體表現勝過道瓊工業平均指數

### 2. 技術分析
#### Tools
    1.技術指標：
    (1) Renko chart：

        Renko chart, 磚形圖，與平常的K線圖不同的是會以固定大小磚塊替代candles，磚的大小由自己設定，當價格突破了一個磚的大小才會形成新的磚，
        新的磚只會再原磚的45度角處生成；由於需要價格突破了一個磚的大小才會形成磚，而每次價格的突破所需時間皆不同，因此每塊磚之間的時間長度也
        不固定。
        
        磚形圖的優勢在於排除了其他因素，只專注於價格因子。
        我打算利用Renko chart的以上性質建構交易的條件判斷
    
    (2) Moving Average Convergence Divergence, MACD :

        在了解MACD之前必須先了解exponential moving average, EMA，EMA為指數加權平均，越靠近當前的數據權重相對高，而越遠離當前的數據權重相
        對低，EMA[t] = a*P[t] + (1-a)EMA[t-1], a=2/(1+N), N為窗口大小。
        MACD = EMA12 - EMA26
        Signal line = EMA9(MACD)，也就是MACD線的EMA, while N=9
        
        買進信號 : 當MACD由下向上穿越Signal line
        賣出信號 : 當MACD由上向下穿越Signal line
        我打算利用MACD的以上性質建構交易的條件判斷

    (3) On-Balance Volume, OBV:

        OBV基於每天的交易量變化來計算：
            當日收盤價高於前日收盤價：將當日的交易量加到 OBV 中。
            當日收盤價低於前日收盤價：將當日的交易量從 OBV 中減去。
            當日收盤價等於前日收盤價 : OBV 保持不變。
            
        OBV 線上升時，表明買盤力量強，市場可能處於上升趨勢。
        OBV 線下降時，表明賣盤力量強，市場可能處於下降趨勢。
        
        我打算利用OBV的以上性質建構交易的條件判斷
#### Data:
    
    以美股交易量較大的5支股票作為主要交易標的: Apple, Google, Microsoft, Amazon, Tesla
    
#### 策略說明：

    我將使用不一樣的技術指標搭配，購艦出三項交易策略並且比較三者的表現:
    1. Renko chart：

        Renko chart, 磚形圖，與平常的K線圖不同的是會以固定大小磚塊替代candles，磚的大小由自己設定，當價格突破了一個磚的大小才會形成新的磚，
        新的磚只會再原磚的45度角處生成；由於需要價格突破了一個磚的大小才會形成磚，而每次價格的突破所需時間皆不同，因此每塊磚之間的時間長度也
        不固定。磚形圖的優勢在於排除了其他因素，只專注於價格因子。
    
    2. MACD :

        在了解MACD之前必須先了解exponential moving average, EMA，EMA為指數加權平均，越靠近當前的數據全中相對高，而越遠離當前的數據權重相
        對低，EMA[t] = a*P[t] + (1-a)EMA[t-1], a=2/(1+N), N為窗口大小。
        MACD = EMA12 - EMA26
        Signal line = EMA9(MACD)，也就是MACD線的EMA, while N=9
    
    3. 買入信號：連續兩個以上的上升renko bar加上MACD line大於Singnal line，並且MACD line的斜率大於Singnal line斜率
       出場時機：MACD line小於Singnal line，並且MACD line的斜率小於Singnal line斜率
    
    4. 賣出信號：連續兩個以上的下降renko bar加上MACD line小於Singnal line，並且MACD line的斜率小於Singnal line斜率
       出場時機：MACD line大於Singnal line，並且MACD line的斜率大於Singnal line斜率

回測：
    
    選取過去五年DJI成分股的股價資訊作為回測資料，比較此投資策略是否勝過DJI
    
    回測結果：
        
        1. Compound Annual Growth Rate:            
        
        2. Sharpe ratio:
        
        3. Calmar ratio:
