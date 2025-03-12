import requests
import pandas as pd
import time
from datetime import datetime, timedelta, date

class AlphaVantageAPI:
    """
    Alpha Vantage API 工具类
    用于获取股票历史数据，替代yfinance
    """
    
    def __init__(self, api_key='demo'):
        """
        初始化API工具类
        
        参数:
        api_key: Alpha Vantage API密钥，默认为'demo'（仅适用于小规模测试）
        """
        self.api_key = api_key
        self.base_url = 'https://www.alphavantage.co/query'
        
    def get_daily_adjusted(self, symbol, outputsize='full'):
        """
        获取股票的每日价格数据
        
        参数:
        symbol: 股票代码，例如'AAPL'
        outputsize: 'compact'获取最近100个交易日数据，'full'获取所有历史数据
        
        返回:
        DataFrame对象，包含日期索引和OHLCV数据
        """
        params = {
            'function': 'TIME_SERIES_DAILY',  # 使用标准接口替代高级接口
            'symbol': symbol,
            'outputsize': outputsize,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                # 转换JSON数据为DataFrame
                df = pd.DataFrame(data['Time Series (Daily)']).T
                
                # 重命名列 - 调整列名以匹配响应格式
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                
                # 转换类型
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col])
                
                # 转换索引为日期类型并排序
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                # 添加缺失的列以匹配yfinance格式
                df['Adj Close'] = df['Close']  # 使用收盘价作为调整后收盘价
                df['Dividends'] = 0.0  # 没有股息数据
                df['Stock Splits'] = 0.0  # 没有拆分数据
                
                return df
            else:
                if 'Error Message' in data:
                    print(f"API错误: {data['Error Message']}")
                elif 'Note' in data:
                    print(f"API限制: {data['Note']}")
                else:
                    print(f"未知错误: {data}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"获取Alpha Vantage数据时出错: {e}")
            return pd.DataFrame()
    
    def get_stock_data(self, symbol, start_date=None, end_date=None):
        """
        获取特定日期范围内的股票数据（接口与yfinance兼容）
        
        参数:
        symbol: 股票代码，例如'AAPL'
        start_date: 开始日期，格式为'YYYY-MM-DD'或datetime对象
        end_date: 结束日期，格式为'YYYY-MM-DD'或datetime对象
        
        返回:
        DataFrame对象，包含OHLCV数据
        """
        # 转换日期为字符串格式
        if start_date:
            if isinstance(start_date, datetime) or isinstance(start_date, date):
                start_date = start_date.strftime('%Y-%m-%d')
        if end_date:
            if isinstance(end_date, datetime) or isinstance(end_date, date):
                end_date = end_date.strftime('%Y-%m-%d')
            
        # 获取股票数据
        df = self.get_daily_adjusted(symbol)
        
        # 如果数据为空，返回空DataFrame
        if df.empty:
            return df
            
        # 按日期范围过滤
        if start_date:
            df = df.loc[df.index >= start_date]
        if end_date:
            df = df.loc[df.index <= end_date]
        
        return df
        
    def get_ticker_info(self, symbol):
        """
        获取股票的概览信息
        
        参数:
        symbol: 股票代码，例如'AAPL'
        
        返回:
        包含公司概览信息的字典
        """
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            return data
        except Exception as e:
            print(f"获取股票信息时出错: {e}")
            return {}
    
    # 模拟yfinance.Ticker类的接口
    class Ticker:
        def __init__(self, symbol, api_key='demo'):
            self.symbol = symbol
            self.api = AlphaVantageAPI(api_key)
            self._info = None
            
        @property
        def info(self):
            if self._info is None:
                self._info = self.api.get_ticker_info(self.symbol)
            return self._info
            
        def history(self, start=None, end=None, period=None, interval='1d'):
            """模拟yfinance的history方法"""
            if interval != '1d':
                print(f"警告: Alpha Vantage API目前只支持日级别数据，忽略interval={interval}")
                
            if period:
                # 处理period参数
                today = datetime.now()
                if period == '1d':
                    start = today - timedelta(days=1)
                elif period == '5d':
                    start = today - timedelta(days=5)
                elif period == '1mo':
                    start = today - timedelta(days=30)
                elif period == '3mo':
                    start = today - timedelta(days=90)
                elif period == '6mo':
                    start = today - timedelta(days=180)
                elif period == '1y':
                    start = today - timedelta(days=365)
                elif period == '2y':
                    start = today - timedelta(days=730)
                elif period == '5y':
                    start = today - timedelta(days=1825)
                elif period == '10y':
                    start = today - timedelta(days=3650)
                    
            return self.api.get_stock_data(self.symbol, start, end)

# 提供类似yfinance的接口函数
def Ticker(symbol, api_key='demo'):
    return AlphaVantageAPI.Ticker(symbol, api_key)

def download(ticker, start=None, end=None, period=None, interval='1d', api_key='demo'):
    """模拟yfinance.download函数"""
    av_api = AlphaVantageAPI(api_key)
    
    if period:
        # 处理period参数
        today = datetime.now()
        if period == '1d':
            start = today - timedelta(days=1)
        elif period == '5d':
            start = today - timedelta(days=5)
        elif period == '1mo':
            start = today - timedelta(days=30)
        elif period == '3mo':
            start = today - timedelta(days=90)
        elif period == '6mo':
            start = today - timedelta(days=180)
        elif period == '1y':
            start = today - timedelta(days=365)
        elif period == '2y':
            start = today - timedelta(days=730)
        elif period == '5y':
            start = today - timedelta(days=1825)
        elif period == '10y':
            start = today - timedelta(days=3650)
            
    return av_api.get_stock_data(ticker, start, end) 