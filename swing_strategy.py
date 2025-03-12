import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SwingTrader:
    def __init__(self, symbol="AAPL", start_date="2022-01-01", end_date="2024-01-01", initial_shares=1000, trade_shares=100):
        """初始化波段交易策略参数"""
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.positions = None
        self.cash = 100000  # 初始现金设为10万美元
        self.initial_shares = initial_shares  # 初始持股数
        self.trade_shares = trade_shares  # 每次交易的股数
        self.swing_threshold = 0.10  # 10%的波动阈值
        self.reference_price = None  # 参考价格，用于计算波动
        
    def fetch_data(self):
        """获取历史数据"""
        ticker = yf.Ticker(self.symbol)
        self.data = ticker.history(start=self.start_date, end=self.end_date)
        print(f"获取了{len(self.data)}个交易日的数据")
        
        # 确保数据正常
        print(f"首日价格: {self.data['Close'].iloc[0]:.2f}")
        print(f"末日价格: {self.data['Close'].iloc[-1]:.2f}")
        print(f"期间价格变化: {((self.data['Close'].iloc[-1] - self.data['Close'].iloc[0]) / self.data['Close'].iloc[0] * 100):.2f}%")
        
        # 计算初始资产价值
        self.initial_asset_value = self.initial_shares * self.data['Close'].iloc[0] + self.cash
        initial_stock_value = self.initial_shares * self.data['Close'].iloc[0]
        print(f"初始持股: {self.initial_shares}股，价值: ${initial_stock_value:,.2f}")
        print(f"初始现金: ${self.cash:,.2f}")
        print(f"初始总资产: ${self.initial_asset_value:,.2f}")
        print(f"每次交易股数: {self.trade_shares}股")
        
        # 初始化交易信号列
        self.data['Signal'] = 0  # 0=无信号, 1=买入, -1=卖出
        
        # 设置初始参考价格
        self.reference_price = self.data['Close'].iloc[0]
        
    def generate_signals(self):
        """生成交易信号"""
        print("\n生成波段交易信号...")
        
        for i in range(1, len(self.data)):
            current_date = self.data.index[i]
            current_price = self.data['Close'].iloc[i]
            
            # 计算价格变化百分比
            price_change = (current_price - self.reference_price) / self.reference_price
            
            # 价格下跌超过阈值，生成买入信号
            if price_change <= -self.swing_threshold:
                self.data.loc[self.data.index[i], 'Signal'] = 1
                print(f"买入信号 - 日期: {current_date.strftime('%Y-%m-%d')}, 价格: ${current_price:.2f}, "
                      f"参考价格: ${self.reference_price:.2f}, 变化: {price_change*100:.2f}%")
                # 更新参考价格
                self.reference_price = current_price
                
            # 价格上涨超过阈值，生成卖出信号
            elif price_change >= self.swing_threshold:
                self.data.loc[self.data.index[i], 'Signal'] = -1
                print(f"卖出信号 - 日期: {current_date.strftime('%Y-%m-%d')}, 价格: ${current_price:.2f}, "
                      f"参考价格: ${self.reference_price:.2f}, 变化: {price_change*100:.2f}%")
                # 更新参考价格
                self.reference_price = current_price
        
        # 统计交易信号
        buy_signals = sum(self.data['Signal'] == 1)
        sell_signals = sum(self.data['Signal'] == -1)
        
        print(f"\n共生成 {buy_signals} 个买入信号和 {sell_signals} 个卖出信号")
    
    def backtest_swing_strategy(self):
        """执行波段策略回测"""
        # 初始化持仓记录
        self.positions = pd.DataFrame(index=self.data.index, 
                                      columns=['Shares', 'Cash', 'Total_Asset', 'Reference_Price'])
        
        # 设置初始持仓
        initial_price = self.data['Close'].iloc[0]
        self.positions.iloc[0] = [
            self.initial_shares, 
            self.cash, 
            self.initial_shares * initial_price + self.cash,
            initial_price  # 初始参考价格
        ]
        
        # 记录实际持仓状态
        current_shares = self.initial_shares
        current_cash = self.cash
        
        # 打印初始状态
        print("\n波段交易执行明细:")
        print("-" * 120)
        print(f"{'日期':<12} {'价格':>10} {'参考价':>10} {'信号':>10} {'交易量':>10} {'交易金额':>15} {'持股':>8} {'现金':>15} {'总资产':>15}")
        print("-" * 120)
        print(f"{self.data.index[0].strftime('%Y-%m-%d'):<12} {initial_price:>10.2f} {self.reference_price:>10.2f} {'初始':>10} {'-':>10} {'-':>15} {current_shares:>8} {current_cash:>15,.2f} {current_shares * initial_price + current_cash:>15,.2f}")
        
        # 遍历回测区间
        for i in range(1, len(self.data)):
            date = self.data.index[i]
            market_price = self.data['Close'].iloc[i]
            signal = self.data['Signal'].iloc[i]
            
            # 初始化当前行的持仓数据
            shares = current_shares
            cash = current_cash
            ref_price = self.positions['Reference_Price'].iloc[i-1]
            
            # 处理交易信号
            signal_text = ''
            trade_amount = 0
            trade_volume = 0
            
            if signal == 1:  # 买入信号
                signal_text = '买入'
                trade_volume = self.trade_shares
                trade_amount = trade_volume * market_price
                
                # 执行买入
                if cash >= trade_amount:
                    cash -= trade_amount
                    shares += trade_volume
                    ref_price = market_price
                else:
                    # 资金不足，只买入能买的最大数量
                    max_shares = int(cash / market_price)
                    if max_shares > 0:
                        trade_volume = max_shares
                        trade_amount = trade_volume * market_price
                        cash -= trade_amount
                        shares += trade_volume
                        ref_price = market_price
                    else:
                        signal_text = '资金不足'
                        trade_volume = 0
                        trade_amount = 0
                
            elif signal == -1:  # 卖出信号
                signal_text = '卖出'
                trade_volume = self.trade_shares
                
                # 执行卖出
                if shares >= trade_volume:
                    trade_amount = trade_volume * market_price
                    cash += trade_amount
                    shares -= trade_volume
                    ref_price = market_price
                else:
                    # 持股不足，只卖出拥有的全部股票
                    if shares > 0:
                        trade_volume = shares
                        trade_amount = trade_volume * market_price
                        cash += trade_amount
                        shares = 0
                        ref_price = market_price
                    else:
                        signal_text = '持股不足'
                        trade_volume = 0
                        trade_amount = 0
            
            # 更新持仓记录
            self.positions.iloc[i] = [
                shares,
                cash,
                shares * market_price + cash,
                ref_price
            ]
            
            # 打印交易记录
            if signal != 0:
                trade_volume_display = f"{trade_volume}" if trade_volume > 0 else '-'
                trade_amount_display = f"${trade_amount:,.2f}" if trade_amount > 0 else '-'
                
                print(f"{date.strftime('%Y-%m-%d'):<12} {market_price:>10.2f} {ref_price:>10.2f} {signal_text:>10} {trade_volume_display:>10} {trade_amount_display:>15} {shares:>8} {cash:>15,.2f} {shares * market_price + cash:>15,.2f}")
            
            # 更新当前持仓状态
            current_shares = shares
            current_cash = cash
    
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
        print(f"初始资产: ${initial_value:,.2f} ({self.initial_shares}股 × ${first_price:.2f} + ${self.cash:,.2f}现金)")
        print(f"最终资产: ${final_value:,.2f}")
        final_position = self.positions['Shares'].iloc[-1]
        final_cash = self.positions['Cash'].iloc[-1]
        print(f"- 最终持股: {final_position} 股，价值: ${final_position * last_price:,.2f}")
        print(f"- 最终现金: ${final_cash:,.2f}")
        print(f"总收益率: {returns:.2f}%")
        
        # 交易统计
        buy_signals = sum(self.data['Signal'] == 1)
        sell_signals = sum(self.data['Signal'] == -1)
        
        print(f"交易统计:")
        print(f"- 买入交易: {buy_signals} 次")
        print(f"- 卖出交易: {sell_signals} 次")
        print(f"- 每次交易: {self.trade_shares}股")
        
        # 与买入持有策略比较
        buy_and_hold_value = self.initial_shares * last_price + self.cash
        print(f"\n买入持有策略收益率: {buy_and_hold_return:.2f}% (最终价值: ${buy_and_hold_value:,.2f})")
        print(f"波段策略 vs 买入持有: {returns - buy_and_hold_return:.2f}%")
    
    def run_strategy(self):
        """运行完整的波段策略"""
        print(f"开始回测 {self.symbol} 波段交易策略")
        print(f"初始持股: {self.initial_shares}股，波动阈值: {self.swing_threshold*100}%")
        print(f"每次交易股数: {self.trade_shares}股")
        print(f"回测时间范围: {self.start_date} 至 {self.end_date}\n")
        
        self.fetch_data()
        self.generate_signals()
        self.backtest_swing_strategy()
        self.display_summary()

# 使用示例
if __name__ == "__main__":
    trader = SwingTrader(
        symbol="AAPL",
        start_date="2023-05-01",
        end_date="2024-05-01",
        initial_shares=1000,
        trade_shares=100
    )
    trader.run_strategy() 