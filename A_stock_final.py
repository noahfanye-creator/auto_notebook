# chanlun_pdf_pro_fixed_with_indices.py
import requests
import pandas as pd
import os
import re
import sys
import traceback
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# ==================== 1. macOS 字体配置修复版 ====================
def setup_macos_fonts_fixed():
    """修复macOS字体设置"""
    print("📱 macOS系统字体配置...")
    
    font_name = 'Helvetica'
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
                break
            except Exception as e:
                print(f"⚠️  字体注册失败 {font_alias}: {e}")
    
    if font_name == 'Helvetica':
        try:
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            font_name = 'STSong-Light'
            print("✅ 使用STSong-Light CID字体")
        except:
            print("⚠️  所有中文字体尝试失败，使用默认Helvetica")
    
    return font_name

FONT_NAME = setup_macos_fonts_fixed()

# ==================== 2. 数据抓取模块 ====================

def normalize_code(code):
    """标准化股票代码"""
    code = code.strip().lower().replace(' ', '')
    
    if re.match(r'^\d{5,6}$', code):
        if code.startswith('6'): 
            return f"sh{code}"
        if code.startswith('0') or code.startswith('3'): 
            return f"sz{code}"
        if code.startswith('4') or code.startswith('8'): 
            return f"bj{code}"
    
    return code

def get_stock_real_time_data(symbol):
    """获取股票实时数据，包括现价和涨跌幅"""
    try:
        url = f"http://hq.sinajs.cn/list={symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if "=\"" in resp.text:
            data = resp.text.split('="')[1].split(',')
            if len(data) >= 32:
                name = data[0]
                open_price = float(data[1])  # 开盘价
                prev_close = float(data[2])  # 昨日收盘价
                current_price = float(data[3])  # 当前价格/收盘价
                high_price = float(data[4])  # 最高价
                low_price = float(data[5])  # 最低价
                volume = float(data[8])  # 成交量（股）
                turnover = float(data[9])  # 成交额（元）
                
                # 计算涨跌幅
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
                
                # 计算振幅
                amplitude = ((high_price - low_price) / prev_close) * 100
                
                # 计算换手率（简化计算，实际需要流通股本数据）
                # 对于A股，我们使用一个近似的流通股本估计
                if symbol.startswith('sh6') or symbol.startswith('sz0'):
                    # 主板股票，假设流通股本为10亿
                    turnover_rate = (volume / 1000000000) * 100
                elif symbol.startswith('sz3'):
                    # 创业板，假设流通股本为5亿
                    turnover_rate = (volume / 500000000) * 100
                elif symbol.startswith('bj'):
                    # 北交所，假设流通股本为1亿
                    turnover_rate = (volume / 100000000) * 100
                else:
                    turnover_rate = (volume / 500000000) * 100
                
                # 格式化数据
                volume_str = f"{volume/10000:.2f}万"  # 转为万手
                turnover_str = f"{turnover/100000000:.2f}亿"  # 转为亿元
                
                return {
                    'name': name,
                    'open_price': open_price,
                    'prev_close': prev_close,
                    'current_price': current_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'volume': volume_str,
                    'turnover': turnover_str,
                    'change': change,
                    'change_percent': change_percent,
                    'amplitude': amplitude,
                    'turnover_rate': turnover_rate,
                    'after_hours_volume': "0",  # 盘后量，新浪接口不提供
                    'after_hours_turnover': "0"  # 盘后额，新浪接口不提供
                }
            elif len(data) >= 3:
                # 如果数据不够完整，至少返回基本价格信息
                name = data[0]
                current_price = float(data[3])
                prev_close = float(data[2])
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
                
                return {
                    'name': name,
                    'current_price': current_price,
                    'prev_close': prev_close,
                    'change': change,
                    'change_percent': change_percent
                }
    except Exception as e:
        print(f"获取实时数据出错: {e}")
    
    return None

def get_name(symbol):
    """获取股票名称"""
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

