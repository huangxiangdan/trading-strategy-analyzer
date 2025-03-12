import yfinance as yf
import pandas as pd

print("测试基本的yfinance功能...")

# 测试获取基本信息
try:
    msft = yf.Ticker("MSFT")
    print("公司信息:")
    print(f"公司名称: {msft.info.get('shortName', 'N/A')}")
    print(f"行业: {msft.info.get('industry', 'N/A')}")
    print(f"当前价格: {msft.info.get('currentPrice', 'N/A')}")
    print(f"52周最高价: {msft.info.get('fiftyTwoWeekHigh', 'N/A')}")
    print(f"52周最低价: {msft.info.get('fiftyTwoWeekLow', 'N/A')}")
except Exception as e:
    print(f"获取公司信息失败: {e}")

# 测试获取当前股价
try:
    print("\n尝试获取当前股价...")
    tickers = yf.Tickers('AAPL MSFT GOOG')
    print(tickers.tickers['AAPL'].history(period='1d'))
    print(tickers.tickers['MSFT'].history(period='1d'))
    print(tickers.tickers['GOOG'].history(period='1d'))
except Exception as e:
    print(f"获取当前股价失败: {e}")

# 测试获取一周的数据
try:
    print("\n尝试获取过去一周的数据...")
    data = yf.download("AAPL", period="1wk")
    print(data)
except Exception as e:
    print(f"获取一周数据失败: {e}")

print("\n测试完成") 