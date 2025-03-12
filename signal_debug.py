import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# 获取AAPL数据
data = yf.download("AAPL", start="2023-01-01", end="2023-12-31")

# 手动打印数据分析
print(f"获取了{len(data)}个交易日的数据")
print(f"开始日期: {data.index[0].strftime('%Y-%m-%d')}")
print(f"结束日期: {data.index[-1].strftime('%Y-%m-%d')}")

# 关键价格
ref_price = 142.31  # 2023-01-26的收盘价
sell_threshold = ref_price * 1.1
buy_threshold = ref_price * 0.9

print(f"\n参考价格: ${ref_price}")
print(f"卖出阈值 (10%上涨): ${sell_threshold:.2f}")

# 找出超过阈值的日期
above_threshold = []
for i in range(len(data)):
    date = data.index[i]
    close = float(data['Close'].iloc[i])  # 转换为float
    if close > sell_threshold:
        above_threshold.append((date, close))

print(f"\n收盘价超过卖出阈值的天数: {len(above_threshold)}")

if above_threshold:
    first_date, first_price = above_threshold[0]
    print(f"首次超过阈值日期: {first_date.strftime('%Y-%m-%d')}")
    print(f"首次超过阈值收盘价: ${first_price:.2f}")
    print(f"相对于参考价格涨幅: {(first_price - ref_price) / ref_price * 100:.2f}%")
    
    # 检查前10个超过阈值的日期
    print("\n前10个超过阈值的日期:")
    for i, (date, price) in enumerate(above_threshold[:10]):
        change = (price - ref_price) / ref_price * 100
        print(f"{date.strftime('%Y-%m-%d')}: ${price:.2f} ({change:.2f}%)")
        
# 检查特定日期的价格
specific_dates = [
    datetime(2023, 2, 1),
    datetime(2023, 3, 1),
    datetime(2023, 4, 3),
    datetime(2023, 5, 1),
    datetime(2023, 6, 1),
    datetime(2023, 7, 3),
    datetime(2023, 8, 1),
    datetime(2023, 9, 1),
    datetime(2023, 10, 2),
    datetime(2023, 11, 1),
    datetime(2023, 12, 1)
]

print("\n各月价格检查:")
for date in specific_dates:
    closest_idx = data.index.searchsorted(date)
    if closest_idx < len(data):
        closest_date = data.index[closest_idx]
        price = float(data['Close'].iloc[closest_idx])  # 转换为float
        change = (price - ref_price) / ref_price * 100
        status = "✓" if price > sell_threshold else "✗"
        print(f"{closest_date.strftime('%Y-%m-%d')}: ${price:.2f} ({change:+.2f}%) {status}") 