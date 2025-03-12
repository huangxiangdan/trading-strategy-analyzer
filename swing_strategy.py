import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SwingTrader:
    def __init__(self, data, initial_shares=1000, trade_shares=100, threshold=0.1):
        """
        初始化波段交易策略
        :param data: DataFrame，包含股票价格数据
        :param initial_shares: 初始持股数量
        :param trade_shares: 每次交易的股数
        :param threshold: 触发信号的价格变化阈值
        """
        self.data = data.copy()
        self.trade_shares = trade_shares
        self.threshold = threshold
        
        # 初始化持仓DataFrame
        self.positions = pd.DataFrame(index=data.index)
        self.positions['Close'] = data['Close']
        self.positions['Signal'] = 0
        self.positions['Shares'] = float(initial_shares)
        self.positions['Cash'] = 100000.0  # 初始现金10万
        
        # 计算初始总资产
        initial_total_asset = float(initial_shares * data['Close'].iloc[0] + 100000.0)
        self.positions['Total_Asset'] = initial_total_asset
        
        # 生成交易信号和执行回测
        self._generate_signals()
        self._backtest()
    
    def _generate_signals(self):
        """生成交易信号，基于复权价格的波动"""
        reference_price = self.data['Close'].iloc[0]  # 初始参考价格（复权）
        
        for i in range(1, len(self.data)):
            current_price = self.data['Close'].iloc[i]
            price_change = (current_price - reference_price) / reference_price
            
            # 根据价格变化生成信号
            if price_change >= self.threshold:  # 上涨超过阈值，卖出
                self.positions.iloc[i, self.positions.columns.get_loc('Signal')] = -1
                reference_price = current_price
            elif price_change <= -self.threshold:  # 下跌超过阈值，买入
                self.positions.iloc[i, self.positions.columns.get_loc('Signal')] = 1
                reference_price = current_price
    
    def _backtest(self):
        """执行回测，使用复权价格计算资产价值"""
        for i in range(1, len(self.positions)):
            # 复制前一天的持仓和现金
            self.positions.iloc[i, self.positions.columns.get_loc('Shares')] = self.positions.iloc[i-1]['Shares']
            self.positions.iloc[i, self.positions.columns.get_loc('Cash')] = self.positions.iloc[i-1]['Cash']
            
            # 根据信号执行交易
            signal = self.positions.iloc[i]['Signal']
            if signal == 1:  # 买入信号
                shares_to_buy = self.trade_shares
                cost = shares_to_buy * self.positions.iloc[i]['Close']
                if cost <= self.positions.iloc[i]['Cash']:
                    self.positions.iloc[i, self.positions.columns.get_loc('Shares')] += shares_to_buy
                    self.positions.iloc[i, self.positions.columns.get_loc('Cash')] -= float(cost)
            elif signal == -1:  # 卖出信号
                shares_to_sell = self.trade_shares
                if shares_to_sell <= self.positions.iloc[i]['Shares']:
                    proceeds = float(shares_to_sell * self.positions.iloc[i]['Close'])
                    self.positions.iloc[i, self.positions.columns.get_loc('Shares')] -= shares_to_sell
                    self.positions.iloc[i, self.positions.columns.get_loc('Cash')] += proceeds
            
            # 更新总资产价值（使用复权价格）
            total_asset = float(
                self.positions.iloc[i]['Shares'] * self.positions.iloc[i]['Close'] +
                self.positions.iloc[i]['Cash']
            )
            self.positions.iloc[i, self.positions.columns.get_loc('Total_Asset')] = total_asset
    
    def display_summary(self):
        """显示回测结果摘要"""
        print("\n" + "=" * 80)
        print("波段策略回测结果摘要")
        print("=" * 80)
        
        # 计算收益率
        initial_value = self.positions['Total_Asset'].iloc[0]
        final_value = self.positions['Total_Asset'].iloc[-1]
        returns = (final_value - initial_value) / initial_value * 100
        
        # 获取初始价格和最终价格
        first_price = self.data['Close'].iloc[0]
        last_price = self.data['Close'].iloc[-1]
        buy_and_hold_return = (last_price / first_price - 1) * 100
        
        # 打印汇总信息
        print(f"初始资产: ${initial_value:,.2f} ({self.positions['Shares'].iloc[0]:.0f}股 × ${first_price:.2f} + ${self.positions['Cash'].iloc[0]:,.2f}现金)")
        print(f"最终资产: ${final_value:,.2f}")
        final_position = self.positions['Shares'].iloc[-1]
        final_cash = self.positions['Cash'].iloc[-1]
        print(f"- 最终持股: {final_position:.0f} 股，价值: ${final_position * last_price:,.2f}")
        print(f"- 最终现金: ${final_cash:,.2f}")
        print(f"总收益率: {returns:.2f}%")
        
        # 交易统计
        buy_signals = sum(self.positions['Signal'] == 1)
        sell_signals = sum(self.positions['Signal'] == -1)
        
        print(f"交易统计:")
        print(f"- 买入交易: {buy_signals} 次")
        print(f"- 卖出交易: {sell_signals} 次")
        print(f"- 每次交易: {self.trade_shares}股")
        
        # 与买入持有策略比较
        buy_and_hold_value = self.positions['Shares'].iloc[0] * last_price + self.positions['Cash'].iloc[0]
        print(f"\n买入持有策略收益率: {buy_and_hold_return:.2f}% (最终价值: ${buy_and_hold_value:,.2f})")
        print(f"波段策略 vs 买入持有: {returns - buy_and_hold_return:.2f}%")

# 使用示例
if __name__ == "__main__":
    ticker = yf.Ticker("AAPL")
    data = ticker.history(start="2023-05-01", end="2024-05-01")
    trader = SwingTrader(data, initial_shares=1000, trade_shares=100)
    trader.display_summary() 