def calculate_technical_indicators(df):
    """计算技术指标"""
    if df is None or df.empty:
        return df
    
    # 移动平均线
    df['MA5'] = df['Close'].rolling(window=5, min_periods=1).mean()
    df['MA10'] = df['Close'].rolling(window=10, min_periods=1).mean()
    df['MA20'] = df['Close'].rolling(window=20, min_periods=1).mean()
    df['MA60'] = df['Close'].rolling(window=60, min_periods=1).mean()
    df['MA250'] = df['Close'].rolling(window=250, min_periods=1).mean()
    
    # MACD
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = exp12 - exp26
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD'] = 2 * (df['DIF'] - df['DEA'])
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 布林带
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
    df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
    
    # 成交量均线
    df['Volume_MA5'] = df['Volume'].rolling(window=5, min_periods=1).mean()
    df['Volume_MA10'] = df['Volume'].rolling(window=10, min_periods=1).mean()
    
    # KDJ
    n = 9
    low_list = df['Low'].rolling(window=n, min_periods=1).min()
    high_list = df['High'].rolling(window=n, min_periods=1).max()
    rsv = (df['Close'] - low_list) / (high_list - low_list) * 100
    df['K'] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/3, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
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

def get_market_indices_data():
    """获取市场指数数据"""
    indices_data = {}
    
    # A股主要指数
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
                'data': df
            }
                
    return indices_data

def get_market_summary_analysis(indices_data):
    """生成市场综合分析"""
    if not indices_data:
        return ""
    
    analysis = "【A股市场综合分析】\n\n"
    
    for code, info in indices_data.items():
        df = info['data']
        name = info['name']
        
        if df is not None and not df.empty:
            last = df.iloc[-1]
            
            # 趋势判断
            trend = "横盘"
            if last['MA5'] > last['MA10'] > last['MA20']:
                trend = "多头排列"
            elif last['MA5'] < last['MA10'] < last['MA20']:
                trend = "空头排列"
            
            # RSI状态
            rsi_status = "中性"
            if last['RSI'] > 70:
                rsi_status = "超买"
            elif last['RSI'] < 30:
                rsi_status = "超卖"
            
            analysis += f"{name}:\n"
            analysis += f"  现价: {last['Close']:.2f}, MA5: {last['MA5']:.2f}, MA10: {last['MA10']:.2f}\n"
            analysis += f"  趋势: {trend}, RSI: {last['RSI']:.1f}({rsi_status})\n"
            analysis += f"  MACD: {last['MACD']:.3f}\n\n"
    
    return analysis

