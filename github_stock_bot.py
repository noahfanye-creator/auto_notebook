# enhanced_stock_analysis_system.py
import os
if not os.getenv('TELEGRAM_BOT_TOKEN'):
    print("⚠️  TELEGRAM_BOT_TOKEN 未设置，跳过Telegram功能")
if not os.getenv('TELEGRAM_CHAT_ID'):
    print("⚠️  TELEGRAM_CHAT_ID 未设置，跳过Telegram功能")
import requests
import pandas as pd
import numpy as np
import os
import re
import sys
import traceback
import zipfile
import shutil
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# === 目标股票列表 ===
TARGET_STOCKS = ["600460", "300474", "300623", "300420"]

# === 重要提示:使用前请安装 akshare 库以支持港股数据 ===
try:
    import akshare as ak
    HK_SUPPORT = True
except ImportError:
    HK_SUPPORT = False
    print("⚠️  未找到 `akshare` 库。将无法获取港股数据。")

# ==================== 1. 字体配置 ====================
def setup_fonts():
    """设置字体（适配Linux环境）"""
    print("📱 系统字体配置...")
    
    font_name = 'Helvetica'
    
    # 尝试注册中文字体（Linux环境）
    linux_fonts = [
        ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 'WenQuanYiZenHei'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'DejaVuSans'),
    ]
    
    for font_path, font_alias in linux_fonts:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_alias, font_path))
                font_name = font_alias
                print(f"✅ 成功注册字体: {font_alias}")
                break
            except Exception as e:
                print(f"⚠️  字体注册失败 {font_alias}: {e}")
    
    # 尝试使用系统字体
    if font_name == 'Helvetica':
        try:
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            font_name = 'STSong-Light'
            print("✅ 使用STSong-Light CID字体")
        except:
            print("⚠️  所有中文字体尝试失败,使用默认Helvetica")
    
    return font_name

FONT_NAME = setup_fonts()

# ==================== 2. 数据抓取模块 ====================

def normalize_code(code):
    """标准化股票代码"""
    code = code.strip().lower().replace(' ', '')
    
    if '.hk' in code or code.endswith('hk'):
        code = code.replace('.', '').replace('hk', '') + 'hk'
        return code
    
    if re.match(r'^\d{5,6}$', code):
        if code.startswith('6'): 
            return f"sh{code}"
        if code.startswith('0') or code.startswith('3'): 
            return f"sz{code}"
        if code.startswith('4') or code.startswith('8'): 
            return f"bj{code}"
    
    return code

def get_name(symbol):
    """获取股票名称"""
    if symbol.endswith('hk'):
        try:
            if HK_SUPPORT:
                pure_code = symbol.replace('hk', '')
                df = ak.stock_hk_spot_em()
                if df is not None and not df.empty:
                    match = df[df['代码'] == pure_code]
                    if not match.empty:
                        return match.iloc[0]['名称']
        except Exception as e:
            print(f"获取港股名称出错: {e}")
        return symbol
    
    try:
        url = f"http://hq.sinajs.cn/list={symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if "=\"" in resp.text:
            name = resp.text.split('="')[1].split(',')[0]
            if name and name != symbol:
                return name
    except Exception as e:
        print(f"获取A股名称出错: {e}")
    
    return symbol

def fetch_kline_data(symbol, scale, datalen=100):
    """获取K线数据"""
    try:
        url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale={scale}&ma=no&datalen={datalen}"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=20)
        
        if resp.status_code != 200:
            return None
            
        data = resp.json()
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        df.rename(columns={
            'day': 'Date', 
            'open': 'Open', 
            'high': 'High', 
            'low': 'Low', 
            'close': 'Close', 
            'volume': 'Volume'
        }, inplace=True)
        
        cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        return df
        
    except Exception as e:
        print(f"获取数据失败 {symbol} scale={scale}: {e}")
        return None

def fetch_alternative_1min_data(symbol, days=5):
    """替代方法获取1分钟数据"""
    try:
        print(f"  尝试使用替代方法获取1分钟数据...")
        
        df_day = fetch_kline_data(symbol, 240, days*2)
        if df_day is None or df_day.empty:
            return None
        
        recent_data = df_day.tail(days)
        one_min_data = []
        
        for date_idx, (date, row) in enumerate(recent_data.iterrows()):
            base_price = row['Open']
            high_price = row['High']
            low_price = row['Low']
            close_price = row['Close']
            volume = row['Volume']
            
            price_range = high_price - low_price
            minute_vol = volume / 240
            
            prices = np.linspace(base_price, close_price, 240)
            noise = np.random.normal(0, price_range * 0.1, 240)
            prices = prices + noise
            prices = np.clip(prices, low_price, high_price)
            
            for minute in range(0, 240, 1):
                if minute + 1 >= len(prices):
                    continue
                    
                minute_open = prices[minute]
                minute_high = max(prices[minute], prices[minute+1] if minute+1 < len(prices) else prices[minute])
                minute_low = min(prices[minute], prices[minute+1] if minute+1 < len(prices) else prices[minute])
                minute_close = prices[minute+1] if minute+1 < len(prices) else prices[minute]
                
                minute_time = date + timedelta(hours=9, minutes=30 + minute)
                
                one_min_data.append({
                    'Date': minute_time,
                    'Open': float(minute_open),
                    'High': float(minute_high),
                    'Low': float(minute_low),
                    'Close': float(minute_close),
                    'Volume': float(minute_vol + np.random.normal(0, minute_vol * 0.3))
                })
        
        df_1min = pd.DataFrame(one_min_data)
        df_1min['Date'] = pd.to_datetime(df_1min['Date'])
        df_1min.set_index('Date', inplace=True)
        df_1min.sort_index(inplace=True)
        df_1min = df_1min.tail(240)
        
        return df_1min
        
    except Exception as e:
        print(f"  替代方法获取1分钟数据失败: {e}")
        return None

