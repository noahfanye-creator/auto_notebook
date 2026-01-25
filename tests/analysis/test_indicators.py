"""
测试技术指标计算函数
"""
import pytest
import pandas as pd
import numpy as np
from src.analysis.indicators import (
    calculate_technical_indicators,
    resample_kline_data,
    calculate_ma,
    calculate_rsi,
    calculate_macd,
    calculate_kdj
)


class TestTechnicalIndicators:
    """技术指标计算测试类"""
    
    @pytest.fixture
    def sample_data(self):
        """创建测试用的K线数据"""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 2)
        
        return pd.DataFrame({
            'Open': prices + np.random.randn(100) * 0.5,
            'High': prices + np.abs(np.random.randn(100) * 1),
            'Low': prices - np.abs(np.random.randn(100) * 1),
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
    
    def test_calculate_technical_indicators(self, sample_data):
        """测试综合技术指标计算"""
        df = calculate_technical_indicators(sample_data)
        
        # 检查移动平均线
        assert 'MA5' in df.columns
        assert 'MA10' in df.columns
        assert 'MA20' in df.columns
        assert 'MA60' in df.columns
        
        # 检查MACD
        assert 'MACD' in df.columns
        assert 'DIF' in df.columns
        assert 'DEA' in df.columns
        
        # 检查RSI
        assert 'RSI' in df.columns
        assert df['RSI'].notna().any()  # 至少有一些非空值
        
        # 检查数据完整性
        assert len(df) == len(sample_data)
        assert not df.empty
    
    def test_calculate_technical_indicators_empty(self):
        """测试空数据"""
        empty_df = pd.DataFrame()
        result = calculate_technical_indicators(empty_df)
        assert result.empty
    
    def test_calculate_technical_indicators_none(self):
        """测试None输入"""
        result = calculate_technical_indicators(None)
        assert result is None
    
    def test_calculate_ma(self, sample_data):
        """测试移动平均线计算"""
        df = calculate_ma(sample_data, windows=[5, 10, 20])
        
        assert 'MA5' in df.columns
        assert 'MA10' in df.columns
        assert 'MA20' in df.columns
        
        # 检查MA5的值
        assert df['MA5'].iloc[-1] is not None
    
    def test_calculate_rsi(self, sample_data):
        """测试RSI计算"""
        df = calculate_rsi(sample_data, period=14)
        
        assert 'RSI' in df.columns
        # RSI应该在0-100之间
        valid_rsi = df['RSI'].dropna()
        if len(valid_rsi) > 0:
            assert (valid_rsi >= 0).all()
            assert (valid_rsi <= 100).all()
    
    def test_calculate_macd(self, sample_data):
        """测试MACD计算"""
        df = calculate_macd(sample_data)
        
        assert 'MACD' in df.columns
        assert 'DIF' in df.columns
        assert 'DEA' in df.columns
    
    def test_calculate_kdj(self, sample_data):
        """测试KDJ计算"""
        df = calculate_kdj(sample_data, period=9)
        
        assert 'K' in df.columns
        assert 'D' in df.columns
        assert 'J' in df.columns
    
    def test_resample_kline_data(self, sample_data):
        """测试K线数据重采样"""
        # 周线
        weekly = resample_kline_data(sample_data, 'W')
        assert weekly is not None
        assert not weekly.empty
        assert len(weekly) < len(sample_data)  # 周线数据应该更少
        
        # 月线
        monthly = resample_kline_data(sample_data, 'M')
        assert monthly is not None
        assert not monthly.empty
        assert len(monthly) < len(weekly)  # 月线数据应该更少
    
    def test_resample_kline_data_empty(self):
        """测试空数据重采样"""
        empty_df = pd.DataFrame()
        result = resample_kline_data(empty_df, 'W')
        assert result is None or result.empty