# ==================== 3. 图表生成模块 ====================
def create_candle_chart(df, title, filename):
    """创建K线图表 - 生成包含多个技术指标的组合图表"""
    if df is None or len(df) < 5:
        return False
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import matplotlib.font_manager as fm
        import numpy as np
        
        # ============ 修复：添加中文字体配置 ============
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
        ]
        
        font_added = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_prop = fm.FontProperties(fname=font_path)
                    fm.fontManager.addfont(font_path)
                    font_name = font_prop.get_name()
                    plt.rcParams['font.sans-serif'] = [font_name, 'Arial', 'DejaVu Sans']
                    plt.rcParams['axes.unicode_minus'] = False
                    font_added = True
                    print(f"   使用字体: {font_name}")
                    break
                except:
                    continue
        
        if not font_added:
            plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            print("   使用默认字体")
        
        # 获取数据并计算指标
        plot_data = df.tail(min(120, len(df))).copy()
        
        # 确保有足够的数据计算指标
        if len(plot_data) < 20:
            plot_data = df.tail(60).copy()
        
        # 计算技术指标
        plot_data = calculate_technical_indicators(plot_data)
        
        # 创建4个子图：价格+成交量+MACD+KDJ
        fig = plt.figure(figsize=(14, 10))
        
        # 1. 价格图表（占40%高度）
        ax1 = plt.subplot(4, 1, 1)
        ax1.set_title(title, fontsize=14, fontweight='bold', pad=10)
        
        # 绘制价格线
        dates = plot_data.index
        closes = plot_data['Close'].values
        
        # 绘制收盘价线
        ax1.plot(dates, closes, 'black', linewidth=1.5, label='收盘价', alpha=0.8)
        
        # 绘制均线
        ax1.plot(dates, plot_data['MA5'], 'orange', linewidth=1, label='MA5', alpha=0.8)
        ax1.plot(dates, plot_data['MA10'], 'blue', linewidth=1, label='MA10', alpha=0.8)
        ax1.plot(dates, plot_data['MA20'], 'purple', linewidth=1, label='MA20', alpha=0.8)
        
        # 填充布林带
        ax1.fill_between(dates, plot_data['BB_Upper'], plot_data['BB_Lower'], 
                        color='gray', alpha=0.1, label='布林带')
        ax1.plot(dates, plot_data['BB_Middle'], 'gray', linewidth=0.5, alpha=0.5)
        
        ax1.set_ylabel('价格', fontsize=10)
        ax1.legend(loc='upper left', fontsize=8, ncol=6)
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        # 2. 成交量图表（占20%高度）
        ax2 = plt.subplot(4, 1, 2, sharex=ax1)
        
        # 绘制成交量柱状图
        volumes = plot_data['Volume'].values
        volume_colors = ['green' if closes[i] >= closes[i-1] else 'red' 
                        if i > 0 else 'green' for i in range(len(dates))]
        
        ax2.bar(dates, volumes, color=volume_colors, alpha=0.7, width=0.6)
        
        # 绘制成交量均线
        ax2.plot(dates, plot_data['Volume_MA5'], 'orange', linewidth=1, label='成交量MA5')
        ax2.plot(dates, plot_data['Volume_MA10'], 'blue', linewidth=1, label='成交量MA10')
        
        ax2.set_ylabel('成交量', fontsize=10)
        ax2.legend(loc='upper left', fontsize=8)
        ax2.grid(True, alpha=0.3, linestyle='--')
        
        # 3. MACD图表（占20%高度）
        ax3 = plt.subplot(4, 1, 3, sharex=ax1)
        
        # 绘制MACD柱状图
        macd_values = plot_data['MACD'].values
        macd_colors = ['red' if v >= 0 else 'green' for v in macd_values]
        ax3.bar(dates, macd_values, color=macd_colors, alpha=0.7, width=0.6)
        
        # 绘制DIF和DEA线
        ax3.plot(dates, plot_data['DIF'], 'black', linewidth=1, label='DIF')
        ax3.plot(dates, plot_data['DEA'], 'orange', linewidth=1, label='DEA')
        
        # 零线
        ax3.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
        
        ax3.set_ylabel('MACD', fontsize=10)
        ax3.legend(loc='upper left', fontsize=8)
        ax3.grid(True, alpha=0.3, linestyle='--')
        
        # 4. KDJ图表（占20%高度）
        ax4 = plt.subplot(4, 1, 4, sharex=ax1)
        
        # 绘制KDJ线
        ax4.plot(dates, plot_data['K'], 'blue', linewidth=1, label='K')
        ax4.plot(dates, plot_data['D'], 'orange', linewidth=1, label='D')
        ax4.plot(dates, plot_data['J'], 'purple', linewidth=1, label='J')
        
        # 添加超买超卖线
        ax4.axhline(y=80, color='red', linestyle='--', linewidth=0.5, alpha=0.5)
        ax4.axhline(y=20, color='green', linestyle='--', linewidth=0.5, alpha=0.5)
        
        ax4.set_ylabel('KDJ', fontsize=10)
        ax4.legend(loc='upper left', fontsize=8)
        ax4.grid(True, alpha=0.3, linestyle='--')
        
        # 设置X轴格式
        for ax in [ax1, ax2, ax3, ax4]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, fontsize=8)
        
        # 隐藏ax1-ax3的X轴标签
        plt.setp(ax1.get_xticklabels(), visible=False)
        plt.setp(ax2.get_xticklabels(), visible=False)
        plt.setp(ax3.get_xticklabels(), visible=False)
        
        # 设置X轴标签
        ax4.set_xlabel('时间', fontsize=10)
        
        # 调整布局
        plt.subplots_adjust(hspace=0.1)  # 减少子图间距
        
        # 保存图表
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
        import traceback
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
            
            if create_candle_chart(df, title, img_path):
                charts_created += 1
    
    return charts_created

# ==================== 4. PDF报告生成 ====================

