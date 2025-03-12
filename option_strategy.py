import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class OptionTrader:
    def __init__(self, data, initial_shares=1000, trade_shares=100, threshold=0.1, premium_rate=0.05):
        """
        初始化期权交易策略
        :param data: DataFrame，包含股票价格数据
        :param initial_shares: 初始持股数量
        :param trade_shares: 每次交易的股数
        :param threshold: 触发信号的价格变化阈值
        :param premium_rate: 期权费率
        """
        self.data = data.copy()
        # 添加必要的列到 data DataFrame
        self.data['Signal'] = 0
        self.data['OptionType'] = ''
        self.data['IsExercised'] = False
        self.data['StrikePrice'] = 0.0
        self.data['Premium'] = 0.0
        self.data['OptionShares'] = 0
        
        self.trade_shares = trade_shares
        self.threshold = threshold
        self.premium_rate = premium_rate
        
        # 初始化持仓DataFrame
        self.positions = pd.DataFrame(index=data.index)
        self.positions['Close'] = data['Close']
        self.positions['Signal'] = 0
        self.positions['Strike'] = 0.0
        self.positions['Premium'] = 0.0
        self.positions['Shares'] = float(initial_shares)
        self.positions['Cash'] = 100000.0  # 初始现金10万
        self.positions['IsExercised'] = False
        self.positions['Premium_Income'] = 0.0
        
        # 计算初始总资产
        initial_total_asset = float(initial_shares * data['Close'].iloc[0] + 100000.0)
        self.positions['Total_Asset'] = initial_total_asset
        
        # 生成交易信号和执行回测
        self._generate_signals()
        self._backtest()
    
    def _generate_signals(self):
        """生成期权交易信号，基于复权价格的波动"""
        reference_price = self.data['Close'].iloc[0]  # 初始参考价格（复权）
        
        for i in range(1, len(self.data)):
            current_price = self.data['Close'].iloc[i]
            price_change = (current_price - reference_price) / reference_price
            
            # 根据价格变化生成信号
            if price_change >= self.threshold:  # 上涨超过阈值，卖出看涨期权
                strike_price = current_price * 0.99  # 轻度虚值期权
                premium = current_price * self.premium_rate  # 使用设定的权利金费率
                
                # 更新 positions DataFrame
                self.positions.iloc[i, self.positions.columns.get_loc('Signal')] = -1
                self.positions.iloc[i, self.positions.columns.get_loc('Strike')] = strike_price
                self.positions.iloc[i, self.positions.columns.get_loc('Premium')] = premium
                
                # 更新 data DataFrame
                self.data.iloc[i, self.data.columns.get_loc('Signal')] = -1
                self.data.iloc[i, self.data.columns.get_loc('OptionType')] = 'call'
                self.data.iloc[i, self.data.columns.get_loc('StrikePrice')] = strike_price
                self.data.iloc[i, self.data.columns.get_loc('Premium')] = premium
                self.data.iloc[i, self.data.columns.get_loc('OptionShares')] = self.trade_shares
                
                reference_price = current_price
                
            elif price_change <= -self.threshold:  # 下跌超过阈值，卖出看跌期权
                strike_price = current_price * 1.01  # 轻度虚值期权
                premium = current_price * self.premium_rate  # 使用设定的权利金费率
                
                # 更新 positions DataFrame
                self.positions.iloc[i, self.positions.columns.get_loc('Signal')] = 1
                self.positions.iloc[i, self.positions.columns.get_loc('Strike')] = strike_price
                self.positions.iloc[i, self.positions.columns.get_loc('Premium')] = premium
                
                # 更新 data DataFrame
                self.data.iloc[i, self.data.columns.get_loc('Signal')] = 1
                self.data.iloc[i, self.data.columns.get_loc('OptionType')] = 'put'
                self.data.iloc[i, self.data.columns.get_loc('StrikePrice')] = strike_price
                self.data.iloc[i, self.data.columns.get_loc('Premium')] = premium
                self.data.iloc[i, self.data.columns.get_loc('OptionShares')] = self.trade_shares
                
                reference_price = current_price
    
    def _backtest(self):
        """执行回测，使用复权价格计算资产价值"""
        premium_income = 0.0  # 跟踪累计权利金收入
        
        for i in range(1, len(self.positions)):
            # 复制前一天的持仓和现金
            self.positions.iloc[i, self.positions.columns.get_loc('Shares')] = self.positions.iloc[i-1]['Shares']
            self.positions.iloc[i, self.positions.columns.get_loc('Cash')] = self.positions.iloc[i-1]['Cash']
            self.positions.iloc[i, self.positions.columns.get_loc('Premium_Income')] = premium_income
            self.positions.iloc[i, self.positions.columns.get_loc('IsExercised')] = False  # 默认设置为 False
            
            # 检查是否有新的期权交易
            signal = self.positions.iloc[i]['Signal']
            if signal != 0:
                # 收取期权费
                premium = self.positions.iloc[i]['Premium'] * self.trade_shares
                self.positions.iloc[i, self.positions.columns.get_loc('Cash')] += premium
                premium_income += premium
                self.positions.iloc[i, self.positions.columns.get_loc('Premium_Income')] = premium_income
            
            # 检查期权是否被行权（月底）
            if self.data.index[i].is_month_end:
                strike = self.positions.iloc[i]['Strike']
                current_price = self.positions.iloc[i]['Close']
                
                if signal == -1 and current_price > strike:  # 看涨期权被行权
                    # 更新行权状态
                    self.positions.iloc[i, self.positions.columns.get_loc('IsExercised')] = True
                    
                    # 按行权价卖出股票
                    proceeds = float(strike * self.trade_shares)
                    self.positions.iloc[i, self.positions.columns.get_loc('Shares')] -= self.trade_shares
                    self.positions.iloc[i, self.positions.columns.get_loc('Cash')] += proceeds
                    
                elif signal == 1 and current_price < strike:  # 看跌期权被行权
                    # 更新行权状态
                    self.positions.iloc[i, self.positions.columns.get_loc('IsExercised')] = True
                    
                    # 按行权价买入股票
                    cost = float(strike * self.trade_shares)
                    self.positions.iloc[i, self.positions.columns.get_loc('Shares')] += self.trade_shares
                    self.positions.iloc[i, self.positions.columns.get_loc('Cash')] -= cost
            
            # 更新总资产价值（使用复权价格）
            total_asset = float(
                self.positions.iloc[i]['Shares'] * self.positions.iloc[i]['Close'] +
                self.positions.iloc[i]['Cash']
            )
            self.positions.iloc[i, self.positions.columns.get_loc('Total_Asset')] = total_asset

# 使用示例
if __name__ == "__main__":
    trader = OptionTrader(
        data=yf.Ticker("AAPL").history(start="2023-05-01", end="2024-05-01"),
        initial_shares=1000,
        trade_shares=100,
        threshold=0.1
    )
    print(trader.positions) 