import yfinance as yf
import pandas as pd

# 获取AAPL在2023年1月26日至2023年12月31日期间的数据
data = yf.download("AAPL", start="2023-01-26", end="2023-12-31")

# 打印基本信息
print(f"数据时间范围: {data.index[0].strftime('%Y-%m-%d')} 至 {data.index[-1].strftime('%Y-%m-%d')}")
print(f"总交易日数: {len(data)}")

# 获取价格数据
start_close = data['Close'].iloc[0]
end_close = data['Close'].iloc[-1]
print(f"起始日收盘价: ${start_close:.2f}")
print(f"结束日收盘价: ${end_close:.2f}")
print(f"期间价格变化: {((end_close - start_close) / start_close * 100):.2f}%")

# 计算最高价和最低价
max_price = data['High'].max()
min_price = data['Low'].min()
print(f"\n期间最高价: ${max_price:.2f}")
print(f"期间最低价: ${min_price:.2f}")
print(f"最大价格波动: {((max_price - min_price) / min_price * 100):.2f}%")

# 分析是否有可能触发信号
reference_price = 142.31  # 最后一次交易价格 (2023-01-26)
buy_threshold = reference_price * 0.9  # 下跌10%触发买入
sell_threshold = reference_price * 1.1  # 上涨10%触发卖出

print(f"\n基于最后交易价格 ${reference_price:.2f}:")
print(f"买入信号阈值 (下跌10%): ${buy_threshold:.2f}")
print(f"卖出信号阈值 (上涨10%): ${sell_threshold:.2f}")

# 检查是否有价格达到阈值
min_price_after_trade = min_price
max_price_after_trade = max_price

print(f"\n最低价 ${min_price_after_trade:.2f} {'低于' if min_price_after_trade <= buy_threshold else '未低于'} 买入阈值 ${buy_threshold:.2f}")
print(f"最高价 ${max_price_after_trade:.2f} {'高于' if max_price_after_trade >= sell_threshold else '未高于'} 卖出阈值 ${sell_threshold:.2f}") 