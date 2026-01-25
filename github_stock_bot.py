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
import time
import json
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# 可选依赖：akshare
try:
    import akshare as ak
except Exception:
    ak = None

# === 目标股票列表 ===
TARGET_STOCKS = ["600460", "300474", "300623", "300420"]

# ==================== 1. 字体配置 ====================
def setup_fonts():
    """设置字体（适配macOS/Linux环境）"""
    print("📱 系统字体配置...")
    
    font_name = 'Helvetica'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 优先使用项目内置中文字体
    local_font = os.path.join(current_dir, "SimHei.ttf")
    if os.path.exists(local_font):
        try:
            pdfmetrics.registerFont(TTFont('SimHeiLocal', local_font))
            font_name = 'SimHeiLocal'
            print("✅ 使用本地字体: SimHei.ttf")
            return font_name
        except Exception as e:
            print(f"⚠️  本地字体注册失败: {e}")
    
    # macOS字体
    if sys.platform == 'darwin':
        mac_fonts = [
            ('/System/Library/Fonts/PingFang.ttc', 'PingFang'),
            ('/System/Library/Fonts/STHeiti Light.ttc', 'STHeiti'),
            ('/System/Library/Fonts/Hiragino Sans GB.ttc', 'Hiragino'),
            ('/Library/Fonts/Arial Unicode.ttf', 'ArialUnicode'),
        ]
        for font_path, font_alias in mac_fonts:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_alias, font_path))
                    font_name = font_alias
                    print(f"✅ 成功注册字体: {font_alias}")
                    return font_name
                except Exception as e:
                    print(f"⚠️  字体注册失败 {font_alias}: {e}")
    
    # Linux字体
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
                return font_name
            except Exception as e:
                print(f"⚠️  字体注册失败 {font_alias}: {e}")
    
    # 兜底CID字体
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
    """标准化代码：区分A股和港股市场"""
    code = code.strip()
    
    # 检查是否为港股
    if is_hk_stock(code):
        return normalize_hk_code(code)
    
    # 如果是 6 位数字，判定为 A 股
    if re.match(r'^\d{6}$', code):
        if code.startswith('6'):  # 沪市（包括科创板）
            return f"sh{code}"
        if code.startswith('0') or code.startswith('3'):  # 深市/创业板
            return f"sz{code}"
    
    # 如果已经是带前缀的代码，直接返回
    if code.startswith('sh') or code.startswith('sz'):
        return code
    
    return code

def is_hk_stock(code: str) -> bool:
    """判断是否为港股代码"""
    code = code.strip().upper()
    
    # 以.HK结尾
    if code.endswith('.HK'):
        return True
    
    # 以HK.开头
    if code.startswith('HK.'):
        return True
    
    # 纯数字代码判断
    if code.isdigit():
        # 5位数字（港股通常是5位）
        if len(code) == 5:
            return True
        # 4位数字且以0开头（如0700）
        if len(code) == 4 and code.startswith('0'):
            return True
        # 3位数字且以0开头（如700，补零后是00700）
        if len(code) == 3 and code.startswith('0'):
            return True
    
    return False

def normalize_hk_code(code: str) -> str:
    """标准化港股代码格式"""
    code = code.strip().upper()
    
    # 移除.HK后缀
    if code.endswith('.HK'):
        code = code[:-3]
    
    # 移除HK.前缀
    if code.startswith('HK.'):
        code = code[3:]
    
    # 确保是5位数字
    if code.isdigit():
        code = code.zfill(5)
    
    # 返回标准格式：HK.00700
    return f"HK.{code}"

def parse_stock_list(stocks_input: str):
    """解析股票列表，支持逗号与空格分隔"""
    if not stocks_input:
        return []
    normalized = stocks_input.replace(',', ' ').replace('，', ' ')
    return [item for item in normalized.split() if item]

def is_china_stock_market_open():
    """
    检查今日是否为A股交易日（自动剔除法定节假日）
    """
    try:
        if ak is None:
            print("⚠️  akshare 未安装，跳过交易日检查")
            return True
        # 获取上证指数最新行情
        df = ak.stock_zh_index_daily(symbol="sh000001")
        if df is None or df.empty:
            return True # 接口故障时默认运行，防止漏发
        
        # 比较最后交易日与系统今日日期
        last_trade_date = pd.to_datetime(df.iloc[-1]['date']).date()
        today = datetime.now().date()
        
        # 如果上证最后交易日期不是今天，说明今天休市
        if last_trade_date != today:
            return False
        return True
    except Exception as e:
        print(f"⚠️ 交易日检查异常: {e}")
        return True

def is_hk_stock_market_open():
    """
    检查今日是否为港股交易日
    """
    try:
        if ak is None:
            print("⚠️  akshare 未安装，跳过港股交易日检查")
            return True
        # 使用恒生指数判断港股交易日
        df = ak.stock_hk_index_daily_sina(symbol="HSI")
        if df is None or df.empty:
            return True
        
        last_trade_date = pd.to_datetime(df.iloc[-1]['date']).date()
        today = datetime.now().date()
        
        if last_trade_date != today:
            return False
        return True
    except Exception as e:
        print(f"⚠️ 港股交易日检查异常: {e}")
        return True

def get_name(symbol):
    """获取股票名称 - 支持A股和港股"""
    try:
        # 港股使用免费数据源（AKShare/yfinance）
        if symbol.startswith('HK.'):
            code = symbol.replace('HK.', '')
            
            # 使用免费数据源获取股票名称
            try:
                from src.data.hk_data_sources import HKDataSources
                name = HKDataSources.get_stock_name_fallback(code)
                if name:
                    return name
            except Exception as e:
                print(f"⚠️  获取港股名称失败 {symbol}: {e}")
        
        # A股使用新浪财经接口
        if symbol.startswith('sh') or symbol.startswith('sz'):
            # 新浪财经实时数据接口
            url = f"http://hq.sinajs.cn/list={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://finance.sina.com.cn',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'gbk'
            
            if response.status_code == 200:
                content = response.text
                # 解析新浪财经返回的数据格式
                # 格式：var hq_str_sh600460="士兰微,29.80,29.89,30.50,30.98,29.75,..."
                if '="' in content:
                    data_str = content.split('="')[1].split('"')[0]
                    if data_str:
                        parts = data_str.split(',')
                        if len(parts) > 0:
                            return parts[0]  # 股票名称
        
        # 如果上面失败，尝试使用东方财富接口
        clean_code = re.sub(r'[a-zA-Z]', '', symbol)
        if clean_code:
            # 东方财富股票信息接口
            url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={'1.' if clean_code.startswith('6') else '0.'}{clean_code}&fields=f12,f13,f14"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    return data['data'].get('f14', symbol)
    
    except Exception as e:
        print(f"获取股票名称出错 {symbol}: {e}")
    
    # 返回原始代码
    return symbol

