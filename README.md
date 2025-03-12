# 交易策略分析工具

这是一个基于网页的交易策略分析工具，可以让用户对比波段交易策略和期权交易策略的表现。

## 功能特点

- 支持不同股票代码的回测分析
- 自定义回测时间范围
- 可调整关键策略参数（如波动阈值、权利金率等）
- 交互式图表展示策略表现
- 策略对比分析及报告导出

## 包含的交易策略

1. **波段交易策略**：当价格波动超过设定阈值时进行买卖操作，通过波段差价获利
2. **期权策略**：在价格波动时卖出看涨和看跌期权，通过收取权利金并控制行权条件获利

## 安装步骤

1. 克隆代码库

```bash
git clone <repository-url>
cd trading-strategy-analyzer
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

## 本地运行

```bash
streamlit run app.py
```

运行后在浏览器中访问 http://localhost:8501 

## 部署到网络

### 部署到Streamlit Cloud（推荐）

1. 在 [Streamlit Cloud](https://streamlit.io/cloud) 上注册账号
2. 创建新的应用，链接到您的GitHub仓库
3. 选择app.py作为主文件
4. 部署应用，几分钟后即可访问

### 部署到Heroku

1. 安装Heroku CLI并登录

```bash
npm install -g heroku
heroku login
```

2. 创建Heroku应用

```bash
heroku create your-app-name
```

3. 添加必要文件

创建Procfile文件：
```
web: sh setup.sh && streamlit run app.py
```

创建setup.sh文件：
```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

4. 部署到Heroku

```bash
git add .
git commit -m "Setup for Heroku"
git push heroku master
```

## 使用说明

1. 在左侧边栏中输入您想分析的股票代码（例如苹果公司为"AAPL"）
2. 选择回测的时间范围
3. 调整策略参数
4. 点击"运行策略分析"按钮
5. 查看结果并对比分析

## 文件结构

- `app.py` - 主应用程序文件，包含Streamlit界面
- `swing_strategy.py` - 波段交易策略实现
- `option_strategy.py` - 期权交易策略实现
- `requirements.txt` - 依赖包列表
- `README.md` - 项目说明文档

## 许可证

MIT 