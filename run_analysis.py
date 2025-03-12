import pandas as pd
import numpy as np
import alpha_vantage_api as av
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 配置Alpha Vantage API密钥
ALPHA_VANTAGE_API_KEY = "7H89Q1YFCR6FW9IB"

# 导入策略类
from swing_strategy import SwingTrader
from option_strategy import OptionTrader

print("========== 苹果股票波段策略与期权策略对比分析 ==========")

# 分析参数设置
symbol = "AAPL"
start_date = "2020-01-01"
end_date = "2021-12-31"
initial_shares = 1000
trade_shares = 100
swing_threshold = 0.10
premium_rate = 0.05

print(f"分析参数:")
print(f"- 股票代码: {symbol}")
print(f"- 分析时间范围: {start_date} 至 {end_date}")
print(f"- 初始持股: {initial_shares}股")
print(f"- 每次交易: {trade_shares}股")
print(f"- 波动阈值: {swing_threshold*100}%")
print(f"- 期权权利金率: {premium_rate*100}%")
print("-" * 50)

# 将日期字符串转换为日期对象，然后再转回字符串，确保格式一致
try:
    # 解析日期字符串为日期对象
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # 确保日期在有效范围内
    latest_safe_date = datetime(2024, 1, 1).date()
    adjusted_end_date_obj = min(end_date_obj, latest_safe_date)
    
    # 转回字符串格式
    start_date_str = start_date_obj.strftime("%Y-%m-%d")
    adjusted_end_date_str = adjusted_end_date_obj.strftime("%Y-%m-%d")
    
    # 获取股票数据
    print(f"正在获取{symbol}股票数据...")
    api = av.AlphaVantageAPI(api_key=ALPHA_VANTAGE_API_KEY)
    stock_data = api.get_stock_data(symbol, start_date_str, adjusted_end_date_str)
    
    if stock_data.empty:
        print(f"错误: 无法获取{symbol}的数据，请检查股票代码或日期范围。")
        exit(1)
        
    print(f"成功获取 {len(stock_data)} 个交易日的数据")
    print(f"首日价格: ${stock_data['Close'].iloc[0]:.2f}")
    print(f"末日价格: ${stock_data['Close'].iloc[-1]:.2f}")
    price_change = ((stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[0]) / stock_data['Close'].iloc[0] * 100)
    print(f"期间价格变化: {price_change:.2f}%")
    print("-" * 50)
    
except Exception as e:
    print(f"获取股票数据时出错: {e}")
    print(f"注意: Alpha Vantage API有频率限制，如果频繁请求可能需要等待或使用另一个API密钥。")
    exit(1)

# 运行波段交易策略
print("正在运行波段交易策略...")
try:
    swing_trader = SwingTrader(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_shares=initial_shares,
        trade_shares=trade_shares
    )
    swing_trader.data = stock_data.copy()
    swing_trader.reference_price = stock_data['Close'].iloc[0]
    swing_trader.swing_threshold = swing_threshold
    swing_trader.initial_asset_value = initial_shares * stock_data['Close'].iloc[0] + swing_trader.cash
    
    # 运行策略
    swing_trader.generate_signals()
    swing_trader.backtest_swing_strategy()
    
    # 显示波段策略结果
    swing_initial_value = swing_trader.positions['Total_Asset'].iloc[0]
    swing_final_value = swing_trader.positions['Total_Asset'].iloc[-1]
    swing_returns = (swing_final_value - swing_initial_value) / swing_initial_value * 100
    
    buy_signals = sum(swing_trader.data['Signal'] == 1)
    sell_signals = sum(swing_trader.data['Signal'] == -1)
    
    print(f"波段策略结果:")
    print(f"- 初始资产: ${swing_initial_value:,.2f}")
    print(f"- 最终资产: ${swing_final_value:,.2f}")
    print(f"- 总收益率: {swing_returns:.2f}%")
    print(f"- 买入交易: {buy_signals}次")
    print(f"- 卖出交易: {sell_signals}次")
    
except Exception as e:
    print(f"运行波段策略时出错: {e}")

print("-" * 50)

