"""
测试代码标准化函数
"""

import pytest
from src.utils.code_normalizer import normalize_code, is_hk_stock, normalize_hk_code, parse_stock_list


class TestCodeNormalizer:
    """代码标准化测试类"""

    def test_normalize_a_share_code_sh(self):
        """测试上海A股代码标准化"""
        assert normalize_code("600460") == "sh600460"
        assert normalize_code("688630") == "sh688630"
        assert normalize_code("sh600460") == "sh600460"

    def test_normalize_a_share_code_sz(self):
        """测试深圳A股代码标准化"""
        assert normalize_code("300474") == "sz300474"
        assert normalize_code("000001") == "sz000001"
        assert normalize_code("sz300474") == "sz300474"

    def test_normalize_hk_code(self):
        """测试港股代码标准化"""
        assert normalize_hk_code("00700") == "HK.00700"
        assert normalize_hk_code("700") == "HK.00700"
        assert normalize_hk_code("00700.HK") == "HK.00700"
        assert normalize_hk_code("HK.00700") == "HK.00700"

    def test_is_hk_stock(self):
        """测试港股识别"""
        assert is_hk_stock("00700") is True
        assert is_hk_stock("700") is False  # 3位数字不是港股
        assert is_hk_stock("00700.HK") is True
        assert is_hk_stock("HK.00700") is True
        assert is_hk_stock("600460") is False
        assert is_hk_stock("300474") is False

    def test_parse_stock_list(self):
        """测试股票列表解析"""
        # 空格分隔
        assert parse_stock_list("600460 300474") == ["600460", "300474"]
        # 逗号分隔
        assert parse_stock_list("600460,300474") == ["600460", "300474"]
        # 中文逗号
        assert parse_stock_list("600460，300474") == ["600460", "300474"]
        # 混合
        assert parse_stock_list("600460, 300474 300623") == ["600460", "300474", "300623"]
        # 空字符串
        assert parse_stock_list("") == []
        # None
        assert parse_stock_list(None) == []
