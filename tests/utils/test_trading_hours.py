"""
测试交易时间判断函数
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd
from src.utils.trading_hours import is_china_stock_market_open, is_hk_stock_market_open


class TestTradingHours:
    """交易时间判断测试类"""
    
    @patch('src.utils.trading_hours.ak')
    @patch('src.utils.trading_hours.datetime')
    def test_china_market_open_weekday(self, mock_datetime, mock_ak):
        """测试A股市场工作日开盘"""
        # 模拟akshare返回数据（最后交易日是今天）
        mock_df = pd.DataFrame({
            'date': [datetime(2024, 1, 15).date()]
        })
        mock_ak.stock_zh_index_daily.return_value = mock_df
        
        # 模拟当前日期
        mock_datetime.now.return_value = datetime(2024, 1, 15, 10, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = is_china_stock_market_open()
        assert result == True
    
    @patch('src.utils.trading_hours.ak')
    @patch('src.utils.trading_hours.datetime')
    def test_china_market_closed_weekend(self, mock_datetime, mock_ak):
        """测试A股市场周末休市"""
        # 模拟akshare返回数据（最后交易日是周五）
        mock_df = pd.DataFrame({
            'date': [datetime(2024, 1, 12).date()]  # 周五
        })
        mock_ak.stock_zh_index_daily.return_value = mock_df
        
        # 模拟当前日期（周六）
        mock_datetime.now.return_value = datetime(2024, 1, 13, 10, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = is_china_stock_market_open()
        assert result == False
    
    @patch('src.utils.trading_hours.ak')
    @patch('src.utils.trading_hours.datetime')
    def test_hk_market_open_weekday(self, mock_datetime, mock_ak):
        """测试港股市场工作日开盘"""
        # 模拟akshare返回数据
        mock_df = pd.DataFrame({
            'date': [datetime(2024, 1, 15).date()]
        })
        mock_ak.stock_hk_index_daily_sina.return_value = mock_df
        
        # 模拟当前日期
        mock_datetime.now.return_value = datetime(2024, 1, 15, 10, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = is_hk_stock_market_open()
        assert result == True
    
    @patch('src.utils.trading_hours.ak')
    @patch('src.utils.trading_hours.datetime')
    def test_hk_market_closed_weekend(self, mock_datetime, mock_ak):
        """测试港股市场周末休市"""
        # 模拟akshare返回数据（最后交易日是周五）
        mock_df = pd.DataFrame({
            'date': [datetime(2024, 1, 12).date()]  # 周五
        })
        mock_ak.stock_hk_index_daily_sina.return_value = mock_df
        
        # 模拟当前日期（周六）
        mock_datetime.now.return_value = datetime(2024, 1, 13, 10, 0)
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        result = is_hk_stock_market_open()
        assert result == False
