import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random

# 生成模拟股票数据
def generate_stock_data(start_date, periods=500, volatility=0.015):
    # 创建日期索引
    date_rng = pd.date_range(start=start_date, periods=periods, freq='B')
    
    # 生成随机价格走势
    price = 100.0  # 起始价格
    prices = [price]
    for i in range(1, periods):
        # 添加一些趋势因素和随机噪声
        change = np.random.normal(0.0005, volatility)  # 均值略大于0，表示长期上涨趋势
        price *= (1 + change)
        prices.append(price)
    
    # 创建DataFrame
    df = pd.DataFrame(
        data={
            'Open': prices,
            'High': [p * (1 + random.uniform(0, 0.01)) for p in prices],
            'Low': [p * (1 - random.uniform(0, 0.01)) for p in prices],
            'Close': prices,
            'Adj Close': prices,
            'Volume': [int(random.uniform(1000000, 10000000)) for _ in range(periods)]
        },
        index=date_rng
    )
    
    return df

# 波段交易策略
class SwingTrader:
    def __init__(self, data, initial_shares=1000, trade_shares=100, cash=100000, swing_threshold=0.1):
        self.data = data.copy()
        self.initial_shares = initial_shares
        self.trade_shares = trade_shares
        self.cash = cash
        self.swing_threshold = swing_threshold
        self.reference_price = data['Close'].iloc[0]
        self.initial_asset_value = initial_shares * data['Close'].iloc[0] + cash
        self.positions = pd.DataFrame(index=data.index)
        
    def generate_signals(self):
        self.data['Signal'] = 0
        self.data['Ref_Price'] = 0.0
        
        current_ref_price = self.reference_price
        
        for i in range(len(self.data)):
            current_price = self.data['Close'].iloc[i]
            price_change = (current_price - current_ref_price) / current_ref_price
            
            self.data.loc[self.data.index[i], 'Ref_Price'] = current_ref_price
            
            # 检查是否达到波动阈值
            if price_change <= -self.swing_threshold:
                # 价格下跌超过阈值，买入信号
                self.data.loc[self.data.index[i], 'Signal'] = 1
                current_ref_price = current_price  # 更新参考价格
            elif price_change >= self.swing_threshold:
                # 价格上涨超过阈值，卖出信号
                self.data.loc[self.data.index[i], 'Signal'] = -1
                current_ref_price = current_price  # 更新参考价格
    
    def backtest_swing_strategy(self):
        self.positions['Shares'] = self.initial_shares
        self.positions['Cash'] = self.cash
        self.positions['Close'] = self.data['Close']
        
        for i in range(len(self.data)):
            date = self.data.index[i]
            price = self.data['Close'].iloc[i]
            signal = self.data['Signal'].iloc[i]
            
            if i > 0:
                self.positions.loc[date, 'Shares'] = self.positions['Shares'].iloc[i-1]
                self.positions.loc[date, 'Cash'] = self.positions['Cash'].iloc[i-1]
            
            # 根据信号执行交易
            if signal == 1:  # 买入
                # 检查现金是否足够
                cost = self.trade_shares * price
                if self.positions.loc[date, 'Cash'] >= cost:
                    self.positions.loc[date, 'Shares'] += self.trade_shares
                    self.positions.loc[date, 'Cash'] -= cost
                
            elif signal == -1:  # 卖出
                # 检查股票是否足够
                if self.positions.loc[date, 'Shares'] >= self.trade_shares:
                    self.positions.loc[date, 'Shares'] -= self.trade_shares
                    self.positions.loc[date, 'Cash'] += self.trade_shares * price
            
            # 计算总资产价值
            self.positions.loc[date, 'Stock_Value'] = self.positions.loc[date, 'Shares'] * price
            self.positions.loc[date, 'Total_Asset'] = self.positions.loc[date, 'Stock_Value'] + self.positions.loc[date, 'Cash'] 