# 运行期权策略
print("正在运行期权交易策略...")
try:
    option_trader = OptionTrader(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_shares=initial_shares,
        premium_rate=premium_rate,
        option_shares=trade_shares
    )
    option_trader.data = stock_data.copy()
    option_trader.reference_price = stock_data['Close'].iloc[0]
    option_trader.swing_threshold = swing_threshold
    option_trader.initial_asset_value = initial_shares * stock_data['Close'].iloc[0] + option_trader.cash
    
    # 标记每月最后一个交易日
    option_trader.data['YearMonth'] = option_trader.data.index.to_period('M')
    option_trader.data['IsLastDayOfMonth'] = False
    
    # 找出每月的最后一个交易日
    last_days = option_trader.data.groupby('YearMonth').apply(lambda x: x.index[-1])
    for last_day in last_days:
        option_trader.data.loc[last_day, 'IsLastDayOfMonth'] = True
    
    # 初始化交易信号和期权列
    option_trader.data['Signal'] = 0  # 0=无信号, 1=卖出看跌期权, -1=卖出看涨期权
    option_trader.data['OptionType'] = ''  # 'put', 'call', 或空字符串
    option_trader.data['StrikePrice'] = 0.0
    option_trader.data['Premium'] = 0.0
    option_trader.data['IsExercised'] = False
    option_trader.data['OptionShares'] = 0  # 期权涉及的股票数量
    
    # 运行策略
    option_trader.generate_signals()
    option_trader.backtest_option_strategy()
    
    # 显示期权策略结果
    option_initial_value = option_trader.positions['Total_Asset'].iloc[0]
    option_final_value = option_trader.positions['Total_Asset'].iloc[-1]
    total_premium = option_trader.positions['Premium_Income'].iloc[-1]
    option_returns = (option_final_value - option_initial_value) / option_initial_value * 100
    
    put_signals = sum(option_trader.data['Signal'] == 1)
    call_signals = sum(option_trader.data['Signal'] == -1)
    exercised = sum(option_trader.data['IsExercised'])
    
    print(f"期权策略结果:")
    print(f"- 初始资产: ${option_initial_value:,.2f}")
    print(f"- 最终资产: ${option_final_value:,.2f}")
    print(f"- 总收益率: {option_returns:.2f}%")
    print(f"- 累计权利金: ${total_premium:,.2f} ({total_premium/option_initial_value*100:.2f}%)")
    print(f"- 卖出看跌期权: {put_signals}次")
    print(f"- 卖出看涨期权: {call_signals}次")
    print(f"- 期权被行权: {exercised}次 ({exercised/(put_signals+call_signals)*100 if put_signals+call_signals > 0 else 0:.2f}%)")
    
except Exception as e:
    print(f"运行期权策略时出错: {e}")

print("-" * 50)

# 计算买入持有策略
first_price = stock_data['Close'].iloc[0]
last_price = stock_data['Close'].iloc[-1]
buy_and_hold_return = (last_price / first_price - 1) * 100
buy_and_hold_value = initial_shares * last_price + 100000

print(f"买入持有策略结果:")
print(f"- 初始资产: ${swing_initial_value:,.2f}")
print(f"- 最终资产: ${buy_and_hold_value:,.2f}")
print(f"- 总收益率: {buy_and_hold_return:.2f}%")

print("-" * 50)

# 策略对比
print("策略对比分析:")
print(f"1. 波段策略收益率: {swing_returns:.2f}% (相对买入持有: {swing_returns - buy_and_hold_return:.2f}%)")
print(f"2. 期权策略收益率: {option_returns:.2f}% (相对买入持有: {option_returns - buy_and_hold_return:.2f}%)")
print(f"3. 买入持有收益率: {buy_and_hold_return:.2f}%")

print("-" * 50)
better_strategy = "波段策略" if swing_returns > option_returns else "期权策略"
diff = abs(swing_returns - option_returns)

print(f"分析结论:")
print(f"1. 在回测期间（{start_date} 至 {end_date}），{better_strategy}表现更好，高出{diff:.2f}个百分点")

if swing_returns > buy_and_hold_return and option_returns > buy_and_hold_return:
    print("2. 两种策略均优于买入持有策略")
elif swing_returns > buy_and_hold_return:
    print("2. 波段策略优于买入持有策略，但期权策略表现不及买入持有")
elif option_returns > buy_and_hold_return:
    print("2. 期权策略优于买入持有策略，但波段策略表现不及买入持有")
else:
    print("2. 两种策略均不如买入持有策略")

print(f"3. 累计权利金收入占初始资产的{total_premium/option_initial_value*100:.2f}%，是期权策略的主要收益来源")
print("========== 分析完成 ==========") 