def create_pdf_with_market_analysis(stock_code, stock_name, stock_data_map, indices_data, real_time_data, save_path, temp_dir):
    """创建包含市场指数分析的PDF报告"""
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
        
        # 创建样式
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
            spaceAfter=10,
            textColor=colors.red
        )
        
        change_style = ParagraphStyle(
            name='ChangeStyle',
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
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"{stock_name}技术分析报告", title_style))
        story.append(Paragraph(f"({stock_code})", subtitle_style))
        story.append(Spacer(1, 15))
        
        # 显示实时价格和涨跌幅
        if real_time_data:
            current_price = real_time_data.get('current_price', 0)
            change_percent = real_time_data.get('change_percent', 0)
            change = real_time_data.get('change', 0)
            
            # 价格显示
            story.append(Paragraph(f"当前价格: {current_price:.2f}", price_style))
            
            # 涨跌幅显示，根据涨跌显示不同颜色
            if change >= 0:
                change_style.textColor = colors.red
                change_text = f"涨跌幅: +{change:.2f} (+{change_percent:.2f}%)"
            else:
                change_style.textColor = colors.green
                change_text = f"涨跌幅: {change:.2f} ({change_percent:.2f}%)"
            
            story.append(Paragraph(change_text, change_style))
            story.append(Spacer(1, 10))
            
            # ============ 新增：股票基本信息表格 ============
            # 创建基本信息表格
            basic_info_data = []
            
            # 第一行：表头
            basic_info_data.append(['指标', '数值', '指标', '数值'])
            
            # 第二行：开盘和涨幅
            open_price = real_time_data.get('open_price', 0)
            basic_info_data.append(['开盘', f"{open_price:.2f}", 
                                   '涨幅', f"{change_percent:.2f}%"])
            
            # 第三行：收盘和振幅
            amplitude = real_time_data.get('amplitude', 0)
            basic_info_data.append(['收盘', f"{current_price:.2f}", 
                                   '振幅', f"{amplitude:.2f}%"])
            
            # 第四行：最高和成交量
            high_price = real_time_data.get('high_price', 0)
            volume = real_time_data.get('volume', '0')
            basic_info_data.append(['最高', f"{high_price:.2f}", 
                                   '成交量', volume])
            
            # 第五行：最低和成交额
            low_price = real_time_data.get('low_price', 0)
            turnover = real_time_data.get('turnover', '0')
            basic_info_data.append(['最低', f"{low_price:.2f}", 
                                   '成交额', turnover])
            
            # 第六行：昨收和换手率
            prev_close = real_time_data.get('prev_close', 0)
            turnover_rate = real_time_data.get('turnover_rate', 0)
            basic_info_data.append(['昨收', f"{prev_close:.2f}", 
                                   '换手率', f"{turnover_rate:.2f}%"])
            
            # 第七行：盘后量
            after_hours_volume = real_time_data.get('after_hours_volume', '0')
            basic_info_data.append(['', '', '盘后量', after_hours_volume])
            
            # 第八行：盘后额
            after_hours_turnover = real_time_data.get('after_hours_turnover', '0')
            basic_info_data.append(['', '', '盘后额', after_hours_turnover])
            
            # 创建表格样式
            basic_info_table = Table(basic_info_data, colWidths=[60, 80, 60, 80])
            basic_info_table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (3,0), colors.lightgrey),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('SPAN', (0,6), (1,6)),  # 合并空单元格
                ('SPAN', (0,7), (1,7)),  # 合并空单元格
            ]))
            
            story.append(Spacer(1, 10))
            story.append(Paragraph("股票基本信息", normal_style))
            story.append(basic_info_table)
        else:
            story.append(Paragraph("价格数据获取中...", normal_style))
        
        story.append(Spacer(1, 15))
        story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
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
        
        # 创建指数图表表格
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
            # 每行显示2个指数
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
        
        # 第二部分：个股详细技术分析
        story.append(Paragraph("二、个股技术分析", section_style))
        
        # 个股各级别分析
        periods = [
            ('日线级别分析', 'day'),
            ('周线级别分析', 'week'),
            ('月线级别分析', 'month'),
            ('30分钟级别分析', '30m'),
            ('5分钟级别分析', '5m')
        ]
        
        for cn_name, key in periods:
            df = stock_data_map.get(key)
            
            story.append(Paragraph(cn_name, subtitle_style))
            story.append(Spacer(1, 10))
            
            if df is not None and not df.empty and len(df) >= 3:
                try:
                    last = df.iloc[-1]
                    
                    # 技术指标表格
                    indicator_data = [
                        ['指标', '数值', '状态'],
                        ['收盘价', f"{last['Close']:.2f}", 
                         '📈' if last['Close'] > last['MA5'] else '📉'],
                        ['MA5', f"{last['MA5']:.2f}", 
                         '金叉' if last['MA5'] > last['MA10'] else '死叉'],
                        ['MA10', f"{last['MA10']:.2f}", ''],
                        ['MA20', f"{last['MA20']:.2f}", ''],
                        ['RSI', f"{last['RSI']:.1f}", 
                         '超买' if last['RSI'] > 70 else ('超卖' if last['RSI'] < 30 else '正常')],
                        ['MACD', f"{last['MACD']:.3f}", 
                         '看涨' if last['MACD'] > 0 else '看跌']
                    ]
                    
                    table = Table(indicator_data, colWidths=[60, 80, 60])
                    table.setStyle(TableStyle([
                        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
                        ('FONTSIZE', (0,0), (-1,-1), 9),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ]))
                    story.append(table)
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
                        ratio = min(500/img_width, 300/img_height)
                        
                        img = Image(img_path, width=img_width*ratio, height=img_height*ratio)
                        img.hAlign = 'CENTER'
                        story.append(img)
                    except:
                        story.append(Paragraph("[图表加载失败]", normal_style))
                
                story.append(Spacer(1, 20))
                
                if key != '5m':
                    story.append(PageBreak())
        
        # 免责声明
        story.append(Spacer(1, 20))
        story.append(Paragraph("免责声明：本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。", 
                              ParagraphStyle(name='Disclaimer', parent=normal_style, fontSize=8, textColor=colors.grey)))
        
        doc.build(story)
        print(f"    PDF生成成功: {os.path.basename(save_path)}")
        return True
        
    except Exception as e:
        print(f"    PDF生成失败: {e}")
        traceback.print_exc()
        return False

