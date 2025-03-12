import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

print("开始测试yfinance库...")

# 设置日期范围
end_date = datetime.today()
start_date = end_date - timedelta(days=30)  # 只获取最近30天的数据

# 尝试获取AAPL数据
print(f"尝试获取AAPL从{start_date.strftime('%Y-%m-%d')}到{end_date.strftime('%Y-%m-%d')}的数据")
try:
    ticker = yf.Ticker("AAPL")
    data = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    
    if data.empty:
        print("获取的数据为空")
    else:
        print(f"成功获取到{len(data)}条数据记录")
        print("\n前5条数据:")
        print(data.head())
        
        print("\n数据统计信息:")
        print(data.describe())
except Exception as e:
    print(f"获取数据时出错: {e}")

# 尝试获取其他股票代码的数据进行对比
print("\n尝试获取MSFT(微软)的数据:")
try:
    ticker = yf.Ticker("MSFT")
    data = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    
    if data.empty:
        print("获取的MSFT数据为空")
    else:
        print(f"成功获取到{len(data)}条MSFT数据记录")
except Exception as e:
    print(f"获取MSFT数据时出错: {e}")

print("\n测试完成") 