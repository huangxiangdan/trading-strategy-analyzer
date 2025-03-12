import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class OptionTrader:
    def __init__(self, symbol="AAPL", start_date="2022-01-01", end_date="2024-01-01", initial_shares=1000, premium_rate=0.05, option_shares=100):
        """初始化期权交易策略参数"""
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.positions = None
        self.cash = 100000  # 初始现金设为10万美元
        self.initial_shares = initial_shares  # 初始持股数
        self.premium_rate = premium_rate  # 权利金收益率，现在设为5%
        self.option_shares = option_shares  # 每次期权交易的股数
        self.option_transactions = []  # 记录期权交易
        self.swing_threshold = 0.10  # 10%的波动阈值，用于设定期权行权价格
        self.reference_price = None  # 参考价格，用于计算波动
        self.active_option = None  # 当前活跃的期权 (None, 'put', 'call')
        self.option_strike = None  # 当前期权的行权价
        self.option_start_date = None  # 期权开始日期
        
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
        print(f"每次期权交易股数: {self.option_shares}股")
        print(f"期权权利金率: {self.premium_rate*100}%")
        
        # 标记每月最后一个交易日
        self.data['YearMonth'] = self.data.index.to_period('M')
        self.data['IsLastDayOfMonth'] = False
        
        # 找出每月的最后一个交易日
        last_days = self.data.groupby('YearMonth').apply(lambda x: x.index[-1])
        for last_day in last_days:
            self.data.loc[last_day, 'IsLastDayOfMonth'] = True
        
        # 初始化交易信号和期权列
        self.data['Signal'] = 0  # 0=无信号, 1=卖出看跌期权, -1=卖出看涨期权
        self.data['OptionType'] = ''  # 'put', 'call', 或空字符串
        self.data['StrikePrice'] = 0.0
        self.data['Premium'] = 0.0
        self.data['IsExercised'] = False
        self.data['OptionShares'] = 0  # 期权涉及的股票数量
        
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
            
            # 如果当前没有活跃期权，检查是否达到波段阈值
            if self.active_option is None:
                # 价格下跌超过阈值，生成卖出看跌期权信号
                if price_change <= -self.swing_threshold:
                    self.data.loc[self.data.index[i], 'Signal'] = 1
                    # 看跌期权行权价应该是参考价格减去10%
                    put_strike = self.reference_price * (1 - self.swing_threshold)
                    premium = current_price * self.premium_rate
                    
                    self.data.loc[self.data.index[i], 'OptionType'] = 'put'
                    self.data.loc[self.data.index[i], 'StrikePrice'] = put_strike
                    self.data.loc[self.data.index[i], 'Premium'] = premium
                    self.data.loc[self.data.index[i], 'OptionShares'] = self.option_shares
                    
                    self.active_option = 'put'
                    self.option_strike = put_strike
                    self.option_start_date = current_date
                    
                    print(f"价格下跌触发 - 日期: {current_date.strftime('%Y-%m-%d')}, 当前价格: ${current_price:.2f}, "
                          f"参考价格: ${self.reference_price:.2f}, 变化: {price_change*100:.2f}%")
                    print(f"卖出看跌期权 - 行权价: ${put_strike:.2f}, 权利金: ${premium:.2f}, 股数: {self.option_shares}")
                    
                # 价格上涨超过阈值，生成卖出看涨期权信号
                elif price_change >= self.swing_threshold:
                    self.data.loc[self.data.index[i], 'Signal'] = -1
                    # 看涨期权行权价应该是参考价格加上10%
                    call_strike = self.reference_price * (1 + self.swing_threshold)
                    premium = current_price * self.premium_rate
                    
                    self.data.loc[self.data.index[i], 'OptionType'] = 'call'
                    self.data.loc[self.data.index[i], 'StrikePrice'] = call_strike
                    self.data.loc[self.data.index[i], 'Premium'] = premium
                    self.data.loc[self.data.index[i], 'OptionShares'] = self.option_shares
                    
                    self.active_option = 'call'
                    self.option_strike = call_strike
                    self.option_start_date = current_date
                    
                    print(f"价格上涨触发 - 日期: {current_date.strftime('%Y-%m-%d')}, 当前价格: ${current_price:.2f}, "
                          f"参考价格: ${self.reference_price:.2f}, 变化: {price_change*100:.2f}%")
                    print(f"卖出看涨期权 - 行权价: ${call_strike:.2f}, 权利金: ${premium:.2f}, 股数: {self.option_shares}")
            
            # 检查每月最后一个交易日是否有期权到期
            if self.active_option and self.data['IsLastDayOfMonth'].iloc[i]:
                # 检查期权是否被行权
                if self.active_option == 'put' and current_price <= self.option_strike:
                    # 看跌期权被行权
                    self.data.loc[self.data.index[i], 'IsExercised'] = True
                    print(f"看跌期权被行权 - 日期: {current_date.strftime('%Y-%m-%d')}, 当前价格: ${current_price:.2f}, "
                          f"行权价: ${self.option_strike:.2f}, 股数: {self.option_shares}")
                    # 更新参考价格
                    self.reference_price = self.option_strike
                    self.active_option = None
                    
                elif self.active_option == 'call' and current_price >= self.option_strike:
                    # 看涨期权被行权
                    self.data.loc[self.data.index[i], 'IsExercised'] = True
                    print(f"看涨期权被行权 - 日期: {current_date.strftime('%Y-%m-%d')}, 当前价格: ${current_price:.2f}, "
                          f"行权价: ${self.option_strike:.2f}, 股数: {self.option_shares}")
                    # 更新参考价格
                    self.reference_price = self.option_strike
                    self.active_option = None
                    
                else:
                    # 期权未被行权，重置活跃期权
                    print(f"期权未被行权 - 日期: {current_date.strftime('%Y-%m-%d')}, 当前价格: ${current_price:.2f}, "
                          f"行权价: ${self.option_strike:.2f}, 股数: {self.option_shares}")
                    self.active_option = None
        
        # 统计交易信号
        put_signals = sum(self.data['Signal'] == 1)
        call_signals = sum(self.data['Signal'] == -1)
        exercised = sum(self.data['IsExercised'])
        
        print(f"\n共生成 {put_signals} 个卖出看跌期权信号和 {call_signals} 个卖出看涨期权信号")
        print(f"其中 {exercised} 个期权被行权")
    
    def backtest_option_strategy(self):
        """执行期权策略回测"""
        # 初始化持仓记录
        self.positions = pd.DataFrame(index=self.data.index, 
                                      columns=['Shares', 'Cash', 'Total_Asset', 'Premium_Income', 'Reference_Price'])
        
        # 设置初始持仓
        initial_price = self.data['Close'].iloc[0]
        self.positions.iloc[0] = [
            self.initial_shares, 
            self.cash, 
            self.initial_shares * initial_price + self.cash,
            0,  # 初始无权利金收入
            initial_price  # 初始参考价格
        ]
        
        # 记录实际持仓状态
        current_shares = self.initial_shares
        current_cash = self.cash
        cumulative_premium = 0
        
        # 打印初始状态
        print("\n期权交易执行明细:")
        print("-" * 130)
        print(f"{'日期':<12} {'价格':>10} {'参考价':>10} {'信号':>10} {'期权类型':>10} {'行权价':>10} {'权利金':>10} {'期权股数':>10} {'行权状态':>10} {'持股':>8} {'现金':>15} {'总资产':>15}")
        print("-" * 130)
        print(f"{self.data.index[0].strftime('%Y-%m-%d'):<12} {initial_price:>10.2f} {self.reference_price:>10.2f} {'初始':>10} {'-':>10} {'-':>10} {'-':>10} {'-':>10} {'-':>10} {current_shares:>8} {current_cash:>15,.2f} {current_shares * initial_price + current_cash:>15,.2f}")
        
        # 遍历回测区间
        for i in range(1, len(self.data)):
            date = self.data.index[i]
            market_price = self.data['Close'].iloc[i]
            signal = self.data['Signal'].iloc[i]
            option_type = self.data['OptionType'].iloc[i]
            strike_price = self.data['StrikePrice'].iloc[i]
            premium = self.data['Premium'].iloc[i]
            option_shares = self.data['OptionShares'].iloc[i]
            is_exercised = self.data['IsExercised'].iloc[i]
            
            # 初始化当前行的持仓数据
            shares = current_shares
            cash = current_cash
            ref_price = self.positions['Reference_Price'].iloc[i-1]
            
            # 处理交易信号
            signal_text = ''
            
            if signal == 1:  # 卖出看跌期权
                signal_text = '卖出看跌'
                # 收取权利金
                premium_income = premium * option_shares
                cash += premium_income
                cumulative_premium += premium_income
                
            elif signal == -1:  # 卖出看涨期权
                signal_text = '卖出看涨'
                # 收取权利金
                premium_income = premium * option_shares
                cash += premium_income
                cumulative_premium += premium_income
            
            # 处理期权行权
            exercise_text = ''
            
            if is_exercised:
                if option_type == 'put':
                    exercise_text = '看跌行权'
                    ref_price = strike_price
                elif option_type == 'call':
                    exercise_text = '看涨行权'
                    ref_price = strike_price
            elif self.data['IsLastDayOfMonth'].iloc[i] and (self.data['OptionType'].iloc[i-1] != ''):
                exercise_text = '未行权'
            
            # 更新持仓记录
            self.positions.iloc[i] = [
                shares,
                cash,
                shares * market_price + cash,
                cumulative_premium,
                ref_price
            ]
            
            # 打印交易记录
            if signal != 0 or is_exercised or (self.data['IsLastDayOfMonth'].iloc[i] and (self.data['OptionType'].iloc[i-1] != '')):
                # 正确处理各种数据类型的格式化
                strike_display = f"{strike_price:.2f}" if strike_price > 0 else '-'
                premium_display = f"{premium:.2f}" if premium > 0 else '-'
                shares_display = f"{option_shares}" if option_shares > 0 else '-'
                
                print(f"{date.strftime('%Y-%m-%d'):<12} {market_price:>10.2f} {ref_price:>10.2f} {signal_text:>10} {option_type:>10} {strike_display:>10} {premium_display:>10} {shares_display:>10} {exercise_text:>10} {shares:>8} {cash:>15,.2f} {shares * market_price + cash:>15,.2f}")
            
            # 更新当前持仓状态
            current_shares = shares
            current_cash = cash
    
    def display_summary(self):
        """显示回测结果摘要"""
        print("\n" + "=" * 80)
        print("期权策略回测结果摘要")
        print("=" * 80)
        
        # 计算收益率
        initial_value = self.positions['Total_Asset'].iloc[0]
        final_value = self.positions['Total_Asset'].iloc[-1]
        total_premium = self.positions['Premium_Income'].iloc[-1]
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
        print(f"累计权利金收入: ${total_premium:,.2f} ({total_premium/initial_value*100:.2f}%)")
        
        # 交易统计
        put_signals = sum(self.data['Signal'] == 1)
        call_signals = sum(self.data['Signal'] == -1)
        exercised = sum(self.data['IsExercised'])
        
        print(f"交易统计:")
        print(f"- 卖出看跌期权: {put_signals} 次")
        print(f"- 卖出看涨期权: {call_signals} 次")
        print(f"- 期权被行权: {exercised} 次 ({exercised/(put_signals+call_signals)*100 if put_signals+call_signals > 0 else 0:.2f}%)")
        print(f"- 每次期权交易: {self.option_shares}股")
        print(f"- 期权权利金率: {self.premium_rate*100:.2f}%")
        
        # 与买入持有策略比较
        buy_and_hold_value = self.initial_shares * last_price + self.cash
        print(f"\n买入持有策略收益率: {buy_and_hold_return:.2f}% (最终价值: ${buy_and_hold_value:,.2f})")
        print(f"期权策略 vs 买入持有: {returns - buy_and_hold_return:.2f}%")
    
    def run_strategy(self):
        """运行完整的期权策略"""
        print(f"开始回测 {self.symbol} 月度期权策略")
        print(f"初始持股: {self.initial_shares}股，权利金率: {self.premium_rate*100}%，波动阈值: {self.swing_threshold*100}%")
        print(f"每次期权交易股数: {self.option_shares}股")
        print(f"回测时间范围: {self.start_date} 至 {self.end_date}\n")
        
        self.fetch_data()
        self.generate_signals()
        self.backtest_option_strategy()
        self.display_summary()

# 使用示例
if __name__ == "__main__":
    trader = OptionTrader(
        symbol="AAPL",
        start_date="2023-05-01",
        end_date="2024-05-01",
        initial_shares=1000,
        premium_rate=0.05,  # 5%权利金率
        option_shares=100
    )
    trader.run_strategy() 