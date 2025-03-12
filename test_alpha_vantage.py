import alpha_vantage_api as av
import pandas as pd
from datetime import datetime, timedelta

# 配置API密钥
API_KEY = "7H89Q1YFCR6FW9IB"

print("测试Alpha Vantage API...")

# 测试获取AAPL股票数据
symbol = "AAPL"
end_date = "2021-12-31"
start_date = "2021-12-01"  # 获取一个月的数据，避免超出API限制

print(f"尝试获取{symbol}从{start_date}到{end_date}的数据")

try:
    # 初始化API
    api = av.AlphaVantageAPI(api_key=API_KEY)
    
    # 获取股票数据
    data = api.get_stock_data(symbol, start_date, end_date)
    
    if data.empty:
        print("获取的数据为空，请检查API密钥是否正确或日期范围是否有效")
    else:
        print(f"成功获取到{len(data)}条数据记录")
        print("\n数据预览:")
        print(data.head())
        
        # 显示数据统计信息
        print("\n数据统计信息:")
        print(f"日期范围: {data.index.min()} 至 {data.index.max()}")
        print(f"开盘价范围: ${data['Open'].min():.2f} - ${data['Open'].max():.2f}")
        print(f"收盘价范围: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
        
        # 保存到CSV文件，以便后续使用
        data.to_csv(f"{symbol}_data.csv")
        print(f"\n数据已保存到 {symbol}_data.csv 文件")
except Exception as e:
    print(f"测试失败: {e}")

# 测试模拟yfinance接口
print("\n测试模拟yfinance接口...")
try:
    # 使用Ticker类
    ticker = av.Ticker(symbol, api_key=API_KEY)
    ticker_data = ticker.history(start=start_date, end=end_date)
    
    if not ticker_data.empty:
        print("Ticker接口测试成功")
    
    # 使用download函数
    download_data = av.download(symbol, start=start_date, end=end_date, api_key=API_KEY)
    
    if not download_data.empty:
        print("download函数测试成功")
        
except Exception as e:
    print(f"接口测试失败: {e}")

print("\n测试完成") 