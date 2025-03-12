import streamlit as st
import pandas as pd
import numpy as np
# 替换yfinance导入为alpha_vantage_api
import alpha_vantage_api as av
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
from io import BytesIO
import base64
import yfinance as yf
import os
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取 Alpha Vantage API 密钥
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
if not ALPHA_VANTAGE_API_KEY:
    st.error("请设置环境变量 ALPHA_VANTAGE_API_KEY")
    st.stop()

# 导入策略类
from swing_strategy import SwingTrader
from option_strategy import OptionTrader

# 设置页面配置
st.set_page_config(
    page_title="交易策略分析工具",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("📊 交易策略分析工具")
st.markdown("### 波段交易与期权策略回测比较")

# 侧边栏设置
st.sidebar.header("策略参数设置")

# 添加缓存管理
with st.sidebar.expander("缓存管理"):
    st.write("数据缓存可以加快加载速度，避免频繁调用API")
    cache_dir = "cache"
    if os.path.exists(cache_dir):
        cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.pkl')]
        if cache_files:
            st.write(f"当前缓存文件数：{len(cache_files)}个")
            total_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in cache_files)
            st.write(f"缓存总大小：{total_size / 1024 / 1024:.2f} MB")
            if st.button("清理过期缓存"):
                clear_stock_cache()
                st.success("已清理过期缓存！")
            if st.button("清理所有缓存"):
                for f in cache_files:
                    try:
                        os.remove(os.path.join(cache_dir, f))
                    except Exception as e:
                        st.error(f"删除缓存文件失败：{str(e)}")
                st.success("已清理所有缓存！")
        else:
            st.write("当前没有缓存文件")

# 股票代码输入
symbol = st.sidebar.text_input("股票代码（例如：AAPL, MSFT, NVDA）", "AAPL")

# 日期范围选择
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "开始日期",
        datetime(2023, 1, 1)  # 修改为2023年1月1日
    )
with col2:
    end_date = st.date_input(
        "结束日期",
        datetime(2024, 1, 1)  # 修改为2024年1月1日
    )

# 交易参数设置
initial_shares = st.sidebar.number_input("初始持股数量", min_value=100, max_value=10000, value=1000, step=100)
trade_shares = st.sidebar.number_input("每次交易股数", min_value=10, max_value=1000, value=100, step=10)
swing_threshold = st.sidebar.slider("波动阈值 (%)", min_value=5, max_value=20, value=10, step=1) / 100
premium_rate = st.sidebar.slider("期权权利金率 (%)", min_value=1, max_value=10, value=5, step=1) / 100

# 策略选择
strategy_type = st.sidebar.radio(
    "选择要查看的策略",
    ["两种策略对比", "仅波段策略", "仅期权策略"]
)

# 运行按钮
run_button = st.sidebar.button("运行策略分析")

# 下载Excel报告
def get_excel_download_link(df, filename="交易策略回测报告.xlsx"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='回测数据')
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">下载Excel报告</a>'
    return href

# 函数：获取股票数据
@st.cache_data
def get_stock_data(symbol, start_date, end_date):
    """
    使用Alpha Vantage API获取股票的历史数据（包含复权价格）
    添加本地缓存功能，避免频繁调用API
    """
    try:
        # 构建缓存文件名
        cache_dir = "cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        cache_file = f"{cache_dir}/{symbol}_{start_date}_{end_date}.pkl"
        
        # 检查缓存是否存在且未过期（7天）
        if os.path.exists(cache_file):
            file_modified_time = os.path.getmtime(cache_file)
            if (time.time() - file_modified_time) < 7 * 24 * 3600:  # 7天内的缓存有效
                try:
                    data = pd.read_pickle(cache_file)
                    print(f"从缓存加载 {symbol} 的数据")
                    return data
                except Exception as e:
                    print(f"读取缓存文件失败：{str(e)}")
                    # 如果读取缓存失败，继续获取新数据
        
        # 如果没有缓存或缓存已过期，从API获取数据
        print(f"从API获取 {symbol} 的数据")
        api = av.AlphaVantageAPI(api_key=ALPHA_VANTAGE_API_KEY)
        data = api.get_stock_data(symbol, start_date, end_date)
        
        if data.empty:
            st.error(f"无法获取 {symbol} 的数据，请检查股票代码是否正确。")
            return None
            
        # 确保数据包含所需的列
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required_columns):
            st.error(f"获取的数据缺少必要的列：{required_columns}")
            return None
            
        # 添加YearMonth列用于月度统计
        data['YearMonth'] = data.index.to_period('M')
        
        # 保存到缓存
        try:
            data.to_pickle(cache_file)
            print(f"数据已缓存到 {cache_file}")
        except Exception as e:
            print(f"保存缓存文件失败：{str(e)}")
        
        return data
        
    except Exception as e:
        st.error(f"获取数据时发生错误：{str(e)}")
        return None