def fetch_kline_data_from_sina(symbol, scale=240, datalen=100):
    """从新浪财经获取K线数据
    
    Args:
        symbol: 股票代码，如 sh600460
        scale: K线周期，240=日线，30=30分钟，5=5分钟，1=1分钟
        datalen: 数据长度
    """
    try:
        # 提取纯数字代码
        clean_code = re.sub(r'[a-zA-Z]', '', symbol)
        if not clean_code:
            print(f"❌ 无效的股票代码: {symbol}")
            return None
        
        # 新浪财经历史数据接口
        # 日线数据
        if scale == 240:
            url = f"https://quotes.sina.cn/cn/api/openapi.php/CN_MarketDataService.getKLineData"
            params = {
                'symbol': symbol.upper(),
                'scale': scale,
                'datalen': datalen,
                'ma': 'no'
            }
        else:
            # 分钟数据
            url = f"https://quotes.sina.cn/cn/api/openapi.php/StockV2Service.getMinLine"
            params = {
                'symbol': symbol.upper(),
                'scale': scale,
                'datalen': datalen
            }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://finance.sina.com.cn',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        print(f"  📡 从新浪财经获取数据: {symbol} scale={scale}")
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"  ❌ HTTP错误: {response.status_code}")
            return None
        
        try:
            data = response.json()
        except:
            # 尝试处理可能的非标准JSON响应
            text = response.text
            if 'day' in text or 'd=' in text:
                # 尝试解析
                try:
                    # 尝试提取JSON部分
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = text[start:end]
                        data = json.loads(json_str)
                    else:
                        print(f"  ❌ 无法解析JSON响应")
                        return None
                except:
                    print(f"  ❌ JSON解析失败")
                    return None
            else:
                print(f"  ❌ 响应不是有效的JSON")
                return None
        
        # 解析新浪财经返回的数据结构
        klines = []
        
        if scale == 240:
            # 日线数据格式
            if 'result' in data and 'data' in data['result']:
                for item in data['result']['data']:
                    try:
                        klines.append({
                            'Date': item['day'],
                            'Open': float(item['open']),
                            'High': float(item['high']),
                            'Low': float(item['low']),
                            'Close': float(item['close']),
                            'Volume': float(item.get('volume', 0))
                        })
                    except:
                        continue
        else:
            # 分钟数据格式
            if 'result' in data and 'data' in data['result']:
                for item in data['result']['data']:
                    try:
                        klines.append({
                            'Date': f"{item['d']} {item['t']}:00",
                            'Open': float(item['o']),
                            'High': float(item['h']),
                            'Low': float(item['l']),
                            'Close': float(item['c']),
                            'Volume': float(item.get('v', 0))
                        })
                    except:
                        continue
        
        if not klines:
            print(f"  ⚠️  未获取到有效数据")
            return None
        
        # 创建DataFrame
        df = pd.DataFrame(klines)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        print(f"    ✓ 获取到 {len(df)} 条数据")
        return df
        
    except Exception as e:
        print(f"  ❌ 从新浪财经获取数据失败 {symbol}: {e}")
        traceback.print_exc()
        return None

def fetch_kline_data_fallback(symbol, scale=240, datalen=100):
    """新浪K线备用接口（json_v2）"""
    try:
        url = (
            "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            f"CN_MarketData.getKLineData?symbol={symbol}&scale={scale}&ma=no&datalen={datalen}"
        )
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return None
        
        data = response.json()
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
        
        return df if not df.empty else None
    except Exception as e:
        print(f"  ❌ 备用接口获取失败 {symbol} scale={scale}: {e}")
        return None

def fetch_kline_data(symbol, scale=240, datalen=100):
    """获取K线数据 - 支持A股和港股"""
    # 港股使用免费数据源
    if symbol.startswith('HK.'):
        return fetch_kline_data_from_hk_sources(symbol, scale, datalen)
    
    # A股使用新浪财经API
    df = fetch_kline_data_from_sina(symbol, scale, datalen)
    if df is None or df.empty:
        df = fetch_kline_data_fallback(symbol, scale, datalen)
    return df

def fetch_kline_data_from_hk_sources(symbol, scale=240, datalen=100):
    """从免费数据源获取港股K线数据（新浪财经/东方财富/AKShare）"""
    try:
        from src.data.hk_data_sources import HKDataSources
        
        # 提取股票代码
        code = symbol.replace('HK.', '')
        
        # 转换周期格式
        period_map = {
            240: '1d',   # 日线
            60: '60m',  # 60分钟
            30: '30m',  # 30分钟
            15: '15m',  # 15分钟
            5: '5m',    # 5分钟
            1: '1m',    # 1分钟
        }
        
        period = period_map.get(scale, '1d')
        
        print(f"  📡 从免费数据源获取港股数据: {symbol} period={period}")
        print(f"    数据源: 新浪财经 → 东方财富 → AKShare")
        
        # 使用多个免费数据源（自动降级）
        df = HKDataSources.get_kline_with_fallback(code, period=period, count=datalen)
        
        if df is not None and not df.empty:
            print(f"    ✓ 获取到 {len(df)} 条数据")
            return df
        else:
            print(f"  ⚠️  未获取到有效数据")
            return None
        
    except ImportError:
        # 不需要额外依赖，新浪财经和东方财富接口只需要requests
        print(f"  ⚠️  模块导入失败，但会尝试使用新浪财经和东方财富接口")
        return None
    except Exception as e:
        print(f"  ❌ 获取港股数据失败 {symbol}: {e}")
        traceback.print_exc()
        return None

def fetch_alternative_1min_data(symbol, days=5):
    """替代方法获取1分钟数据"""
    try:
        print(f"  尝试使用替代方法获取1分钟数据...")
        
        # 先获取日线数据
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
            volume = row['Volume'] if 'Volume' in row else 100000
            
            price_range = high_price - low_price
            minute_vol = volume / 240  # 假设均匀分布
            
            prices = np.linspace(base_price, close_price, 240)
            noise = np.random.normal(0, price_range * 0.1, 240)
            prices = prices + noise
            prices = np.clip(prices, low_price, high_price)
            
            for minute in range(0, 239, 1):  # 减少1，防止越界
                minute_open = prices[minute]
                minute_high = max(prices[minute], prices[minute+1])
                minute_low = min(prices[minute], prices[minute+1])
                minute_close = prices[minute+1]
                
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

def normalize_beijing_time(df):
    """将时间索引规范为北京时间（无时区）"""
    if df is None or df.empty:
        return df
    
    if not isinstance(df.index, pd.DatetimeIndex):
        return df
    
    if df.index.tz is None:
        return df
    
    try:
        df = df.copy()
        df.index = df.index.tz_convert('Asia/Shanghai').tz_localize(None)
        return df
    except Exception:
        return df

def filter_trading_hours(df):
    """仅保留A股交易时段数据"""
    if df is None or df.empty:
        return df
    
    try:
        df = normalize_beijing_time(df)
        if not isinstance(df.index, pd.DatetimeIndex):
            return df
        
        morning = df.between_time('09:30', '11:30')
        afternoon = df.between_time('13:00', '15:00')
        filtered = pd.concat([morning, afternoon]).sort_index()
        return filtered
    except Exception:
        return df

def is_intraday_data(df):
    """判断是否为日内数据（含时间）"""
    if df is None or df.empty or not isinstance(df.index, pd.DatetimeIndex):
        return False
    return any((df.index.hour != 0) | (df.index.minute != 0))

