import yfinance as yf
import pandas as pd
from datetime import datetime

# 获取AAPL在2023年1月26日至2023年12月31日期间的数据
data = yf.download("AAPL", start="2023-01-26", end="2023-12-31")

# 设置参考价格
reference_price = 142.31  # 2023年1月26日卖出价格
buy_threshold = reference_price * 0.9  # 下跌10%触发买入
sell_threshold = reference_price * 1.1  # 上涨10%触发卖出

print(f"参考价格: ${reference_price:.2f}")
print(f"买入阈值: ${buy_threshold:.2f}")
print(f"卖出阈值: ${sell_threshold:.2f}")
print(f"数据范围: {data.index[0].strftime('%Y-%m-%d')} 至 {data.index[-1].strftime('%Y-%m-%d')}")
print(f"总交易日数: {len(data)}")

# 计算每天的相对变化
data['Change_Pct'] = ((data['Close'] - reference_price) / reference_price * 100).round(2)

# 找出所有可能触发卖出信号的日期
sell_signal_days = data[data['Close'] >= sell_threshold]
print(f"\n收盘价超过卖出阈值的天数: {len(sell_signal_days)}")

# 打印所有可能触发卖出信号的日期
if len(sell_signal_days) > 0:
    print("\n可能的卖出信号日期（仅显示前10条）:")
    print(f"{'日期':<12} {'收盘价':>10} {'相对变化':>12}")
    print("-" * 40)
    
    # 仅显示前10条记录
    for i, (date, row) in enumerate(sell_signal_days.iterrows()):
        if i >= 10:
            print(f"... 还有 {len(sell_signal_days) - 10} 条记录 ...")
            break
        print(f"{date.strftime('%Y-%m-%d')} ${row['Close']:.2f} {row['Change_Pct']:>11.2f}%")

# 找出第一个超过卖出阈值的日期
if len(sell_signal_days) > 0:
    first_signal_date = sell_signal_days.index[0]
    days_since_ref = (first_signal_date - data.index[0]).days
    print(f"\n首次收盘价超过卖出阈值: {first_signal_date.strftime('%Y-%m-%d')}")
    print(f"首次超过阈值的收盘价: ${sell_signal_days['Close'].iloc[0]:.2f}")
    print(f"相对于参考价格的变化: {sell_signal_days['Change_Pct'].iloc[0]:.2f}%")
    print(f"从参考日期起间隔: {days_since_ref} 天")
    
    # 打印首次超过阈值前后5天的价格
    signal_idx = data.index.get_loc(first_signal_date)
    start_idx = max(0, signal_idx - 5)
    end_idx = min(len(data), signal_idx + 5)
    
    print("\n突破前后价格走势:")
    print(f"{'日期':<12} {'收盘价':>10} {'相对变化':>12}")
    print("-" * 40)
    
    for i in range(start_idx, end_idx + 1):
        date = data.index[i]
        close = data['Close'].iloc[i]
        change = data['Change_Pct'].iloc[i]
        marker = " *" if i == signal_idx else ""
        print(f"{date.strftime('%Y-%m-%d')} ${close:.2f} {change:>11.2f}%{marker}")

# 检查关键价格区间分布
price_ranges = {
    f"<= {buy_threshold:.2f}": len(data[data['Close'] <= buy_threshold]),
    f"{buy_threshold:.2f} - {reference_price:.2f}": len(data[(data['Close'] > buy_threshold) & (data['Close'] < reference_price)]),
    f"{reference_price:.2f} - {sell_threshold:.2f}": len(data[(data['Close'] >= reference_price) & (data['Close'] < sell_threshold)]),
    f">= {sell_threshold:.2f}": len(data[data['Close'] >= sell_threshold])
}

print("\n价格区间分布:")
for range_name, count in price_ranges.items():
    print(f"{range_name}: {count} 天 ({count/len(data)*100:.1f}%)") 