# 添加缓存清理函数
def clear_stock_cache():
    """清理过期的股票数据缓存（超过7天）"""
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        return
        
    current_time = time.time()
    for cache_file in os.listdir(cache_dir):
        if cache_file.endswith('.pkl'):
            cache_path = os.path.join(cache_dir, cache_file)
            file_modified_time = os.path.getmtime(cache_path)
            if (current_time - file_modified_time) > 7 * 24 * 3600:  # 7天后过期
                try:
                    os.remove(cache_path)
                    print(f"已删除过期缓存：{cache_file}")
                except Exception as e:
                    print(f"删除过期缓存失败：{str(e)}")

# 函数：创建价格图表
def plot_price_chart(data, positions=None, title="股票价格走势"):
    fig = go.Figure()
    
    # 添加股票价格线
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Close'],
        mode='lines',
        name='收盘价',
        line=dict(color='royalblue', width=2)
    ))
    
    # 如果有交易记录，添加买入卖出点
    if positions is not None and 'Signal' in positions.columns:
        # 买入点（波段策略中 Signal=1，期权策略中 Signal=1 表示卖出看跌期权）
        buy_signals = positions[positions['Signal'] == 1]
        if not buy_signals.empty:
            fig.add_trace(go.Scatter(
                x=buy_signals.index,
                y=buy_signals['Close'],
                mode='markers',
                name='买入信号/卖出看跌期权',
                marker=dict(symbol='triangle-up', size=12, color='green', line=dict(width=1, color='darkgreen'))
            ))
        
        # 卖出点（波段策略中 Signal=-1，期权策略中 Signal=-1 表示卖出看涨期权）
        sell_signals = positions[positions['Signal'] == -1]
        if not sell_signals.empty:
            fig.add_trace(go.Scatter(
                x=sell_signals.index,
                y=sell_signals['Close'],
                mode='markers',
                name='卖出信号/卖出看涨期权',
                marker=dict(symbol='triangle-down', size=12, color='red', line=dict(width=1, color='darkred'))
            ))
    
    # 添加期权行权点标注
    if positions is not None and 'IsExercised' in positions.columns:
        # 找出所有被行权的点
        exercised_points = positions[positions['IsExercised'] == True]
        if not exercised_points.empty:
            # 找出看涨期权行权点（Signal=-1 的行权点）
            call_exercised = exercised_points[exercised_points['Signal'] == -1]
            if not call_exercised.empty:
                fig.add_trace(go.Scatter(
                    x=call_exercised.index,
                    y=call_exercised['Close'],
                    mode='markers',
                    name='看涨期权行权',
                    marker=dict(symbol='star', size=14, color='orange', line=dict(width=1, color='darkorange'))
                ))
            
            # 找出看跌期权行权点（Signal=1 的行权点）
            put_exercised = exercised_points[exercised_points['Signal'] == 1]
            if not put_exercised.empty:
                fig.add_trace(go.Scatter(
                    x=put_exercised.index,
                    y=put_exercised['Close'],
                    mode='markers',
                    name='看跌期权行权',
                    marker=dict(symbol='star', size=14, color='purple', line=dict(width=1, color='darkpurple'))
                ))
    
    # 设置图表布局
    fig.update_layout(
        title=title,
        xaxis_title='日期',
        yaxis_title='价格',
        hovermode='x unified',
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        height=500,
    )
    
    # 添加范围选择器
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1个月", step="month", stepmode="backward"),
                dict(count=3, label="3个月", step="month", stepmode="backward"),
                dict(count=6, label="6个月", step="month", stepmode="backward"),
                dict(count=1, label="1年", step="year", stepmode="backward"),
                dict(step="all", label="全部")
            ])
        )
    )
    
    return fig