def format_beijing_time(dt):
    """格式化北京时间"""
    if dt is None:
        return "未知"
    if getattr(dt, "tzinfo", None) is not None:
        try:
            dt = dt.tz_convert('Asia/Shanghai').tz_localize(None)
        except Exception:
            pass
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def calculate_technical_indicators(df):
    """计算技术指标（增强版）"""
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # 移动平均线
    window_5 = min(5, len(df))
    window_10 = min(10, len(df))
    window_20 = min(20, len(df))
    window_60 = min(60, len(df))
    
    if 'Close' in df.columns:
        df['MA5'] = df['Close'].rolling(window=window_5, min_periods=1).mean()
        df['MA10'] = df['Close'].rolling(window=window_10, min_periods=1).mean()
        df['MA20'] = df['Close'].rolling(window=window_20, min_periods=1).mean()
        df['MA60'] = df['Close'].rolling(window=window_60, min_periods=1).mean()
        df['MA250'] = df['Close'].rolling(window=min(250, len(df)), min_periods=1).mean()
    
    # MACD
    if 'Close' in df.columns and len(df) >= 26:
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['DIF'] = exp12 - exp26
        df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
        df['MACD'] = 2 * (df['DIF'] - df['DEA'])
    
    # RSI
    if 'Close' in df.columns and len(df) >= 14:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=min(14, len(df))).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=min(14, len(df))).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        df['RSI'] = df['RSI'].fillna(50)
    
    # 布林带
    if 'Close' in df.columns and len(df) >= 20:
        df['BB_Middle'] = df['Close'].rolling(window=min(20, len(df))).mean()
        df['BB_Std'] = df['Close'].rolling(window=min(20, len(df))).std()
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
    
    # 成交量均线
    if 'Volume' in df.columns:
        df['Volume_MA5'] = df['Volume'].rolling(window=min(5, len(df)), min_periods=1).mean()
        df['Volume_MA10'] = df['Volume'].rolling(window=min(10, len(df)), min_periods=1).mean()
        
        # 量比
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA5']
        df['Volume_Ratio'] = df['Volume_Ratio'].replace([np.inf, -np.inf], 1).fillna(1)
    
    # KDJ指标
    if 'High' in df.columns and 'Low' in df.columns and 'Close' in df.columns and len(df) >= 9:
        window_9 = min(9, len(df))
        low_list = df['Low'].rolling(window=window_9, min_periods=1).min()
        high_list = df['High'].rolling(window=window_9, min_periods=1).max()
        rsv = ((df['Close'] - low_list) / (high_list - low_list) * 100).fillna(50)
        df['K'] = rsv.ewm(com=2, adjust=False).mean()
        df['D'] = df['K'].ewm(com=2, adjust=False).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']
    
    # 威廉指标
    if 'High' in df.columns and 'Low' in df.columns and 'Close' in df.columns and len(df) >= 14:
        high_14 = df['High'].rolling(window=min(14, len(df)), min_periods=1).max()
        low_14 = df['Low'].rolling(window=min(14, len(df)), min_periods=1).min()
        df['WR'] = ((high_14 - df['Close']) / (high_14 - low_14) * 100).fillna(50)
    
    # OBV
    if 'Close' in df.columns and 'Volume' in df.columns:
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
    if 'High' in df.columns and 'Low' in df.columns and 'Close' in df.columns:
        df['Amplitude'] = ((df['High'] - df['Low']) / df['Close'].shift(1).replace(0, 1)) * 100
        df['Amplitude'] = df['Amplitude'].fillna(0)
    
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

def get_market_indices_data(is_hk=False):
    """获取市场指数数据 - 使用新浪财经"""
    indices_data = {}
    
    if is_hk:
        hk_indices = {
            'HSI': '恒生指数',
            'HSCEI': '恒生国企指数',
            'HSTECH': '恒生科技指数',
            'HSCCI': '恒生综合指数',
            'CES100': '恒生中国企业精选100'
        }
        
        print("📊 获取港股指数数据...")
        try:
            import akshare as ak
        except Exception as e:
            print(f"  ❌ AKShare不可用，无法获取港股指数: {e}")
            return indices_data
        
        for code, name in hk_indices.items():
            print(f"  获取 {name}...")
            try:
                df = ak.stock_hk_index_daily_sina(symbol=code)
                if df is not None and not df.empty:
                    df = df.rename(columns={
                        'date': 'Date',
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    })
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                    df.sort_index(inplace=True)
                    df = df.tail(150)
                    df = calculate_technical_indicators(df)
                    indices_data[code] = {
                        'name': name,
                        'data': df,
                        'type': 'HK'
                    }
                    print(f"    ✓ 获取成功: {len(df)} 条数据")
                else:
                    print(f"    ❌ 获取失败")
            except Exception as e:
                print(f"    ❌ 获取失败: {e}")
    else:
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
            
            try:
                # 使用新浪财经接口获取指数数据
                df = fetch_kline_data(code, 240, 150)
                
                if df is not None and not df.empty:
                    df = calculate_technical_indicators(df)
                    indices_data[code] = {
                        'name': name,
                        'data': df,
                        'type': 'A'
                    }
                    print(f"    ✓ 获取成功: {len(df)} 条数据")
                else:
                    print(f"    ❌ 获取失败")
            except Exception as e:
                print(f"    ❌ 获取失败: {e}")
    
    return indices_data

def load_sector_index_map():
    """加载行业代码对照表"""
    try:
        import json
        import os
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'sector_index_map.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载行业代码对照表失败: {e}")
    return {'code_to_name': {}, 'name_to_code': {}}

def get_sector_index_name(sector_input):
    """根据代码或名称获取行业名称"""
    sector_map = load_sector_index_map()
    code_to_name = sector_map.get('code_to_name', {})
    name_to_code = sector_map.get('name_to_code', {})
    
    # 如果是代码（BK开头）
    if sector_input.startswith('BK') and sector_input in code_to_name:
        return code_to_name[sector_input]
    # 如果是名称
    elif sector_input in name_to_code:
        return sector_input
    # 尝试模糊匹配
    else:
        for code, name in code_to_name.items():
            if sector_input in name or name in sector_input:
                return name
    return None