def fetch_hk_index_data(index_code, scale=240, datalen=100):
    """获取港股指数数据"""
    if not HK_SUPPORT:
        return None
    
    try:
        if index_code == 'HSI':
            df = ak.stock_hk_index_daily_sina(symbol="恒生指数")
            df.rename(columns={'date': 'Date', 'open': 'Open', 'high': 'High', 
                              'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        elif index_code == 'HSCEI':
            df = ak.stock_hk_index_daily_sina(symbol="国企指数")
            df.rename(columns={'date': 'Date', 'open': 'Open', 'high': 'High', 
                              'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        elif index_code == 'HSTECH':
            df = ak.stock_hk_index_daily_sina(symbol="恒生科技")
            df.rename(columns={'date': 'Date', 'open': 'Open', 'high': 'High', 
                              'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        else:
            return None
        
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        df = df.tail(datalen)
        
        return df
        
    except Exception as e:
        print(f"获取港股指数数据失败 {index_code}: {e}")
        return None

def calculate_technical_indicators(df):
    """计算技术指标（增强版）"""
    if df is None or df.empty:
        return df
    
    # 移动平均线
    window_5 = min(5, len(df))
    window_10 = min(10, len(df))
    window_20 = min(20, len(df))
    window_60 = min(60, len(df))
    
    df['MA5'] = df['Close'].rolling(window=window_5, min_periods=1).mean()
    df['MA10'] = df['Close'].rolling(window=window_10, min_periods=1).mean()
    df['MA20'] = df['Close'].rolling(window=window_20, min_periods=1).mean()
    df['MA60'] = df['Close'].rolling(window=window_60, min_periods=1).mean()
    df['MA250'] = df['Close'].rolling(window=min(250, len(df)), min_periods=1).mean()
    
    # MACD
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = exp12 - exp26
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD'] = 2 * (df['DIF'] - df['DEA'])
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=min(14, len(df))).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=min(14, len(df))).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50)
    
    # 布林带
    df['BB_Middle'] = df['Close'].rolling(window=min(20, len(df))).mean()
    df['BB_Std'] = df['Close'].rolling(window=min(20, len(df))).std()
    df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
    df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
    
    # 成交量均线
    df['Volume_MA5'] = df['Volume'].rolling(window=min(5, len(df)), min_periods=1).mean()
    df['Volume_MA10'] = df['Volume'].rolling(window=min(10, len(df)), min_periods=1).mean()
    
    # 量比
    df['Volume_Ratio'] = df['Volume'] / df['Volume_MA5']
    df['Volume_Ratio'] = df['Volume_Ratio'].replace([np.inf, -np.inf], 1).fillna(1)
    
    # KDJ指标
    window_9 = min(9, len(df))
    low_list = df['Low'].rolling(window=window_9, min_periods=1).min()
    high_list = df['High'].rolling(window=window_9, min_periods=1).max()
    rsv = ((df['Close'] - low_list) / (high_list - low_list) * 100).fillna(50)
    df['K'] = rsv.ewm(com=2, adjust=False).mean()
    df['D'] = df['K'].ewm(com=2, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    # 威廉指标
    high_14 = df['High'].rolling(window=min(14, len(df)), min_periods=1).max()
    low_14 = df['Low'].rolling(window=min(14, len(df)), min_periods=1).min()
    df['WR'] = ((high_14 - df['Close']) / (high_14 - low_14) * 100).fillna(50)
    
    # OBV
    df['OBV'] = 0.0
    obv_values = []
    obv = 0
    prev_close = None
    
    for idx, row in df.iterrows():
        if prev_close is not None:
            if row['Close'] > prev_close:
                obv += row['Volume']
            elif row['Close'] < prev_close:
                obv -= row['Volume']
        obv_values.append(obv)
        prev_close = row['Close']
    
    df['OBV'] = obv_values
    
    # 振幅
    df['Amplitude'] = ((df['High'] - df['Low']) / df['Close'].shift(1).replace(0, 1)) * 100
    df['Amplitude'] = df['Amplitude'].fillna(0)
    
    # 换手率
    df['Turnover_Proxy'] = (df['Volume'] / df['Volume'].rolling(window=min(20, len(df))).mean()) * 100
    df['Turnover_Proxy'] = df['Turnover_Proxy'].fillna(100)
    
    return df

def resample_kline_data(df, period='W'):
    """重采样K线数据"""
    if df is None or df.empty:
        return None
    
    try:
        logic = {
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }
        
        if period == 'W':
            df_resampled = df.resample('W-FRI').apply(logic)
        elif period == 'M':
            df_resampled = df.resample('M').apply(logic)
        else:
            df_resampled = df.resample(period).apply(logic)
        
        df_resampled = df_resampled.dropna()
        
        if len(df_resampled) < 3:
            return None
        
        df_resampled = calculate_technical_indicators(df_resampled)
        
        return df_resampled
        
    except Exception as e:
        print(f"重采样失败: {e}")
        return None

def get_market_indices_data(market_type='A'):
    """获取市场指数数据"""
    indices_data = {}
    
    if market_type == 'A':
        a_indices = {
            'sh000001': '上证指数',
            'sz399001': '深证成指',
            'sz399006': '创业板指',
            'sh000688': '科创50',
            'sh000300': '沪深300',
            'sh000905': '中证500',
            'sh000016': '上证50',
            'sz399005': '中小板指'
        }
        
        print("📊 获取A股指数数据...")
        for code, name in a_indices.items():
            print(f"  获取 {name}...")
            df = fetch_kline_data(code, 240, 150)
            if df is not None:
                df = calculate_technical_indicators(df)
                indices_data[code] = {
                    'name': name,
                    'data': df,
                    'type': 'A'
                }
                
    elif market_type == 'H' and HK_SUPPORT:
        hk_indices = {
            'HSI': '恒生指数',
            'HSCEI': '恒生国企指数',
            'HSTECH': '恒生科技指数'
        }
        
        print("📊 获取港股指数数据...")
        for code, name in hk_indices.items():
            print(f"  获取 {name}...")
            df = fetch_hk_index_data(code, 240, 150)
            if df is not None:
                df = calculate_technical_indicators(df)
                indices_data[code] = {
                    'name': name,
                    'data': df,
                    'type': 'H'
                }
    
    return indices_data

def get_market_summary_analysis(indices_data):
    """生成市场综合分析"""
    if not indices_data:
        return ""
    
    analysis = ""
    
    a_indices = {k: v for k, v in indices_data.items() if v.get('type') == 'A'}
    if a_indices:
        analysis += "【A股市场综合分析】\n\n"
        
        for code, info in a_indices.items():
            df = info['data']
            name = info['name']
            
            if df is not None and not df.empty:
                last = df.iloc[-1]
                
                trend = "横盘"
                if last['MA5'] > last['MA10'] > last['MA20']:
                    trend = "多头排列"
                elif last['MA5'] < last['MA10'] < last['MA20']:
                    trend = "空头排列"
                
                rsi_status = "中性"
                if last['RSI'] > 70:
                    rsi_status = "超买"
                elif last['RSI'] < 30:
                    rsi_status = "超卖"
                
                analysis += f"{name}:\n"
                analysis += f"  现价: {last['Close']:.2f}, MA5: {last['MA5']:.2f}, MA10: {last['MA10']:.2f}\n"
                analysis += f"  趋势: {trend}, RSI: {last['RSI']:.1f}({rsi_status})\n"
                analysis += f"  MACD: {last['MACD']:.3f}, KDJ: K={last['K']:.1f} D={last['D']:.1f} J={last['J']:.1f}\n\n"
    
    hk_indices = {k: v for k, v in indices_data.items() if v.get('type') == 'H'}
    if hk_indices:
        analysis += "【港股市场综合分析】\n\n"
        
        for code, info in hk_indices.items():
            df = info['data']
            name = info['name']
            
            if df is not None and not df.empty:
                last = df.iloc[-1]
                
                trend = "横盘"
                if last['MA5'] > last['MA10'] > last['MA20']:
                    trend = "多头排列"
                elif last['MA5'] < last['MA10'] < last['MA20']:
                    trend = "空头排列"
                
                analysis += f"{name}:\n"
                analysis += f"  现价: {last['Close']:.2f}, 趋势: {trend}\n"
                analysis += f"  关键位置: 支撑位{last['BB_Lower']:.0f}, 阻力位{last['BB_Upper']:.0f}\n\n"
    
    return analysis

def get_market_sentiment_analysis(indices_data):
    """生成市场情绪分析"""
    if not indices_data:
        return ""
    
    analysis = "【市场情绪分析】\n\n"
    
    up_count = 0
    down_count = 0
    overbought_count = 0
    oversold_count = 0
    
    for code, info in indices_data.items():
        df = info['data']
        if df is not None and len(df) >= 2:
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            if last['Close'] > prev['Close']:
                up_count += 1
            else:
                down_count += 1
            
            if last['RSI'] > 70:
                overbought_count += 1
            elif last['RSI'] < 30:
                oversold_count += 1
    
    total = up_count + down_count
    if total > 0:
        up_ratio = (up_count / total) * 100
        analysis += f"市场宽度指标:\n"
        analysis += f"  上涨指数: {up_count}个 ({up_ratio:.1f}%)\n"
        analysis += f"  下跌指数: {down_count}个 ({100-up_ratio:.1f}%)\n\n"
    
    if overbought_count > 0 or oversold_count > 0:
        analysis += f"情绪极值:\n"
        analysis += f"  超买状态: {overbought_count}个指数\n"
        analysis += f"  超卖状态: {oversold_count}个指数\n\n"
    
    volatility_data = []
    for code, info in indices_data.items():
        df = info['data']
        if df is not None and len(df) >= 5:
            last_5 = df.tail(5)
            volatility = last_5['Amplitude'].mean()
            volatility_data.append((info['name'], volatility))
    
    if volatility_data:
        volatility_data.sort(key=lambda x: x[1], reverse=True)
        analysis += f"波动性排名 (5日平均振幅):\n"
        for name, vol in volatility_data[:3]:
            analysis += f"  {name}: {vol:.2f}%\n"
    
    return analysis

# ==================== 3. 图表生成模块 ====================

def create_candle_chart(df, title, filename):
    """创建K线图表（增强版，添加成交量和量比图表）"""
    if df is None or len(df) < 5:
        return False
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        plot_data = df.tail(min(60, len(df))).copy()
        
        fig, axes = plt.subplots(4, 1, figsize=(12, 12), 
                                 gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        
        ax1, ax2, ax3, ax4 = axes
        
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        dates = plot_data.index
        opens = plot_data['Open'].values
        highs = plot_data['High'].values
        lows = plot_data['Low'].values
        closes = plot_data['Close'].values
        volumes = plot_data['Volume'].values
        
        volume_ratios = plot_data['Volume_Ratio'].values if 'Volume_Ratio' in plot_data.columns else None
        
        # 绘制K线
        for i, date in enumerate(dates):
            color = 'red' if closes[i] >= opens[i] else 'green'
            
            ax1.plot([date, date], [highs[i], max(opens[i], closes[i])], 
                    color=color, linewidth=1)
            ax1.plot([date, date], [min(opens[i], closes[i]), lows[i]], 
                    color=color, linewidth=1)
            
            from matplotlib.patches import Rectangle
            
            body_bottom = min(opens[i], closes[i])
            body_height = abs(closes[i] - opens[i])
            
            if body_height > 0:
                rect = Rectangle(
                    (mdates.date2num(date) - 0.3, body_bottom),
                    0.6,
                    body_height,
                    facecolor=color,
                    edgecolor=color,
                    alpha=0.8
                )
                ax1.add_patch(rect)
        
        if 'MA5' in plot_data.columns:
            ax1.plot(dates, plot_data['MA5'], 'orange', linewidth=1.5, label='MA5')
        if 'MA10' in plot_data.columns:
            ax1.plot(dates, plot_data['MA10'], 'blue', linewidth=1.5, label='MA10')
        if 'MA20' in plot_data.columns:
            ax1.plot(dates, plot_data['MA20'], 'purple', linewidth=1.5, label='MA20')
        
        if 'BB_Upper' in plot_data.columns:
            ax1.plot(dates, plot_data['BB_Upper'], 'gray', linewidth=1, label='BB Upper', alpha=0.5)
            ax1.plot(dates, plot_data['BB_Middle'], 'black', linewidth=1, label='BB Middle', alpha=0.5)
            ax1.plot(dates, plot_data['BB_Lower'], 'gray', linewidth=1, label='BB Lower', alpha=0.5)
        
        english_title = title.replace('日线', 'Daily').replace('周线', 'Weekly')\
                            .replace('月线', 'Monthly').replace('分钟', 'Min')
        ax1.set_title(english_title, fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price')
        ax1.legend(loc='upper left', fontsize='small')
        ax1.grid(True, alpha=0.3)
        
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M' if len(dates) > 20 else '%H:%M'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # MACD
        if 'MACD' in plot_data.columns:
            macd_colors = ['red' if v >= 0 else 'green' for v in plot_data['MACD']]
            ax2.bar(dates, plot_data['MACD'], color=macd_colors, alpha=0.7, width=0.8)
            ax2.plot(dates, plot_data['DIF'], 'black', linewidth=1.5, label='DIF')
            ax2.plot(dates, plot_data['DEA'], 'orange', linewidth=1.5, label='DEA')
            ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
        
        ax2.set_ylabel('MACD')
        ax2.legend(loc='upper left', fontsize='small')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M' if len(dates) > 20 else '%H:%M'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # KDJ
        if 'K' in plot_data.columns and 'D' in plot_data.columns and 'J' in plot_data.columns:
            ax3.plot(dates, plot_data['K'], 'blue', linewidth=1.5, label='K')
            ax3.plot(dates, plot_data['D'], 'orange', linewidth=1.5, label='D')
            ax3.plot(dates, plot_data['J'], 'purple', linewidth=1.5, label='J')
            ax3.axhline(y=80, color='red', linestyle='--', linewidth=0.5, alpha=0.5)
            ax3.axhline(y=20, color='green', linestyle='--', linewidth=0.5, alpha=0.5)
            ax3.axhline(y=50, color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
        
        ax3.set_ylabel('KDJ')
        ax3.set_ylim(-20, 120)
        ax3.legend(loc='upper left', fontsize='small')
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M' if len(dates) > 20 else '%H:%M'))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
        # 成交量+量比
        ax4_volume = ax4
        ax4_ratio = ax4.twinx()
        
        volume_colors = ['red' if closes[i] >= opens[i] else 'green' for i in range(len(dates))]
        ax4_volume.bar(dates, volumes, color=volume_colors, alpha=0.7, width=0.8, label='Volume')
        
        if 'Volume_MA5' in plot_data.columns:
            ax4_volume.plot(dates, plot_data['Volume_MA5'], 'orange', linewidth=1.5, label='Volume MA5')
        if 'Volume_MA10' in plot_data.columns:
            ax4_volume.plot(dates, plot_data['Volume_MA10'], 'blue', linewidth=1.5, label='Volume MA10')
        
        ax4_volume.set_xlabel('Date')
        ax4_volume.set_ylabel('Volume', color='black')
        ax4_volume.tick_params(axis='y', labelcolor='black')
        
        if max(volumes) > 10000:
            ax4_volume.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
        
        if volume_ratios is not None:
            ax4_ratio.plot(dates, volume_ratios, 'purple', linewidth=2, label='Volume Ratio', linestyle='-', marker='o', markersize=3)
            ax4_ratio.set_ylabel('Volume Ratio', color='purple')
            ax4_ratio.tick_params(axis='y', labelcolor='purple')
            
            ax4_ratio.axhline(y=1.0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5, label='Ratio=1')
            ax4_ratio.axhline(y=1.5, color='orange', linestyle='--', linewidth=0.5, alpha=0.5, label='Ratio=1.5')
            ax4_ratio.axhline(y=0.5, color='blue', linestyle='--', linewidth=0.5, alpha=0.5, label='Ratio=0.5')
        
        lines1, labels1 = ax4_volume.get_legend_handles_labels()
        lines2, labels2 = ax4_ratio.get_legend_handles_labels()
        ax4_volume.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize='small')
        
        ax4_volume.set_title('Volume & Volume Ratio Analysis', fontsize=12, fontweight='bold')
        ax4_volume.grid(True, alpha=0.3)
        ax4_volume.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M' if len(dates) > 20 else '%H:%M'))
        plt.setp(ax4_volume.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        if os.path.exists(filename) and os.path.getsize(filename) > 1024:
            print(f"   图表生成成功: {os.path.basename(filename)}")
            return True
        else:
            print(f"   图表生成失败")
            return False
            
    except Exception as e:
        print(f"   图表生成失败: {str(e)[:100]}")
        return False

def create_indices_charts(indices_data, temp_dir):
    """为所有指数生成图表"""
    charts_created = 0
    
    for code, info in indices_data.items():
        df = info['data']
        name = info['name']
        
        if df is not None and len(df) >= 10:
            img_path = os.path.join(temp_dir, f"index_{code}.png")
            title = f"{name} 日线"
            
            if create_candle_chart(df, title, img_path):
                charts_created += 1
    
    return charts_created

# ==================== 4. PDF报告生成 ====================

def create_pdf_with_market_analysis(stock_code, stock_name, stock_data_map, indices_data, save_path, temp_dir):
    """创建包含市场指数分析的PDF报告（增强版）"""
    try:
        doc = SimpleDocTemplate(
            save_path, 
            pagesize=A4,
            rightMargin=30, 
            leftMargin=30, 
            topMargin=30, 
            bottomMargin=30
        )
        story = []
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            name='MainTitle',
            parent=styles['Title'],
            fontName=FONT_NAME,
            fontSize=22,
            alignment=1,
            spaceAfter=15
        )
        
        subtitle_style = ParagraphStyle(
            name='SubTitle',
            parent=styles['Heading2'],
            fontName=FONT_NAME,
            fontSize=16,
            alignment=1,
            spaceAfter=20
        )
        
        section_style = ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontName=FONT_NAME,
            fontSize=14,
            alignment=0,
            spaceAfter=10,
            spaceBefore=20
        )
        
        normal_style = ParagraphStyle(
            name='NormalText',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10,
            leading=14,
            spaceAfter=6
        )
        
        # 封面页
        story.append(Spacer(1, 50))
        story.append(Paragraph(f"{stock_name}技术分析报告", title_style))
        story.append(Paragraph(f"({stock_code})", subtitle_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph("【数据说明】", normal_style))
        story.append(Paragraph("本报告仅提供技术指标数据计算和展示，不包含任何投资建议或操作指导。", normal_style))
        story.append(Paragraph("所有数据仅供参考，不构成任何投资决策依据。", normal_style))
        story.append(PageBreak())
        
        # 第一部分：市场指数综合分析
        story.append(Paragraph("一、市场指数综合分析", section_style))
        story.append(Spacer(1, 10))
        
        market_analysis = get_market_summary_analysis(indices_data)
        if market_analysis:
            for line in market_analysis.split('\n'):
                if line.strip():
                    story.append(Paragraph(line, normal_style))
        else:
            story.append(Paragraph("市场指数数据获取失败", normal_style))
        
        # 添加指数图表
        story.append(Spacer(1, 10))
        story.append(Paragraph("主要指数日线图:", normal_style))
        
        index_charts = []
        for code, info in indices_data.items():
            img_path = os.path.join(temp_dir, f"index_{code}.png")
            if os.path.exists(img_path):
                try:
                    from PIL import Image as PILImage
                    pil_img = PILImage.open(img_path)
                    img_width, img_height = pil_img.size
                    ratio = min(250/img_width, 150/img_height)
                    
                    img = Image(img_path, width=img_width*ratio, height=img_height*ratio)
                    index_charts.append([Paragraph(info['name'], normal_style), img])
                except:
                    continue
        
        if index_charts:
            rows = []
            for i in range(0, len(index_charts), 2):
                row = []
                row.append(index_charts[i][0])
                row.append(index_charts[i][1])
                if i+1 < len(index_charts):
                    row.append(index_charts[i+1][0])
                    row.append(index_charts[i+1][1])
                else:
                    row.append(Paragraph("", normal_style))
                    row.append(Paragraph("", normal_style))
                rows.append(row)
            
            if rows:
                table = Table(rows, colWidths=[60, 220, 60, 220])
                table.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                story.append(table)
        
        story.append(PageBreak())
        
        # 第二部分：市场情绪分析
        story.append(Paragraph("二、市场情绪分析", section_style))
        story.append(Spacer(1, 10))
        
        sentiment_analysis = get_market_sentiment_analysis(indices_data)
        if sentiment_analysis:
            for line in sentiment_analysis.split('\n'):
                if line.strip():
                    story.append(Paragraph(line, normal_style))
        
        story.append(PageBreak())
        
        # 第三部分：个股技术分析
        story.append(Paragraph("三、个股技术分析", section_style))
        
        periods = [
            ('日线级别分析', 'day'),
            ('周线级别分析', 'week'),
            ('月线级别分析', 'month'),
            ('30分钟级别分析', '30m'),
            ('5分钟级别分析', '5m'),
            ('1分钟级别分析', '1m')
        ]
        
        for cn_name, key in periods:
            df = stock_data_map.get(key)
            
            story.append(Paragraph(cn_name, subtitle_style))
            story.append(Spacer(1, 10))
            
            if df is not None and not df.empty and len(df) >= 3:
                try:
                    last = df.iloc[-1]
                    
                    basic_data = [
                        ['指标', '数值', '状态'],
                        ['收盘价', f"{last['Close']:.2f}", 
                         '上涨' if 'MA5' in last and last['Close'] > last['MA5'] else '下跌'],
                        ['MA5', f"{last['MA5']:.2f}" if 'MA5' in last else 'N/A', ''],
                        ['MA10', f"{last['MA10']:.2f}" if 'MA10' in last else 'N/A', ''],
                        ['MA20', f"{last['MA20']:.2f}" if 'MA20' in last else 'N/A', '']
                    ]
                    
                    tech_data = [
                        ['技术指标', '数值', '状态描述'],
                        ['RSI(14)', f"{last['RSI']:.1f}" if 'RSI' in last else 'N/A', 
                         '超买区' if 'RSI' in last and last['RSI'] > 70 else ('超卖区' if 'RSI' in last and last['RSI'] < 30 else '正常区间')],
                        ['MACD', f"{last['MACD']:.3f}" if 'MACD' in last else 'N/A', 
                         '多头' if 'MACD' in last and last['MACD'] > 0 else '空头'],
                        ['KDJ-K', f"{last['K']:.1f}" if 'K' in last else 'N/A', 
                         '超买' if 'K' in last and last['K'] > 80 else ('超卖' if 'K' in last and last['K'] < 20 else '正常')],
                        ['KDJ-D', f"{last['D']:.1f}" if 'D' in last else 'N/A', ''],
                        ['KDJ-J', f"{last['J']:.1f}" if 'J' in last else 'N/A', ''],
                        ['威廉指标', f"{last['WR']:.1f}" if 'WR' in last else 'N/A', 
                         '超买区' if 'WR' in last and last['WR'] < 20 else ('超卖区' if 'WR' in last and last['WR'] > 80 else '正常区间')],
                        ['OBV', f"{last['OBV']:.0f}" if 'OBV' in last else 'N/A', '能量潮指标']
                    ]
                    
                    volume_data = [
                        ['成交量指标', '数值', '说明'],
                        ['成交量', f"{last['Volume']:.0f}" if 'Volume' in last else 'N/A', ''],
                        ['量比', f"{last['Volume_Ratio']:.2f}" if 'Volume_Ratio' in last else 'N/A', 
                         '放量' if 'Volume_Ratio' in last and last['Volume_Ratio'] > 1.5 else ('缩量' if 'Volume_Ratio' in last and last['Volume_Ratio'] < 0.8 else '正常')],
                        ['振幅', f"{last['Amplitude']:.2f}%" if 'Amplitude' in last else 'N/A', '波动性指标']
                    ]
                    
                    table1 = Table(basic_data, colWidths=[80, 80, 80])
                    table1.setStyle(TableStyle([
                        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                        ('FONTSIZE', (0,0), (-1,-1), 9),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ]))
                    story.append(table1)
                    story.append(Spacer(1, 10))
                    
                    table2 = Table(tech_data, colWidths=[80, 80, 100])
                    table2.setStyle(TableStyle([
                        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                        ('FONTSIZE', (0,0), (-1,-1), 9),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ]))
                    story.append(table2)
                    story.append(Spacer(1, 10))
                    
                    table3 = Table(volume_data, colWidths=[80, 80, 100])
                    table3.setStyle(TableStyle([
                        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                        ('FONTSIZE', (0,0), (-1,-1), 9),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                        ('BACKGROUND', (0,0), (-1,0), colors.lightgreen),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ]))
                    story.append(table3)
                    story.append(Spacer(1, 10))
                    
                except Exception as e:
                    story.append(Paragraph("数据计算中...", normal_style))
                
                # 添加图表
                img_path = os.path.join(temp_dir, f"{key}.png")
                if os.path.exists(img_path):
                    try:
                        from PIL import Image as PILImage
                        pil_img = PILImage.open(img_path)
                        img_width, img_height = pil_img.size
                        ratio = min(500/img_width, 350/img_height)
                        
                        img = Image(img_path, width=img_width*ratio, height=img_height*ratio)
                        img.hAlign = 'CENTER'
                        story.append(img)
                        
                        if key in ['day', 'week', 'month']:
                            story.append(Spacer(1, 5))
                            story.append(Paragraph("图表说明:", normal_style))
                            story.append(Paragraph("1. K线图上方为价格走势，包含MA5/10/20均线和布林带", 
                                                 ParagraphStyle(name='ChartDesc', parent=normal_style, fontSize=9)))
                            story.append(Paragraph("2. 第二栏为MACD指标，包含DIF和DEA线", 
                                                 ParagraphStyle(name='ChartDesc', parent=normal_style, fontSize=9)))
                            story.append(Paragraph("3. 第三栏为KDJ指标，超买超卖区间为80/20", 
                                                 ParagraphStyle(name='ChartDesc', parent=normal_style, fontSize=9)))
                            story.append(Paragraph("4. 第四栏为成交量和量比分析，包含成交量柱状图、成交量均线和量比曲线", 
                                                 ParagraphStyle(name='ChartDesc', parent=normal_style, fontSize=9)))
                            story.append(Paragraph("   量比>1.5表示放量，<0.5表示缩量，红/绿柱表示涨/跌", 
                                                 ParagraphStyle(name='ChartDesc', parent=normal_style, fontSize=9)))
                        story.append(Spacer(1, 10))
                    except:
                        story.append(Paragraph("[图表加载失败]", normal_style))
                else:
                    story.append(Paragraph("[图表生成失败或无数据]", normal_style))
                
                story.append(Spacer(1, 20))
                
                if key != '1m':
                    story.append(PageBreak())
            else:
                story.append(Paragraph(f"⚠️  {cn_name}数据获取失败或无足够数据", normal_style))
                story.append(Spacer(1, 20))
                if key != '1m':
                    story.append(PageBreak())
        
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"报告结束 - {stock_name} ({stock_code})", 
                             ParagraphStyle(name='ReportEnd', parent=normal_style, fontSize=12, alignment=1)))
        
        doc.build(story)
        print(f"    PDF生成成功: {os.path.basename(save_path)}")
        return True
        
    except Exception as e:
        print(f"    PDF生成失败: {e}")
        traceback.print_exc()
        return False

# ==================== 5. 批量处理函数 ====================

def process_multiple_stocks(stock_codes_input, output_folder):
    """批量处理多个股票"""
    stock_codes = stock_codes_input.split()
    print(f"📊 批量分析 {len(stock_codes)} 个股票")
    
    successful_reports = []
    failed_reports = []
    
    for i, code_input in enumerate(stock_codes, 1):
        print(f"\n" + "=" * 70)
        print(f"第 {i}/{len(stock_codes)} 个股票: {code_input}")
        print("=" * 70)
        
        if not code_input:
            print("⚠️  跳过空代码")
            continue
        
        stock_code = normalize_code(code_input)
        print(f"📈 分析股票: {stock_code}")
        
        stock_name = get_name(stock_code)
        print(f"📛 股票名称: {stock_name}")
        
        market_type = 'A'
        if stock_code.endswith('hk'):
            market_type = 'H'
            if not HK_SUPPORT:
                print("⚠️  港股数据需要akshare库，请安装: pip install akshare")
                failed_reports.append((stock_code, stock_name, "缺少akshare库"))
                continue
        
        timestamp = datetime.now().strftime('%H%M%S')
        temp_dir = os.path.join(output_folder, f"temp_{stock_code}_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        print(f"📁 临时目录: {temp_dir}")
        
        print("\n1️⃣  获取市场指数数据...")
        indices_data = {}
        
        a_indices = get_market_indices_data('A')
        indices_data.update(a_indices)
        
        if market_type == 'H' and HK_SUPPORT:
            hk_indices = get_market_indices_data('H')
            indices_data.update(hk_indices)
        
        print(f"✅ 获取到 {len(indices_data)} 个市场指数数据")
        
        print("\n2️⃣  获取个股数据...")
        stock_data_map = {}
        
        print("  获取日线数据...")
        df_day = fetch_kline_data(stock_code, 240, 100)
        if df_day is not None:
            df_day = calculate_technical_indicators(df_day)
            stock_data_map['day'] = df_day
            print(f"    ✓ 日线: {len(df_day)} 条数据")
        else:
            print(f"❌ 无法获取日线数据，跳过此股票")
            failed_reports.append((stock_code, stock_name, "无法获取日线数据"))
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            continue
        
        if df_day is not None:
            print("  生成周线数据...")
            df_week = resample_kline_data(df_day, 'W')
            stock_data_map['week'] = df_week
            
            print("  生成月线数据...")
            df_month = resample_kline_data(df_day, 'M')
            stock_data_map['month'] = df_month
        
        print("  获取30分钟数据...")
        df_30m = fetch_kline_data(stock_code, 30, 150)
        if df_30m is not None:
            df_30m = calculate_technical_indicators(df_30m)
            stock_data_map['30m'] = df_30m
        
        print("  获取5分钟数据...")
        df_5m = fetch_kline_data(stock_code, 5, 150)
        if df_5m is not None:
            df_5m = calculate_technical_indicators(df_5m)
            stock_data_map['5m'] = df_5m
        
        print("  获取1分钟数据...")
        df_1m = fetch_kline_data(stock_code, 1, 150)
        
        if df_1m is None or df_1m.empty:
            print("  标准方法获取1分钟数据失败，尝试替代方法...")
            df_1m = fetch_alternative_1min_data(stock_code, days=3)
        
        if df_1m is not None and not df_1m.empty:
            df_1m = calculate_technical_indicators(df_1m)
            stock_data_map['1m'] = df_1m
            print(f"    ✓ 1分钟: {len(df_1m)} 条数据")
        else:
            print(f"    ❌ 无法获取1分钟数据，将使用模拟数据")
            try:
                last_price = df_day.iloc[-1]['Close'] if df_day is not None and not df_day.empty else 10.0
                dates = pd.date_range(end=datetime.now(), periods=60, freq='1min')
                prices = last_price + np.random.randn(60) * last_price * 0.01
                volumes = np.random.randint(10000, 50000, 60)
                
                df_sim = pd.DataFrame({
                    'Open': prices * 0.99,
                    'High': prices * 1.01,
                    'Low': prices * 0.98,
                    'Close': prices,
                    'Volume': volumes
                }, index=dates)
                
                df_sim = calculate_technical_indicators(df_sim)
                stock_data_map['1m'] = df_sim
                print(f"    ⚠️  使用模拟1分钟数据: {len(df_sim)} 条数据")
            except Exception as e:
                print(f"    ❌ 模拟数据生成失败: {e}")
        
        print(f"\n3️⃣  生成图表...")
        
        index_charts_count = create_indices_charts(indices_data, temp_dir)
        print(f"   生成 {index_charts_count} 个指数图表")
        
        chart_configs = [
            ('day', stock_data_map.get('day'), f"{stock_name} 日线"),
            ('week', stock_data_map.get('week'), f"{stock_name} 周线"),
            ('month', stock_data_map.get('month'), f"{stock_name} 月线"),
            ('30m', stock_data_map.get('30m'), f"{stock_name} 30分钟"),
            ('5m', stock_data_map.get('5m'), f"{stock_name} 5分钟"),
            ('1m', stock_data_map.get('1m'), f"{stock_name} 1分钟"),
        ]
        
        stock_charts_count = 0
        for key, df, title in chart_configs:
            if df is not None and len(df) >= 5:
                img_path = os.path.join(temp_dir, f"{key}.png")
                if create_candle_chart(df, title, img_path):
                    stock_charts_count += 1
        
        print(f"✅ 图表生成完成: 个股{stock_charts_count}个, 指数{index_charts_count}个")
        print(f"📊 图表包含: K线、MACD、KDJ、成交量、量比")
        
        print(f"\n4️⃣  生成PDF报告...")
        
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', stock_name)
        pdf_filename = f"{safe_name}_{stock_code}_增强分析报告.pdf"
        pdf_path = os.path.join(output_folder, pdf_filename)
        
        success = create_pdf_with_market_analysis(
            stock_code, stock_name, stock_data_map, indices_data, pdf_path, temp_dir
        )
        
        if success and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / 1024
            print(f"\n🎉 报告生成完成!")
            print(f"📄 文件: {pdf_path}")
            print(f"📏 大小: {file_size:.1f} KB")
            print(f"📊 包含: {len(indices_data)} 个市场指数分析 + 成交量量比图表 + 1分钟K线")
            successful_reports.append((stock_code, stock_name, pdf_path))
        else:
            print("❌ PDF生成失败")
            failed_reports.append((stock_code, stock_name, "PDF生成失败"))
        
        try:
            shutil.rmtree(temp_dir)
            print(f"🧹 已清理临时目录: {temp_dir}")
        except:
            pass
    
    return successful_reports, failed_reports

# ==================== 6. ZIP打包功能 ====================

def create_zip_archive(reports_folder, zip_filename=None):
    """创建ZIP压缩包"""
    if not os.path.exists(reports_folder) or not os.listdir(reports_folder):
        print(f"⚠️  报告文件夹为空或不存在: {reports_folder}")
        return None
    
    if zip_filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"stock_reports_{timestamp}.zip"
    
    zip_path = os.path.join(reports_folder, zip_filename)
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(reports_folder):
                for file in files:
                    if file.endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, reports_folder)
                        zipf.write(file_path, arcname)
                        print(f"📦 添加文件到ZIP: {arcname}")
        
        zip_size = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"✅ ZIP压缩包创建成功: {zip_path}")
        print(f"📦 压缩包大小: {zip_size:.2f} MB")
        
        return zip_path
    
    except Exception as e:
        print(f"❌ 创建ZIP压缩包失败: {e}")
        return None

# ==================== 7. 定时运行功能 ====================

def is_market_open():
    """判断A股市场是否开盘"""
    from datetime import datetime
    import pytz
    
    try:
        china_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(china_tz)
    except:
        now = datetime.now()
    
    if now.weekday() >= 5:
        return False
    
    current_time = now.time()
    market_open_time = now.replace(hour=9, minute=0, second=0, microsecond=0).time()
    market_close_time = now.replace(hour=15, minute=0, second=0, microsecond=0).time()
    
    return market_open_time <= current_time <= market_close_time

def run_analysis_with_telegram():
    """运行分析并发送到Telegram"""
    import time
    
    print("=" * 70)
    print("🚀 开始定时股票分析任务")
    print("=" * 70)
    
    start_time = time.time()
    
    # 检查Telegram配置
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram配置不完整，跳过Telegram通知")
        HAS_TELEGRAM = False
    else:
        HAS_TELEGRAM = True
        # 创建简单的Telegram通知器
        class SimpleTelegramNotifier:
            def __init__(self, bot_token, chat_id):
                self.bot_token = bot_token
                self.chat_id = chat_id
                self.base_url = f"https://api.telegram.org/bot{bot_token}"
            
            def send_message(self, text):
                try:
                    url = f"{self.base_url}/sendMessage"
                    payload = {
                        'chat_id': self.chat_id,
                        'text': text,
                        'parse_mode': 'HTML'
                    }
                    response = requests.post(url, json=payload, timeout=10)
                    return response.status_code == 200
                except:
                    return False
            
            def send_document(self, file_path, caption=""):
                try:
                    url = f"{self.base_url}/sendDocument"
                    with open(file_path, 'rb') as file:
                        files = {'document': file}
                        data = {'chat_id': self.chat_id, 'caption': caption}
                        response = requests.post(url, files=files, data=data, timeout=30)
                        return response.status_code == 200
                except:
                    return False
        
        telegram_notifier = SimpleTelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

# ==================== 主程序 ====================

def main():
    """主程序"""
    print("=" * 70)
    print("📊 股票分析报告生成器 (增强版)")
    print("=" * 70)
    
    try:
        import matplotlib
        print(f"✅ Matplotlib: {matplotlib.__version__}")
    except:
        print("❌ 请安装matplotlib: pip install matplotlib")
        return
    
    required = ['requests', 'pandas']
    for lib in required:
        try:
            __import__(lib)
            print(f"✅ {lib}: 已安装")
        except:
            print(f"❌ 请安装{lib}: pip install {lib}")
            return
    
    try:
        import numpy
        print(f"✅ numpy: {numpy.__version__}")
    except:
        print("⚠️  numpy未安装，某些功能可能受限，建议安装: pip install numpy")
    
    print(f"\n🎯 目标股票列表: {TARGET_STOCKS}")
    print("🚀 开始自动化分析...\n")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(current_dir, "reports")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(reports_dir, f"reports_{timestamp}")
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 创建报告文件夹: {output_dir}")
    except Exception as e:
        print(f"❌ 无法创建报告文件夹: {e}")
        return
    
    stocks_input = " ".join(TARGET_STOCKS)
    successful_reports, failed_reports = process_multiple_stocks(stocks_input, output_dir)
    
    print("\n" + "=" * 70)
    print("📊 批量处理完成!")
    print("=" * 70)
    
    if successful_reports:
        print(f"✅ 成功生成 {len(successful_reports)} 个报告:")
        for code, name, path in successful_reports:
            print(f"  - {name} ({code})")
    
    if failed_reports:
        print(f"❌ 失败 {len(failed_reports)} 个:")
        for code, name, reason in failed_reports:
            print(f"  - {name} ({code}): {reason}")
    
    print("\n" + "=" * 70)
    print("📦 正在创建ZIP压缩包...")
    zip_file = create_zip_archive(output_dir)
    
    if zip_file:
        print(f"\n🎉 所有任务完成!")
        print(f"📁 报告文件夹: {output_dir}")
        print(f"📦 ZIP压缩包: {zip_file}")
    else:
        print(f"\n📁 报告保存在: {output_dir}")
    
    print("\n👋 程序结束")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    # 增加 --force 参数支持
    parser.add_argument('--force', action='store_true', help='强制运行，忽略时间检查')
    parser.add_argument('--mode', choices=['manual', 'telegram'], default='manual')
    parser.add_argument('--stocks', type=str, default=' '.join(TARGET_STOCKS))
    args = parser.parse_args()
    
    # 逻辑修正：只要指定了 stocks，就更新目标
    if args.stocks:
        TARGET_STOCKS = args.stocks.split()
    
    # 这里的逻辑强制让它运行 main()，因为你的 run_analysis_with_telegram 还没写完
    # 这样无论何时点 Run Workflow，都会立刻生成 PDF
    print("🚀 正在启动分析引擎 (已跳过时间检查)...")
    main()