# 函数：创建资产价值对比图表
def plot_asset_comparison(results):
    """
    绘制资产对比图（使用复权数据）
    """
    option_value = results['results']['Total_Asset']
    
    # 创建买入持有的时间序列数据
    buy_hold = pd.Series(index=option_value.index)
    buy_hold[:] = results['buy_hold_value']
    
    fig = go.Figure()
    
    # 添加期权策略曲线
    fig.add_trace(go.Scatter(
        x=option_value.index,
        y=option_value,
        name='期权策略',
        line=dict(color='blue')
    ))
    
    # 添加买入持有曲线
    fig.add_trace(go.Scatter(
        x=buy_hold.index,
        y=buy_hold,
        name='买入持有',
        line=dict(color='red')
    ))
    
    # 更新布局
    fig.update_layout(
        title='策略收益对比',
        xaxis_title='日期',
        yaxis_title='资产价值 ($)',
        hovermode='x unified'
    )
    
    return fig

# 主应用逻辑
if run_button:
    with st.spinner('正在获取股票数据...'):
        # 获取股票数据
        stock_data = get_stock_data(symbol, start_date, end_date)
        
        if stock_data is not None:
            # 显示股票信息
            st.subheader(f"{symbol} 股票信息")
            st.write(f"获取了 {len(stock_data)} 个交易日的数据")
            st.write(f"首日价格: ${stock_data['Close'].iloc[0]:.2f}")
            st.write(f"末日价格: ${stock_data['Close'].iloc[-1]:.2f}")
            price_change = ((stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[0]) / stock_data['Close'].iloc[0] * 100)
            st.write(f"期间价格变化: {price_change:.2f}%")
            
            # 显示价格图表
            st.plotly_chart(plot_price_chart(stock_data, title=f"{symbol} 价格走势"), use_container_width=True)
            
            # 初始化策略
            swing_trader = None
            option_trader = None
            
            # 根据选择运行策略
            if strategy_type in ["两种策略对比", "仅波段策略"]:
                with st.spinner('运行波段交易策略...'):
                    st.subheader("波段交易策略")
                    # 运行波段交易策略
                    print("正在运行波段交易策略...")
                    try:
                        swing_trader = SwingTrader(
                            data=stock_data,
                            initial_shares=initial_shares,
                            trade_shares=trade_shares,
                            threshold=swing_threshold
                        )
                        
                        # 显示波段策略结果
                        swing_initial_value = swing_trader.positions['Total_Asset'].iloc[0]
                        swing_final_value = swing_trader.positions['Total_Asset'].iloc[-1]
                        swing_returns = (swing_final_value - swing_initial_value) / swing_initial_value * 100
                        
                        buy_signals = sum(swing_trader.positions['Signal'] == 1)
                        sell_signals = sum(swing_trader.positions['Signal'] == -1)
                        
                        print(f"波段策略结果:")
                        print(f"- 初始资产: ${swing_initial_value:,.2f}")
                        print(f"- 最终资产: ${swing_final_value:,.2f}")
                        print(f"- 总收益率: {swing_returns:.2f}%")
                        print(f"- 买入交易: {buy_signals}次")
                        print(f"- 卖出交易: {sell_signals}次")
                        
                        # 显示波段策略交易信号图表
                        st.plotly_chart(plot_price_chart(
                            swing_trader.data, 
                            swing_trader.positions, 
                            title=f"{symbol} 波段交易策略信号"
                        ), use_container_width=True)
                        
                        # 与买入持有策略比较
                        buy_and_hold_value = initial_shares * stock_data['Close'].iloc[-1] + 100000  # 假设初始现金10万
                        buy_and_hold_return = (stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0] - 1) * 100
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("初始资产", f"${swing_initial_value:,.2f}")
                        col2.metric("最终资产", f"${swing_final_value:,.2f}")
                        col3.metric("总收益率", f"{swing_returns:.2f}%", f"{swing_returns - buy_and_hold_return:.2f}%")
                        
                        # 交易统计
                        # 使用positions数据计算实际执行的交易
                        shares_changes = swing_trader.positions['Shares'].diff()
                        actual_buys = sum(shares_changes > 0)
                        actual_sells = sum(shares_changes < 0)
                        
                        st.write("### 交易统计")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("实际买入交易", f"{actual_buys} 次")
                        col2.metric("实际卖出交易", f"{actual_sells} 次") 
                        col3.metric("每次交易", f"{trade_shares} 股")
                        
                        # 与买入持有策略比较
                        st.write(f"买入持有策略收益率: {buy_and_hold_return:.2f}% (最终价值: ${buy_and_hold_value:,.2f})")
                        st.write(f"波段策略 vs 买入持有: {swing_returns - buy_and_hold_return:.2f}%")
                        
                        # 添加：显示波段策略交易数据表格
                        st.write("### 波段交易详细记录")
                        # 创建一个新的DataFrame，只包含实际发生交易的日期
                        trade_records = pd.DataFrame(index=swing_trader.positions.index)
                        trade_records['Shares_Change'] = swing_trader.positions['Shares'].diff()
                        trade_records = trade_records[trade_records['Shares_Change'] != 0].copy()
                        
                        if not trade_records.empty:
                            # 添加易读的信号描述
                            trade_records['交易类型'] = trade_records['Shares_Change'].apply(lambda x: '买入' if x > 0 else '卖出')
                            trade_records['价格'] = swing_trader.data.loc[trade_records.index, 'Close'].map('${:.2f}'.format)
                            trade_records['交易股数'] = trade_records['Shares_Change'].abs()
                            trade_records['交易金额'] = trade_records['Shares_Change'].abs() * swing_trader.data.loc[trade_records.index, 'Close']
                            trade_records['交易金额'] = trade_records['交易金额'].map('${:.2f}'.format)
                            
                            # 选择要显示的列并按日期排序
                            display_records = trade_records[['交易类型', '价格', '交易股数', '交易金额']].sort_index()
                            st.dataframe(display_records)
                            
                            # 显示交易统计
                            st.write(f"总计交易次数：{len(display_records)}次")
                            buy_count = len(display_records[display_records['交易类型'] == '买入'])
                            sell_count = len(display_records[display_records['交易类型'] == '卖出'])
                            st.write(f"买入：{buy_count}次，卖出：{sell_count}次")
                        else:
                            st.info("没有产生交易信号")
                    except Exception as e:
                        st.error(f"运行波段策略时发生错误：{str(e)}")
            
            if strategy_type in ["两种策略对比", "仅期权策略"]:
                with st.spinner('运行期权交易策略...'):
                    st.subheader("期权交易策略")
                    # 运行期权策略
                    print("正在运行期权交易策略...")
                    try:
                        option_trader = OptionTrader(
                            data=stock_data,
                            initial_shares=initial_shares,
                            trade_shares=trade_shares,
                            threshold=swing_threshold,
                            premium_rate=premium_rate
                        )
                        
                        # 获取每月最后一个交易日
                        last_days = option_trader.data.groupby(pd.Grouper(freq='M')).apply(lambda x: x.index[-1] if not x.empty else None)
                        last_days = last_days[last_days.notna()]  # 移除空值
                        option_trader.data['IsLastDayOfMonth'] = option_trader.data.index.isin(last_days)
                        
                        # 显示期权策略结果
                        option_initial_value = option_trader.positions['Total_Asset'].iloc[0]
                        option_final_value = option_trader.positions['Total_Asset'].iloc[-1]
                        option_returns = ((option_final_value - option_initial_value) / option_initial_value * 100) if option_initial_value != 0 else 0
                        total_premium = option_trader.positions['Premium_Income'].iloc[-1]
                        
                        put_signals = sum(option_trader.positions['Signal'] == 1)
                        call_signals = sum(option_trader.positions['Signal'] == -1)
                        exercised = sum(option_trader.positions['IsExercised'])
                        
                        # 保存信号计数供后续使用
                        option_put_signals = put_signals
                        option_call_signals = call_signals
                        option_exercised = exercised
                        
                        print(f"期权策略结果:")
                        print(f"- 初始资产: ${option_initial_value:,.2f}")
                        print(f"- 最终资产: ${option_final_value:,.2f}")
                        print(f"- 总收益率: {option_returns:.2f}%")
                        print(f"- 累计权利金: ${total_premium:,.2f}")
                        print(f"- 卖出看跌期权: {put_signals}次")
                        print(f"- 卖出看涨期权: {call_signals}次")
                        print(f"- 期权被行权: {exercised}次")
                        
                        # 显示期权策略图表
                        st.plotly_chart(plot_price_chart(
                            option_trader.data, 
                            option_trader.positions, 
                            title=f"{symbol} 期权交易策略信号"
                        ), use_container_width=True)
                        
                        # 显示期权策略结果
                        initial_value = option_trader.positions['Total_Asset'].iloc[0]
                        final_value = option_trader.positions['Total_Asset'].iloc[-1]
                        returns = (final_value - initial_value) / initial_value * 100
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("初始资产", f"${initial_value:,.2f}")
                        col2.metric("最终资产", f"${final_value:,.2f}")
                        col3.metric("总收益率", f"{returns:.2f}%", f"{returns - buy_and_hold_return:.2f}%")
                        col4.metric("累计权利金", f"${total_premium:,.2f}", f"{total_premium/initial_value*100:.2f}%")
                        
                        # 交易统计
                        # 使用positions数据计算实际执行的期权交易
                        option_records = option_trader.data[(option_trader.data['Signal'] != 0) | (option_trader.data['IsExercised'] == True)].copy()
                        actual_put_signals = len(option_records[option_records['Signal'] == 1])
                        actual_call_signals = len(option_records[option_records['Signal'] == -1])
                        actual_exercised = sum(option_records['IsExercised'])
                        
                        st.write("### 交易统计")
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("卖出看跌期权", f"{actual_put_signals} 次")
                        col2.metric("卖出看涨期权", f"{actual_call_signals} 次") 
                        col3.metric("期权被行权", f"{actual_exercised} 次", 
                                  f"{(actual_exercised/(actual_put_signals+actual_call_signals)*100) if (actual_put_signals+actual_call_signals) > 0 else 0:.2f}%")
                        col4.metric("每次期权交易", f"{trade_shares} 股")
                        
                        # 与买入持有策略比较
                        buy_and_hold_value = initial_shares * stock_data['Close'].iloc[-1] + 100000  # 假设初始现金10万
                        buy_and_hold_return = (stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0] - 1) * 100
                        st.write(f"买入持有策略收益率: {buy_and_hold_return:.2f}% (最终价值: ${buy_and_hold_value:,.2f})")
                        st.write(f"期权策略 vs 买入持有: {returns - buy_and_hold_return:.2f}%")
                        
                        # 添加：显示期权策略交易数据表格
                        st.write("### 期权交易详细记录")
                        # 创建一个新的DataFrame，只包含期权交易记录
                        option_records = option_trader.data[(option_trader.data['Signal'] != 0) | (option_trader.data['IsExercised'] == True)].copy()
                        if not option_records.empty:
                            # 添加交易描述和格式化数据
                            def get_option_action(row):
                                if row['Signal'] == 1:
                                    return '卖出看跌期权'
                                elif row['Signal'] == -1:
                                    return '卖出看涨期权'
                                elif row['IsExercised'] == True:
                                    return f"期权被行权 ({row['OptionType']})"
                                return '无操作'
                            
                            option_records['操作'] = option_records.apply(get_option_action, axis=1)
                            option_records['价格'] = option_records['Close'].map('${:.2f}'.format)
                            option_records['行权价'] = option_records['StrikePrice'].apply(lambda x: f"${x:.2f}" if x > 0 else "-")
                            option_records['权利金'] = option_records['Premium'].apply(lambda x: f"${x:.2f}" if x > 0 else "-")
                            option_records['期权股数'] = option_records['OptionShares'].apply(lambda x: f"{x}" if x > 0 else "-")
                            
                            # 选择要显示的列
                            display_columns = ['操作', '价格', '行权价', '权利金', '期权股数']
                            st.dataframe(option_records[display_columns])
                    except Exception as e:
                        st.error(f"运行期权策略时发生错误：{str(e)}")
            
            # 如果两种策略都运行了，进行对比分析
            if strategy_type == "两种策略对比" and swing_trader and option_trader:
                st.subheader("策略对比分析")
                
                # 两种策略资产对比图
                st.plotly_chart(plot_asset_comparison(
                    {
                        'results': option_trader.positions,
                        'buy_hold_value': buy_and_hold_value  # 使用买入持有策略的最终价值
                    }
                ), use_container_width=True)
                
                # 对比表格
                comparison_data = {
                    "指标": ["总收益率", "相对买入持有", "交易次数", "最终资产值"],
                    "波段策略": [
                        f"{swing_returns:.2f}%", 
                        f"{swing_returns - buy_and_hold_return:.2f}%", 
                        f"{actual_buys + actual_sells}次", 
                        f"${swing_trader.positions['Total_Asset'].iloc[-1]:,.2f}"
                    ],
                    "期权策略": [
                        f"{option_returns:.2f}%", 
                        f"{option_returns - buy_and_hold_return:.2f}%", 
                        f"{option_put_signals + option_call_signals}次", 
                        f"${option_trader.positions['Total_Asset'].iloc[-1]:,.2f}"
                    ],
                    "买入持有": [
                        f"{buy_and_hold_return:.2f}%", 
                        "0.00%", 
                        "0次", 
                        f"${buy_and_hold_value:,.2f}"
                    ]
                }
                
                comparison_df = pd.DataFrame(comparison_data)
                st.table(comparison_df)
                
                # 策略分析结论
                st.write("### 策略分析结论")
                
                # 自动生成结论
                better_strategy = "波段策略" if swing_returns > option_returns else "期权策略"
                diff = abs(swing_returns - option_returns)
                
                st.write(f"1. 在回测期间（{start_date} 至 {end_date}），{better_strategy}表现更好，高出{diff:.2f}个百分点")
                
                if swing_returns > buy_and_hold_return and option_returns > buy_and_hold_return:
                    st.write("2. 两种策略均优于买入持有策略")
                elif swing_returns > buy_and_hold_return:
                    st.write("2. 波段策略优于买入持有策略，但期权策略表现不及买入持有")
                elif option_returns > buy_and_hold_return:
                    st.write("2. 期权策略优于买入持有策略，但波段策略表现不及买入持有")
                else:
                    st.write("2. 两种策略均不如买入持有策略")
                
                st.write(f"3. 累计权利金收入占初始资产的{total_premium/initial_value*100:.2f}%，是期权策略的主要收益来源")
                
                # 下载报告
                if swing_trader and option_trader:
                    # 生成报告数据
                    report_data = pd.DataFrame()
                    report_data['Date'] = stock_data.index
                    report_data['Close'] = stock_data['Close']
                    report_data['Reference_Price'] = stock_data['Close'].rolling(window=20).mean()
                    report_data['Swing_Signal'] = swing_trader.positions['Signal']
                    report_data['Swing_Total_Asset'] = swing_trader.positions['Total_Asset']
                    report_data['Option_Signal'] = option_trader.positions['Signal']
                    report_data['Option_Type'] = option_trader.data['OptionType']
                    report_data['Option_Total_Asset'] = option_trader.positions['Total_Asset']
                    report_data['Option_Premium_Income'] = option_trader.positions['Premium_Income']
                    
                    st.markdown(get_excel_download_link(report_data), unsafe_allow_html=True)