def get_sector_indices_data(sector_input=None, count=150):
    """
    获取行业板块指数数据
    
    Args:
        sector_input: 行业代码（如"BK1031"）或行业名称（如"光伏设备"）
        count: 获取数据条数
    
    Returns:
        dict: {code: {'name': name, 'data': df, 'type': 'SECTOR'}}
    """
    sector_data = {}
    
    if not sector_input:
        return sector_data
    
    try:
        import akshare as ak
    except Exception as e:
        print(f"  ❌ AKShare不可用，无法获取行业板块指数: {e}")
        return sector_data
    
    # 获取行业名称
    sector_name = get_sector_index_name(sector_input)
    if not sector_name:
        print(f"  ❌ 未找到行业: {sector_input}")
        return sector_data
    
    print(f"📊 获取行业板块指数数据: {sector_name}")
    
    try:
        # 获取行业板块日线K线
        df = ak.stock_board_industry_hist_em(symbol=sector_name, period="日k", adjust="")
        
        if df is not None and not df.empty:
            # 标准化列名
            df = df.rename(columns={
                '日期': 'Date',
                '开盘': 'Open',
                '收盘': 'Close',
                '最高': 'High',
                '最低': 'Low',
                '成交量': 'Volume'
            })
            
            # 处理日期
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
            # 限制数据量
            df = df.tail(count)
            
            # 计算技术指标
            df = calculate_technical_indicators(df)
            
            # 获取行业代码
            sector_map = load_sector_index_map()
            name_to_code = sector_map.get('name_to_code', {})
            sector_code = name_to_code.get(sector_name, sector_input)
            
            sector_data[sector_code] = {
                'name': sector_name,
                'data': df,
                'type': 'SECTOR'
            }
            print(f"    ✓ 获取成功: {len(df)} 条数据")
        else:
            print(f"    ❌ 数据为空")
    except Exception as e:
        print(f"    ❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()
    
    return sector_data

def get_market_summary_analysis(indices_data, market_label="A股"):
    """生成市场综合分析"""
    if not indices_data:
        return "【市场指数数据获取失败】\n\n"
    
    analysis = f"【{market_label}市场综合分析】\n\n"
    
    for code, info in indices_data.items():
        df = info['data']
        name = info['name']
        
        if df is not None and not df.empty and len(df) >= 20:
            last = df.iloc[-1]
            
            trend = "横盘"
            if 'MA5' in last and 'MA10' in last and 'MA20' in last:
                if last['MA5'] > last['MA10'] > last['MA20']:
                    trend = "多头排列"
                elif last['MA5'] < last['MA10'] < last['MA20']:
                    trend = "空头排列"
            
            rsi_status = "中性"
            if 'RSI' in last:
                if last['RSI'] > 70:
                    rsi_status = "超买"
                elif last['RSI'] < 30:
                    rsi_status = "超卖"
            
            analysis += f"{name}:\n"
            analysis += f"  现价: {last['Close']:.2f}"
            
            if 'MA5' in last:
                analysis += f", MA5: {last['MA5']:.2f}"
            if 'MA10' in last:
                analysis += f", MA10: {last['MA10']:.2f}"
            
            analysis += f"\n  趋势: {trend}"
            
            if 'RSI' in last:
                analysis += f", RSI: {last['RSI']:.1f}({rsi_status})"
            
            if 'MACD' in last:
                analysis += f"\n  MACD: {last['MACD']:.3f}"
            
            if 'K' in last and 'D' in last and 'J' in last:
                analysis += f", KDJ: K={last['K']:.1f} D={last['D']:.1f} J={last['J']:.1f}"
            
            analysis += "\n\n"
    
    return analysis

def get_market_sentiment_analysis(indices_data, market_label="A股"):
    """生成市场情绪分析"""
    if not indices_data:
        return ""
    
    analysis = f"【{market_label}市场情绪分析】\n\n"
    
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
            
            if 'RSI' in last:
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
        if df is not None and len(df) >= 5 and 'Amplitude' in df.columns:
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

def create_candle_chart(df, title, filename, max_points=60):
    """创建K线图表（增强版，添加成交量和量比图表）"""
    if df is None or len(df) < 5:
        return False
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import matplotlib.font_manager as fm
        
        plot_data = df.tail(min(max_points, len(df))).copy()
        plot_data = normalize_beijing_time(plot_data)
        
        fig, axes = plt.subplots(4, 1, figsize=(12, 12), 
                                 gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        
        ax1, ax2, ax3, ax4 = axes
        
        # 设置中文字体，避免乱码
        font_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "SimHei.ttf"),
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
        ]
        font_set = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    fm.fontManager.addfont(font_path)
                    font_prop = fm.FontProperties(fname=font_path)
                    font_name = font_prop.get_name()
                    plt.rcParams['font.sans-serif'] = [font_name, 'Arial', 'DejaVu Sans']
                    plt.rcParams['axes.unicode_minus'] = False
                    font_set = True
                    break
                except Exception:
                    continue
        if not font_set:
            plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        
        dates = plot_data.index.to_list()
        intraday = is_intraday_data(plot_data)
        x = np.arange(len(dates)) if intraday else mdates.date2num(dates)
        opens = plot_data['Open'].values
        highs = plot_data['High'].values
        lows = plot_data['Low'].values
        closes = plot_data['Close'].values
        volumes = plot_data['Volume'].values if 'Volume' in plot_data.columns else np.zeros(len(dates))
        
        volume_ratios = plot_data['Volume_Ratio'].values if 'Volume_Ratio' in plot_data.columns else None
        
        # 绘制K线
        for i, date in enumerate(dates):
            color = 'red' if closes[i] >= opens[i] else 'green'
            
            ax1.plot([x[i], x[i]], [highs[i], max(opens[i], closes[i])], 
                    color=color, linewidth=1)
            ax1.plot([x[i], x[i]], [min(opens[i], closes[i]), lows[i]], 
                    color=color, linewidth=1)
            
            from matplotlib.patches import Rectangle
            
            body_bottom = min(opens[i], closes[i])
            body_height = abs(closes[i] - opens[i])
            
            if body_height > 0:
                rect = Rectangle(
                    (x[i] - 0.3, body_bottom),
                    0.6,
                    body_height,
                    facecolor=color,
                    edgecolor=color,
                    alpha=0.8
                )
                ax1.add_patch(rect)
        
        if 'MA5' in plot_data.columns:
            ax1.plot(x, plot_data['MA5'], 'orange', linewidth=1.5, label='MA5')
        if 'MA10' in plot_data.columns:
            ax1.plot(x, plot_data['MA10'], 'blue', linewidth=1.5, label='MA10')
        if 'MA20' in plot_data.columns:
            ax1.plot(x, plot_data['MA20'], 'purple', linewidth=1.5, label='MA20')
        
        if 'BB_Upper' in plot_data.columns:
            ax1.plot(x, plot_data['BB_Upper'], 'gray', linewidth=1, label='BB Upper', alpha=0.5)
            ax1.plot(x, plot_data['BB_Middle'], 'black', linewidth=1, label='BB Middle', alpha=0.5)
            ax1.plot(x, plot_data['BB_Lower'], 'gray', linewidth=1, label='BB Lower', alpha=0.5)
        
        english_title = title.replace('日线', 'Daily').replace('周线', 'Weekly')\
                            .replace('月线', 'Monthly').replace('分钟', 'Min')
        ax1.set_title(english_title, fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price')
        ax1.legend(loc='upper left', fontsize='small')
        ax1.grid(True, alpha=0.3)
        
        if not intraday:
            ax1.xaxis_date()
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # MACD
        if 'MACD' in plot_data.columns:
            macd_colors = ['red' if v >= 0 else 'green' for v in plot_data['MACD']]
            ax2.bar(x, plot_data['MACD'], color=macd_colors, alpha=0.7, width=0.8)
            ax2.plot(x, plot_data['DIF'], 'black', linewidth=1.5, label='DIF')
            ax2.plot(x, plot_data['DEA'], 'orange', linewidth=1.5, label='DEA')
            ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
        
        ax2.set_ylabel('MACD')
        ax2.legend(loc='upper left', fontsize='small')
        ax2.grid(True, alpha=0.3)
        if not intraday:
            ax2.xaxis_date()
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # KDJ
        if 'K' in plot_data.columns and 'D' in plot_data.columns and 'J' in plot_data.columns:
            ax3.plot(x, plot_data['K'], 'blue', linewidth=1.5, label='K')
            ax3.plot(x, plot_data['D'], 'orange', linewidth=1.5, label='D')
            ax3.plot(x, plot_data['J'], 'purple', linewidth=1.5, label='J')
            ax3.axhline(y=80, color='red', linestyle='--', linewidth=0.5, alpha=0.5)
            ax3.axhline(y=20, color='green', linestyle='--', linewidth=0.5, alpha=0.5)
            ax3.axhline(y=50, color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
        
        ax3.set_ylabel('KDJ')
        ax3.set_ylim(-20, 120)
        ax3.legend(loc='upper left', fontsize='small')
        ax3.grid(True, alpha=0.3)
        if not intraday:
            ax3.xaxis_date()
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
        # 成交量+量比
        ax4_volume = ax4
        ax4_ratio = ax4.twinx()
        
        volume_colors = ['red' if closes[i] >= opens[i] else 'green' for i in range(len(dates))]
        ax4_volume.bar(x, volumes, color=volume_colors, alpha=0.7, width=0.8, label='Volume')
        
        if 'Volume_MA5' in plot_data.columns:
            ax4_volume.plot(x, plot_data['Volume_MA5'], 'orange', linewidth=1.5, label='Volume MA5')
        if 'Volume_MA10' in plot_data.columns:
            ax4_volume.plot(x, plot_data['Volume_MA10'], 'blue', linewidth=1.5, label='Volume MA10')
        
        ax4_volume.set_xlabel('Date')
        ax4_volume.set_ylabel('Volume', color='black')
        ax4_volume.tick_params(axis='y', labelcolor='black')
        
        if max(volumes) > 10000:
            ax4_volume.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
        
        if volume_ratios is not None:
            ax4_ratio.plot(x, volume_ratios, 'purple', linewidth=2, label='Volume Ratio', linestyle='-', marker='o', markersize=3)
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
        if not intraday:
            ax4_volume.xaxis_date()
            ax4_volume.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.setp(ax4_volume.xaxis.get_majorticklabels(), rotation=45)
        else:
            tick_count = min(6, len(x))
            tick_positions = np.linspace(0, len(x) - 1, tick_count, dtype=int)
            tick_labels = [dates[i].strftime('%m-%d %H:%M') for i in tick_positions]
            for ax in [ax1, ax2, ax3, ax4_volume]:
                ax.set_xticks(tick_positions)
                ax.set_xticklabels(tick_labels, rotation=45)
        
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
        traceback.print_exc()
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
            
            if create_candle_chart(df, title, img_path, max_points=60):
                charts_created += 1
    
    return charts_created

# ==================== 4. PDF报告生成 ====================

def _format_range(df):
    """格式化数据区间"""
    if df is None or df.empty:
        return "无数据"
    
    start = df.index.min()
    end = df.index.max()
    if pd.isna(start) or pd.isna(end):
        return "无数据"
    
    needs_time = any([
        getattr(start, "hour", 0) != 0,
        getattr(start, "minute", 0) != 0,
        getattr(end, "hour", 0) != 0,
        getattr(end, "minute", 0) != 0
    ])
    fmt = "%Y-%m-%d %H:%M" if needs_time else "%Y-%m-%d"
    return f"{start.strftime(fmt)} ~ {end.strftime(fmt)} ({len(df)}条)"

def _get_trend_status(last):
    """根据均线判断趋势"""
    if last is None:
        return "未知"
    if all(k in last for k in ['MA5', 'MA10', 'MA20']):
        if last['MA5'] > last['MA10'] > last['MA20']:
            return "多头排列"
        if last['MA5'] < last['MA10'] < last['MA20']:
            return "空头排列"
    return "震荡/中性"

def _build_report_summary(stock_name, stock_code, stock_data_map, indices_data):
    """生成结构化摘要文本"""
    summary_lines = []
    day_df = stock_data_map.get('day')
    
    if day_df is not None and not day_df.empty:
        last = day_df.iloc[-1]
        trend = _get_trend_status(last)
        rsi_status = "中性"
        if 'RSI' in last:
            rsi_status = "超买" if last['RSI'] > 70 else ("超卖" if last['RSI'] < 30 else "中性")
        macd_status = "多头" if last.get('MACD', 0) > 0 else "空头"
        
        summary_lines.append(
            f"{stock_name}({stock_code}) 日线收盘: {last['Close']:.2f}，趋势: {trend}，RSI: {rsi_status}，MACD: {macd_status}。"
        )
    else:
        summary_lines.append(f"{stock_name}({stock_code}) 日线数据不足，无法生成核心趋势摘要。")
    
    if indices_data:
        market_label = "港股" if stock_code.startswith("HK.") else "A股"
        sector_count = sum(1 for info in indices_data.values() if info.get('type') == 'SECTOR')
        market_count = len(indices_data) - sector_count
        if sector_count > 0:
            summary_lines.append(f"本次报告包含 {market_count} 个{market_label}主要指数和 {sector_count} 个行业板块指数的综合分析。")
        else:
            summary_lines.append(f"本次报告包含 {market_count} 个{market_label}主要指数的综合分析。")
    
    return summary_lines

def _build_parameters_table(meta, stock_data_map, indices_data):
    """生成参数与数据范围表格"""
    indicator_params = meta.get('indicator_params', {})
    indicator_text = (
        f"MA:{','.join(map(str, indicator_params.get('ma_windows', [])))}; "
        f"MACD:{'/'.join(map(str, indicator_params.get('macd', [])))}; "
        f"RSI:{indicator_params.get('rsi', '')}; "
        f"BB:{indicator_params.get('boll', '')}; "
        f"KDJ:{indicator_params.get('kdj', '')}; "
        f"WR:{indicator_params.get('wr', '')}; "
        f"VOL_MA:{','.join(map(str, indicator_params.get('volume_ma', [])))}"
    )
    
    table_data = [
        ['项目', '说明'],
        ['生成时间', meta.get('generated_at', '')],
        ['数据来源', meta.get('data_source', '未知')],
        ['指数来源', meta.get('index_source', '未知')],
        ['1分钟数据来源', meta.get('one_min_source', '未知')],
        ['日线范围', _format_range(stock_data_map.get('day'))],
        ['周线范围', _format_range(stock_data_map.get('week'))],
        ['月线范围', _format_range(stock_data_map.get('month'))],
        ['30分钟范围', _format_range(stock_data_map.get('30m'))],
        ['5分钟范围', _format_range(stock_data_map.get('5m'))],
        ['1分钟范围', _format_range(stock_data_map.get('1m'))],
        ['指标参数', indicator_text]
    ]
    
    if indices_data:
        index_ranges = [
            _format_range(info.get('data'))
            for info in indices_data.values()
            if info.get('data') is not None
        ]
        if index_ranges:
            table_data.insert(5, ['指数数据范围', f"{len(index_ranges)} 个指数，示例: {index_ranges[0]}"])
    
    return table_data

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
        
        price_style = ParagraphStyle(
            name='PriceStyle',
            parent=styles['Heading2'],
            fontName=FONT_NAME,
            fontSize=18,
            alignment=1,
            spaceAfter=8
        )
        
        change_style = ParagraphStyle(
            name='ChangeStyle',
            parent=styles['Heading2'],
            fontName=FONT_NAME,
            fontSize=14,
            alignment=1,
            spaceAfter=15
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
        
        # 判断是否为行业指数报告（BK开头）
        is_sector_report = stock_code.startswith('BK')
        
        # 封面页
        story.append(Spacer(1, 50))
        if is_sector_report:
            story.append(Paragraph(f"{stock_name}行业板块指数分析报告", title_style))
        else:
            story.append(Paragraph(f"{stock_name}技术分析报告", title_style))
        story.append(Paragraph(f"({stock_code})", subtitle_style))
        story.append(Spacer(1, 20))
        
        day_df = stock_data_map.get('day')
        if day_df is not None and len(day_df) >= 2:
            last = day_df.iloc[-1]
            prev = day_df.iloc[-2]
            latest_price = last.get('Close', 0)
            prev_close = prev.get('Close', latest_price)
            change = latest_price - prev_close
            change_percent = (change / prev_close * 100) if prev_close else 0
            data_time = format_beijing_time(day_df.index[-1])
            
            story.append(Paragraph(f"最新价格: {latest_price:.2f}", price_style))
            if change >= 0:
                change_style.textColor = colors.red
                change_text = f"涨跌幅: +{change:.2f} (+{change_percent:.2f}%)"
            else:
                change_style.textColor = colors.green
                change_text = f"涨跌幅: {change:.2f} ({change_percent:.2f}%)"
            story.append(Paragraph(change_text, change_style))
            story.append(Paragraph(f"数据时间: {data_time}", normal_style))
        else:
            story.append(Paragraph("最新价格数据获取中...", normal_style))
        
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph("【数据说明】", normal_style))
        story.append(Paragraph("本报告仅提供技术指标数据计算和展示，不包含任何投资建议或操作指导。", normal_style))
        story.append(Paragraph("所有数据仅供参考，不构成任何投资决策依据。", normal_style))
        story.append(PageBreak())
        
        # 结构化摘要与参数信息
        story.append(Paragraph("报告摘要", section_style))
        for line in _build_report_summary(stock_name, stock_code, stock_data_map, indices_data):
            story.append(Paragraph(line, normal_style))
        story.append(Spacer(1, 10))
        
        meta = stock_data_map.get('_meta', {})
        if meta:
            story.append(Paragraph("数据与参数", section_style))
            params_table = _build_parameters_table(meta, stock_data_map, indices_data)
            params_table_obj = Table(params_table, colWidths=[110, 400])
            params_table_obj.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(params_table_obj)
        
        story.append(PageBreak())
        
        # 分离市场指数和行业指数
        market_indices = {k: v for k, v in indices_data.items() if v.get('type') != 'SECTOR'}
        sector_indices = {k: v for k, v in indices_data.items() if v.get('type') == 'SECTOR'}
        
        # 第一部分：市场指数综合分析
        story.append(Paragraph("一、市场指数综合分析", section_style))
        story.append(Spacer(1, 10))
        
        market_label = "港股" if stock_code.startswith("HK.") else "A股"
        market_analysis = get_market_summary_analysis(market_indices, market_label=market_label)
        if market_analysis:
            for line in market_analysis.split('\n'):
                if line.strip():
                    story.append(Paragraph(line, normal_style))
        else:
            story.append(Paragraph("市场指数数据获取失败", normal_style))
        
        # 添加市场指数图表
        story.append(Spacer(1, 10))
        story.append(Paragraph("主要指数日线图:", normal_style))
        
        index_charts = []
        for code, info in market_indices.items():
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
        
        # 如果有行业指数，单独展示
        if sector_indices:
            story.append(PageBreak())
            story.append(Paragraph("一.五、行业板块指数分析", section_style))
            story.append(Spacer(1, 10))
            
            for code, info in sector_indices.items():
                df = info['data']
                name = info['name']
                if df is not None and len(df) >= 20:
                    last = df.iloc[-1]
                    trend = _get_trend_status(last)
                    rsi_status = "中性"
                    if 'RSI' in last:
                        rsi_status = "超买" if last['RSI'] > 70 else ("超卖" if last['RSI'] < 30 else "中性")
                    
                    story.append(Paragraph(f"{name}:", normal_style))
                    story.append(Paragraph(f"  现价: {last['Close']:.2f}, 趋势: {trend}, RSI: {rsi_status}", normal_style))
                    story.append(Spacer(1, 5))
            
            # 添加行业指数图表
            story.append(Spacer(1, 10))
            story.append(Paragraph("行业板块指数日线图:", normal_style))
            
            sector_charts = []
            for code, info in sector_indices.items():
                img_path = os.path.join(temp_dir, f"index_{code}.png")
                if os.path.exists(img_path):
                    try:
                        from PIL import Image as PILImage
                        pil_img = PILImage.open(img_path)
                        img_width, img_height = pil_img.size
                        ratio = min(250/img_width, 150/img_height)
                        
                        img = Image(img_path, width=img_width*ratio, height=img_height*ratio)
                        sector_charts.append([Paragraph(info['name'], normal_style), img])
                    except:
                        continue
            
            if sector_charts:
                rows = []
                for i in range(0, len(sector_charts), 2):
                    row = []
                    row.append(sector_charts[i][0])
                    row.append(sector_charts[i][1])
                    if i+1 < len(sector_charts):
                        row.append(sector_charts[i+1][0])
                        row.append(sector_charts[i+1][1])
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
        
        sentiment_analysis = get_market_sentiment_analysis(market_indices, market_label=market_label)
        if sentiment_analysis:
            for line in sentiment_analysis.split('\n'):
                if line.strip():
                    story.append(Paragraph(line, normal_style))
        
        story.append(PageBreak())
        
        # 第三部分：技术分析（个股或行业指数）
        if is_sector_report:
            story.append(Paragraph("三、行业指数技术分析", section_style))
        else:
            story.append(Paragraph("三、个股技术分析", section_style))
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
                        
                        tech_data = []
                        if 'RSI' in last:
                            rsi_status = '超买区' if last['RSI'] > 70 else ('超卖区' if last['RSI'] < 30 else '正常区间')
                            tech_data.append(['RSI(14)', f"{last['RSI']:.1f}", rsi_status])
                        
                        if 'MACD' in last:
                            macd_status = '多头' if last['MACD'] > 0 else '空头'
                            tech_data.append(['MACD', f"{last['MACD']:.3f}", macd_status])
                        
                        if 'K' in last:
                            k_status = '超买' if last['K'] > 80 else ('超卖' if last['K'] < 20 else '正常')
                            tech_data.append(['KDJ-K', f"{last['K']:.1f}", k_status])
                        
                        if 'D' in last:
                            tech_data.append(['KDJ-D', f"{last['D']:.1f}", ''])
                        
                        if 'J' in last:
                            tech_data.append(['KDJ-J', f"{last['J']:.1f}", ''])
                        
                        if 'WR' in last:
                            wr_status = '超买区' if last['WR'] < 20 else ('超卖区' if last['WR'] > 80 else '正常区间')
                            tech_data.append(['威廉指标', f"{last['WR']:.1f}", wr_status])
                        
                        if 'OBV' in last:
                            tech_data.append(['OBV', f"{last['OBV']:.0f}", '能量潮指标'])
                        
                        # 如果tech_data不为空，添加表头
                        if tech_data:
                            tech_data.insert(0, ['技术指标', '数值', '状态描述'])
                        
                        volume_data = [
                            ['成交量指标', '数值', '说明']
                        ]
                        
                        if 'Volume' in last:
                            volume_data.append(['成交量', f"{last['Volume']:.0f}", ''])
                        
                        if 'Volume_Ratio' in last:
                            vr_status = '放量' if last['Volume_Ratio'] > 1.5 else ('缩量' if last['Volume_Ratio'] < 0.8 else '正常')
                            volume_data.append(['量比', f"{last['Volume_Ratio']:.2f}", vr_status])
                        
                        if 'Amplitude' in last:
                            volume_data.append(['振幅', f"{last['Amplitude']:.2f}%", '波动性指标'])
                        
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
                        
                        if tech_data:
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
                        
                        if len(volume_data) > 1:
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

def process_multiple_stocks(stock_codes_input, output_folder, sector_input=None):
    """
    批量处理多个股票
    
    Args:
        stock_codes_input: 股票代码列表（空格或逗号分隔）
        output_folder: 输出文件夹
        sector_input: 行业代码（如"BK1031"）或行业名称（如"光伏设备"），可选
    """
    stock_codes = parse_stock_list(stock_codes_input)
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
        
        # 检查是否为行业代码或行业名称（误输入）
        sector_map = load_sector_index_map()
        name_to_code = sector_map.get('name_to_code', {})
        code_to_name = sector_map.get('code_to_name', {})
        
        # 首先检查是否为行业代码（BK开头）
        if code_input.startswith('BK') and code_input in code_to_name:
            sector_name = code_to_name[code_input]
            print(f"⚠️  检测到行业代码 '{code_input}' ({sector_name})，这不是股票代码")
            print(f"   提示: 如需生成行业报告，请使用 --sector 参数")
            print(f"   示例: python3 github_stock_bot.py --mode manual --stocks \"688630\" --sector \"{code_input}\"")
            failed_reports.append((code_input, code_input, f"输入的是行业代码而非股票代码: {sector_name}"))
            continue
        
        # 检查是否包含点号分隔的多个行业名称（如"航空航天.互联网服务"）
        if '.' in code_input or '，' in code_input or ',' in code_input:
            parts = re.split(r'[.，,]', code_input)
            matched_parts = []
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if part in name_to_code:
                    matched_parts.append(part)
                else:
                    # 模糊匹配：检查部分是否在行业名称中，或行业名称在部分中
                    matched = False
                    for sector_name in name_to_code.keys():
                        if part in sector_name or sector_name in part:
                            matched_parts.append(sector_name)
                            matched = True
                            break
                    
                    # 如果还没匹配到，尝试更宽松的匹配（包含关键词）
                    if not matched:
                        # 提取关键词（2-4个字符的子串）
                        keywords = []
                        for i in range(len(part)):
                            for j in range(i+2, min(i+5, len(part)+1)):
                                keywords.append(part[i:j])
                        
                        for sector_name in name_to_code.keys():
                            # 检查是否有共同的关键词
                            if any(keyword in sector_name for keyword in keywords if len(keyword) >= 2):
                                matched_parts.append(sector_name)
                                matched = True
                                break
                    
                    # 如果仍然没匹配到，但包含中文字符且不像股票代码，也认为是可能的行业名称
                    if not matched and re.search(r'[\u4e00-\u9fa5]', part) and len(part) >= 2:
                        # 检查是否像股票代码
                        is_likely_code = re.match(r'^\d{4,6}$', part) or part.startswith(('BK', 'sh', 'sz', 'HK'))
                        if not is_likely_code:
                            matched_parts.append(part)
            
            # 如果至少匹配到一个行业，就认为是行业名称组合
            if matched_parts:
                print(f"⚠️  检测到多个行业名称组合: {code_input}")
                print(f"   识别到的行业: {', '.join(matched_parts)}")
                print(f"   提示: 行业报告需要分别生成，请使用 --sector 参数")
                print(f"   示例: python3 github_stock_bot.py --mode manual --stocks \"688630\" --sector \"{matched_parts[0]}\"")
                failed_reports.append((code_input, code_input, f"多个行业名称组合: {', '.join(matched_parts)}"))
                continue
        
        # 完全匹配检查
        if code_input in name_to_code:
            print(f"⚠️  检测到行业名称 '{code_input}'，这不是股票代码")
            print(f"   提示: 如需生成行业报告，请使用 --sector 参数")
            print(f"   示例: python3 github_stock_bot.py --mode manual --stocks \"688630\" --sector \"{code_input}\"")
            failed_reports.append((code_input, code_input, "输入的是行业名称而非股票代码"))
            continue
        
        # 如果输入看起来不像股票代码（不是数字，不是BK开头，不是sh/sz/HK开头）
        is_likely_stock_code = (
            re.match(r'^\d{4,6}$', code_input) or 
            code_input.startswith('BK') or 
            code_input.startswith(('sh', 'sz', 'HK'))
        )
        
        # 如果包含中文字符且不像股票代码，进行模糊匹配
        if not is_likely_stock_code and re.search(r'[\u4e00-\u9fa5]', code_input):
            matched_sectors = []
            for sector_name in name_to_code.keys():
                # 检查输入是否包含行业名称的关键部分，或行业名称包含输入
                if (len(code_input) >= 2 and 
                    (code_input in sector_name or sector_name in code_input or 
                     any(word in sector_name for word in code_input if len(word) >= 2))):
                    matched_sectors.append(sector_name)
            
            if matched_sectors:
                print(f"⚠️  输入 '{code_input}' 看起来不像股票代码")
                print(f"   检测到可能的行业名称: {', '.join(matched_sectors[:3])}")
                print(f"   提示: 如需生成行业报告，请使用 --sector 参数")
                print(f"   示例: python3 github_stock_bot.py --mode manual --stocks \"688630\" --sector \"{matched_sectors[0]}\"")
                failed_reports.append((code_input, code_input, f"可能是行业名称而非股票代码: {matched_sectors[0]}"))
                continue
        
        stock_code = normalize_code(code_input)
        print(f"📈 分析股票: {stock_code}")
        
        stock_name = get_name(stock_code)
        
        # 如果获取股票名称失败或名称与输入相同，可能是行业名称
        if not stock_name or stock_name == code_input:
            # 检查是否是行业名称的模糊匹配
            matched_sectors = []
            for sector_name, sector_code in name_to_code.items():
                if code_input in sector_name or sector_name in code_input:
                    matched_sectors.append(sector_name)
            
            if matched_sectors:
                print(f"⚠️  无法获取股票数据，检测到可能的行业名称: {', '.join(matched_sectors[:3])}")
                print(f"   提示: 如需生成行业报告，请使用 --sector 参数")
                failed_reports.append((code_input, code_input, f"可能是行业名称而非股票代码: {matched_sectors[0]}"))
                continue
            else:
                print(f"📛 股票名称: {stock_name or '未知'}")
        else:
            print(f"📛 股票名称: {stock_name}")
        
        timestamp = datetime.now().strftime('%H%M%S')
        temp_dir = os.path.join(output_folder, f"temp_{stock_code}_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        print(f"📁 临时目录: {temp_dir}")
        
        print("\n1️⃣  获取市场指数数据...")
        is_hk = stock_code.startswith('HK.')
        indices_data = get_market_indices_data(is_hk=is_hk)
        print(f"✅ 获取到 {len(indices_data)} 个市场指数数据")
        
        # 如果指定了行业，获取行业板块指数
        sector_indices_data = {}
        if sector_input:
            print(f"\n1️⃣.5  获取行业板块指数数据...")
            sector_indices_data = get_sector_indices_data(sector_input, count=150)
            if sector_indices_data:
                print(f"✅ 获取到 {len(sector_indices_data)} 个行业板块指数数据")
                # 合并到 indices_data
                indices_data.update(sector_indices_data)
            else:
                print(f"⚠️  未获取到行业板块指数数据")
        
        print("\n2️⃣  获取个股数据...")
        stock_data_map = {}
        
        # 判断数据源
        data_source = '新浪财经/东方财富' if is_hk else '新浪财经'
        
        report_meta = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': data_source,
            'index_source': '新浪财经(港股指数)' if is_hk else '新浪财经',
            'indicator_params': {
                'ma_windows': [5, 10, 20, 60, 250],
                'macd': [12, 26, 9],
                'rsi': 14,
                'boll': 20,
                'kdj': 9,
                'wr': 14,
                'volume_ma': [5, 10]
            }
        }
        
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
        df_30m = fetch_kline_data(stock_code, 30, 100)
        if df_30m is not None:
            # 港股数据可能已经是正确时区，A股需要转换
            if not is_hk:
                df_30m = normalize_beijing_time(df_30m)
                df_30m = filter_trading_hours(df_30m)
            df_30m = calculate_technical_indicators(df_30m)
            stock_data_map['30m'] = df_30m
        
        print("  获取5分钟数据...")
        df_5m = fetch_kline_data(stock_code, 5, 100)
        if df_5m is not None:
            # 港股数据可能已经是正确时区，A股需要转换
            if not is_hk:
                df_5m = normalize_beijing_time(df_5m)
                df_5m = filter_trading_hours(df_5m)
            df_5m = calculate_technical_indicators(df_5m)
            stock_data_map['5m'] = df_5m
        
        print("  获取1分钟数据...")
        df_1m = fetch_kline_data(stock_code, 1, 100)
        one_min_source = data_source
        
        if df_1m is not None and not df_1m.empty:
            # 港股数据可能已经是正确时区，A股需要转换
            if not is_hk:
                df_1m = normalize_beijing_time(df_1m)
                df_1m = filter_trading_hours(df_1m)
            df_1m = calculate_technical_indicators(df_1m)
            stock_data_map['1m'] = df_1m
            print(f"    ✓ 1分钟: {len(df_1m)} 条数据")
        else:
            print("    ❌ 无法获取真实1分钟数据，跳过1分钟图表")
            one_min_source = '无数据'
        
        print(f"\n3️⃣  生成图表...")
        
        index_charts_count = create_indices_charts(indices_data, temp_dir)
        print(f"   生成 {index_charts_count} 个指数图表")
        
        chart_configs = [
            ('day', stock_data_map.get('day'), f"{stock_name} 日线", 60),
            ('week', stock_data_map.get('week'), f"{stock_name} 周线", 60),
            ('month', stock_data_map.get('month'), f"{stock_name} 月线", 60),
            ('30m', stock_data_map.get('30m'), f"{stock_name} 30分钟", 100),
            ('5m', stock_data_map.get('5m'), f"{stock_name} 5分钟", 100),
            ('1m', stock_data_map.get('1m'), f"{stock_name} 1分钟", 100),
        ]
        
        stock_charts_count = 0
        for key, df, title, max_points in chart_configs:
            if df is not None and len(df) >= 5:
                img_path = os.path.join(temp_dir, f"{key}.png")
                if create_candle_chart(df, title, img_path, max_points=max_points):
                    stock_charts_count += 1
        
        print(f"✅ 图表生成完成: 个股{stock_charts_count}个, 指数{index_charts_count}个")
        print(f"📊 图表包含: K线、MACD、KDJ、成交量、量比")
        
        print(f"\n4️⃣  生成PDF报告...")
        
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', stock_name)
        pdf_filename = f"{safe_name}_{stock_code}_增强分析报告.pdf"
        pdf_path = os.path.join(output_folder, pdf_filename)
        
        report_meta['one_min_source'] = one_min_source
        stock_data_map['_meta'] = report_meta
        
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

# ==================== 主程序 ====================

def main():
    """主程序"""
# 1. 检查是否为手动模式
    is_manual = '--mode' in sys.argv and 'manual' in sys.argv
    
    # 2. 如果不是手动点，而是 GitHub Actions 自动跑，则检查交易日状态
    if not is_manual:
        has_hk = any(is_hk_stock(code) for code in TARGET_STOCKS)
        has_a = any(not is_hk_stock(code) for code in TARGET_STOCKS)
        
        a_open = True
        hk_open = True
        
        if has_a:
            print("🕒 正在检查 A 股交易日...")
            a_open = is_china_stock_market_open()
        if has_hk:
            print("🕒 正在检查港股交易日...")
            hk_open = is_hk_stock_market_open()
        
        if not a_open and not hk_open:
            print("☕ 今日为法定节假日或休市，跳过分析报告推送。")
            return
        
        # 过滤休市市场的股票
        filtered = []
        skipped = []
        for code in TARGET_STOCKS:
            if is_hk_stock(code):
                if hk_open:
                    filtered.append(code)
                else:
                    skipped.append(code)
            else:
                if a_open:
                    filtered.append(code)
                else:
                    skipped.append(code)
        
        if skipped:
            print(f"☕ 跳过休市市场股票: {', '.join(skipped)}")
        TARGET_STOCKS[:] = filtered
    
    # 3. 只有开盘或是手动触发，才会继续执行下面的逻辑...
    print("🚀 市场已开盘或手动触发，开始分析任务...")
    print("=" * 70)
    print("📊 股票分析报告生成器 (增强版)")
    print("数据来源: 新浪财经")
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
    sector_input = globals().get('SECTOR_INPUT', None)
    successful_reports, failed_reports = process_multiple_stocks(stocks_input, output_dir, sector_input=sector_input)
    
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
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--mode', choices=['manual', 'telegram'], default='manual')
        parser.add_argument('--stocks', type=str, default=' '.join(TARGET_STOCKS))
        parser.add_argument('--sector', type=str, default=None, help='行业代码（如BK1031）或行业名称（如光伏设备）')
        args = parser.parse_args()
        
        if args.mode == 'telegram':
            print("⚠️ Telegram模式需要配置环境变量")
        else:
            if args.stocks != ' '.join(TARGET_STOCKS):
                TARGET_STOCKS = parse_stock_list(args.stocks)
            # 将sector参数存储为全局变量，供process_multiple_stocks使用
            global SECTOR_INPUT
            SECTOR_INPUT = args.sector
            main()
    else:
        main()