# ==================== 5. 新增：批量处理函数 ====================

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
        
        # 标准化代码
        stock_code = normalize_code(code_input)
        print(f"📈 分析股票: {stock_code}")
        
        # 获取股票名称和实时数据
        real_time_data = get_stock_real_time_data(stock_code)
        if real_time_data:
            stock_name = real_time_data['name']
            print(f"📛 股票名称: {stock_name}")
            print(f"💰 当前价格: {real_time_data.get('current_price', 0):.2f}")
            print(f"📊 涨跌幅: {real_time_data.get('change_percent', 0):.2f}%")
            
            # 显示更多信息
            if 'open_price' in real_time_data:
                print(f"📈 开盘价: {real_time_data['open_price']:.2f}")
                print(f"📉 最高价: {real_time_data.get('high_price', 0):.2f}")
                print(f"📉 最低价: {real_time_data.get('low_price', 0):.2f}")
                print(f"📊 成交量: {real_time_data.get('volume', '0')}")
                print(f"💰 成交额: {real_time_data.get('turnover', '0')}")
        else:
            stock_name = get_name(stock_code)
            print(f"📛 股票名称: {stock_name}")
            print("⚠️  无法获取实时价格数据")
        
        # 创建临时目录
        timestamp = datetime.now().strftime('%H%M%S')
        temp_dir = os.path.join(output_folder, f"temp_{stock_code}_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        print(f"📁 临时目录: {temp_dir}")
        
        print("\n1️⃣  获取市场指数数据...")
        indices_data = get_market_indices_data()
        print(f"✅ 获取到 {len(indices_data)} 个市场指数数据")
        
        print("\n2️⃣  获取个股数据...")
        stock_data_map = {}
        
        # 获取日线数据
        print("  获取日线数据...")
        df_day = fetch_kline_data(stock_code, 240, 100)
        if df_day is not None:
            df_day = calculate_technical_indicators(df_day)
            stock_data_map['day'] = df_day
            print(f"    ✓ 日线: {len(df_day)} 条数据")
        else:
            print(f"❌ 无法获取日线数据，跳过此股票")
            failed_reports.append((stock_code, stock_name, "无法获取日线数据"))
            # 清理临时目录
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
            continue
        
        # 重采样
        if df_day is not None:
            print("  生成周线数据...")
            df_week = resample_kline_data(df_day, 'W')
            stock_data_map['week'] = df_week
            
            print("  生成月线数据...")
            df_month = resample_kline_data(df_day, 'M')
            stock_data_map['month'] = df_month
        
        # 分钟线数据
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
        
        print(f"\n3️⃣  生成图表...")
        
        # 生成指数图表
        index_charts_count = create_indices_charts(indices_data, temp_dir)
        print(f"   生成 {index_charts_count} 个指数图表")
        
        # 生成个股图表
        chart_configs = [
            ('day', stock_data_map.get('day'), f"{stock_name} 日线"),
            ('week', stock_data_map.get('week'), f"{stock_name} 周线"),
            ('month', stock_data_map.get('month'), f"{stock_name} 月线"),
            ('30m', stock_data_map.get('30m'), f"{stock_name} 30分钟"),
            ('5m', stock_data_map.get('5m'), f"{stock_name} 5分钟"),
        ]
        
        stock_charts_count = 0
        for key, df, title in chart_configs:
            if df is not None and len(df) >= 5:
                img_path = os.path.join(temp_dir, f"{key}.png")
                if create_candle_chart(df, title, img_path):
                    stock_charts_count += 1
        
        print(f"✅ 图表生成完成: 个股{stock_charts_count}个, 指数{index_charts_count}个")
        
        print(f"\n4️⃣  生成PDF报告...")
        
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', stock_name)
        pdf_filename = f"{safe_name}_{stock_code}_市场分析报告.pdf"
        pdf_path = os.path.join(output_folder, pdf_filename)
        
        success = create_pdf_with_market_analysis(
            stock_code, stock_name, stock_data_map, indices_data, real_time_data, pdf_path, temp_dir
        )
        
        if success and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / 1024
            print(f"\n🎉 报告生成完成！")
            print(f"📄 文件: {pdf_path}")
            print(f"📏 大小: {file_size:.1f} KB")
            print(f"📊 包含: {len(indices_data)} 个市场指数分析")
            successful_reports.append((stock_code, stock_name, pdf_path))
        else:
            print("❌ PDF生成失败")
            failed_reports.append((stock_code, stock_name, "PDF生成失败"))
        
        # 清理临时目录
        try:
            import shutil
            shutil.rmtree(temp_dir)
            print(f"🧹 已清理临时目录: {temp_dir}")
        except:
            pass
    
    return successful_reports, failed_reports

# ==================== 主程序 ====================

def main():
    """主程序"""
    print("=" * 70)
    print("📊 A股股票分析报告生成器 (含市场指数分析)")
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
    
    while True:
        print("\n" + "-" * 70)
        print("📋 输入说明:")
        print("  1. 输入单个股票代码 (如: 600036)")
        print("  2. 输入多个股票代码，用空格分隔 (如: 600036 000001 300750)")
        print("  3. 输入 'q' 退出程序")
        print("-" * 70)
        
        user_input = input("请输入股票代码: ").strip()
        
        if user_input.lower() == 'q':
            print("👋 程序退出")
            break
        
        if not user_input:
            print("⚠️  请输入股票代码")
            continue
        
        # 判断输入是单个还是多个股票代码
        if ' ' in user_input:
            # 多个股票代码，使用批量处理模式
            stock_codes = user_input.split()
            print(f"📊 检测到 {len(stock_codes)} 个股票代码，进入批量处理模式")
            
            # 创建总文件夹
            desktop = os.path.expanduser("~/Desktop")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            batch_folder_name = f"{timestamp}_股票分析报告"
            output_folder = os.path.join(desktop, batch_folder_name)
            
            try:
                os.makedirs(output_folder, exist_ok=True)
                print(f"📁 创建批量输出文件夹: {output_folder}")
            except Exception as e:
                print(f"❌ 无法创建输出文件夹: {e}")
                continue
            
            # 批量处理
            successful_reports, failed_reports = process_multiple_stocks(user_input, output_folder)
            
            # 输出批量处理结果
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
            
            if successful_reports:
                print(f"\n📁 所有报告已保存到: {output_folder}")
                open_folder = input("\n是否打开输出文件夹？(y/n): ").lower()
                if open_folder == 'y':
                    try:
                        import subprocess
                        subprocess.run(['open', output_folder])
                    except:
                        try:
                            import webbrowser
                            webbrowser.open(f"file://{output_folder}")
                        except:
                            print("⚠️  无法自动打开文件夹，请手动打开")
        
        else:
            # 单个股票代码
            code_input = user_input
            # 标准化代码
            stock_code = normalize_code(code_input)
            print(f"📈 分析股票: {stock_code}")
            
            # 获取股票名称和实时数据
            real_time_data = get_stock_real_time_data(stock_code)
            if real_time_data:
                stock_name = real_time_data['name']
                print(f"📛 股票名称: {stock_name}")
                print(f"💰 当前价格: {real_time_data.get('current_price', 0):.2f}")
                print(f"📊 涨跌幅: {real_time_data.get('change_percent', 0):.2f}%")
                
                # 显示更多信息
                if 'open_price' in real_time_data:
                    print(f"📈 开盘价: {real_time_data['open_price']:.2f}")
                    print(f"📉 最高价: {real_time_data.get('high_price', 0):.2f}")
                    print(f"📉 最低价: {real_time_data.get('low_price', 0):.2f}")
                    print(f"📊 成交量: {real_time_data.get('volume', '0')}")
                    print(f"💰 成交额: {real_time_data.get('turnover', '0')}")
            else:
                stock_name = get_name(stock_code)
                print(f"📛 股票名称: {stock_name}")
                print("⚠️  无法获取实时价格数据")
            
            # 创建临时目录
            desktop = os.path.expanduser("~/Desktop")
            timestamp = datetime.now().strftime('%H%M%S')
            temp_dir = os.path.join(desktop, f"temp_{stock_code}_{timestamp}")
            os.makedirs(temp_dir, exist_ok=True)
            print(f"📁 临时目录: {temp_dir}")
            
            print("\n1️⃣  获取市场指数数据...")
            indices_data = get_market_indices_data()
            print(f"✅ 获取到 {len(indices_data)} 个市场指数数据")
            
            print("\n2️⃣  获取个股数据...")
            stock_data_map = {}
            
            # 获取日线数据
            print("  获取日线数据...")
            df_day = fetch_kline_data(stock_code, 240, 100)
            if df_day is not None:
                df_day = calculate_technical_indicators(df_day)
                stock_data_map['day'] = df_day
                print(f"    ✓ 日线: {len(df_day)} 条数据")
            
            # 重采样
            if df_day is not None:
                print("  生成周线数据...")
                df_week = resample_kline_data(df_day, 'W')
                stock_data_map['week'] = df_week
                
                print("  生成月线数据...")
                df_month = resample_kline_data(df_day, 'M')
                stock_data_map['month'] = df_month
            
            # 分钟线数据
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
            
            print(f"\n3️⃣  生成图表...")
            
            # 生成指数图表
            index_charts_count = create_indices_charts(indices_data, temp_dir)
            print(f"   生成 {index_charts_count} 个指数图表")
            
            # 生成个股图表
            chart_configs = [
                ('day', stock_data_map.get('day'), f"{stock_name} 日线"),
                ('week', stock_data_map.get('week'), f"{stock_name} 周线"),
                ('month', stock_data_map.get('month'), f"{stock_name} 月线"),
                ('30m', stock_data_map.get('30m'), f"{stock_name} 30分钟"),
                ('5m', stock_data_map.get('5m'), f"{stock_name} 5分钟"),
            ]
            
            stock_charts_count = 0
            for key, df, title in chart_configs:
                if df is not None and len(df) >= 5:
                    img_path = os.path.join(temp_dir, f"{key}.png")
                    if create_candle_chart(df, title, img_path):
                        stock_charts_count += 1
            
            print(f"✅ 图表生成完成: 个股{stock_charts_count}个, 指数{index_charts_count}个")
            
            print(f"\n4️⃣  生成PDF报告...")
            
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', stock_name)
            pdf_filename = f"{safe_name}_{stock_code}_市场分析报告_{timestamp}.pdf"
            pdf_path = os.path.join(desktop, pdf_filename)
            
            success = create_pdf_with_market_analysis(
                stock_code, stock_name, stock_data_map, indices_data, real_time_data, pdf_path, temp_dir
            )
            
            if success and os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path) / 1024
                print(f"\n🎉 报告生成完成！")
                print(f"📄 文件: {pdf_path}")
                print(f"📏 大小: {file_size:.1f} KB")
                print(f"📊 包含: {len(indices_data)} 个市场指数分析")
                
                open_file = input("\n是否打开PDF文件？(y/n): ").lower()
                if open_file == 'y':
                    try:
                        import subprocess
                        subprocess.run(['open', pdf_path])
                    except:
                        print("⚠️  无法自动打开，请手动打开")
            else:
                print("❌ PDF生成失败")
            
            # 清理临时文件
            try:
                import shutil
                shutil.rmtree(temp_dir)
                print(f"🧹 已清理临时目录: {temp_dir}")
            except:
                pass
        
        print("\n" + "=" * 70)
        
        again = input("是否分析其他股票？(y/n): ").lower()
        if again != 'y':
            print("👋 再见！")
            break

if __name__ == "__main__":
    main()