else:
    # 介绍和使用说明
    st.markdown("""
    ## 欢迎使用交易策略分析工具！
    
    这个工具可以帮助您比较两种不同的交易策略：
    
    1. **波段交易策略**：当价格波动超过设定阈值时进行买卖操作，通过波段差价获利
    2. **期权策略**：在价格波动时卖出看涨和看跌期权，通过收取权利金并控制行权条件获利
    
    ### 如何使用：
    
    1. 在左侧边栏中输入您想分析的股票代码（例如苹果公司为"AAPL"）
    2. 选择回测的时间范围
    3. 调整策略参数
    4. 点击"运行策略分析"按钮
    5. 查看结果并对比分析
    
    ### 参数说明：
    
    - **初始持股数量**：开始时持有的股票数量
    - **每次交易股数**：每次买入/卖出的股票数量或期权涉及的股票数量
    - **波动阈值**：触发交易信号的价格波动百分比（例如10%表示价格上涨或下跌10%时产生信号）
    - **期权权利金率**：卖出期权收取的权利金费率（占股票价格的百分比）
    
    ### 特别提示：
    
    **由于使用yfinance库获取市场数据，本工具只能获取历史股票数据（截至约2024年初）。
    请将日期范围设置在2010年至2023年之间以获得最佳结果。**
    
    点击左侧的"运行策略分析"按钮开始！
    """)
    
    # 显示示例图片
    st.image("https://www.investopedia.com/thmb/4KSHYJhZuIfaW-_8M9Bk-CuqUMc=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/dotdash_Final_Swing_Trading_Sep_2020-01-71f8a6715c0b47ffbb9ce640c52b8577.jpg", caption="波段交易示意图") 