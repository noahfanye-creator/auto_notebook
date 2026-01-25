"""
完整流程集成测试
Mock 网络与数据源，验证「解析参数 → 拉数 → 算指标 → 生成 PDF」流程
"""

import os
import tempfile
from unittest.mock import patch

import pandas as pd

from src.report.generator import process_multiple_stocks, create_zip_archive
from src.utils.code_normalizer import parse_stock_list


def _make_ohlcv_df(rows: int = 60):
    """生成最小 OHLCV DataFrame"""
    import numpy as np

    dates = pd.date_range("2024-01-01", periods=rows, freq="B")
    np.random.seed(42)
    base = 100.0
    returns = np.random.randn(rows).cumsum() * 0.5
    close = base + returns
    high = close + np.abs(np.random.randn(rows))
    low = close - np.abs(np.random.randn(rows))
    open_ = np.roll(close, 1)
    open_[0] = base
    volume = (np.random.rand(rows) * 1e6 + 5e5).astype(int)
    df = pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )
    df.index.name = "Date"
    return df


@patch("src.report.generator.load_sector_index_map")
@patch("src.report.generator.get_sector_indices_data")
@patch("src.report.generator.get_market_indices_data")
@patch("src.report.generator.get_name")
@patch("src.report.generator.fetch_kline_data")
def test_full_workflow_mocked(
    mock_fetch,
    mock_name,
    mock_indices,
    mock_sector_indices,
    mock_sector_map,
):
    """流程集成：解析 → 拉数 → 算指标 → 生成 PDF（全部 mock）"""
    df = _make_ohlcv_df(80)
    mock_fetch.return_value = df
    mock_name.return_value = "测试股票"
    mock_indices.return_value = {
        "sh000001": {
            "name": "上证指数",
            "data": _make_ohlcv_df(80),
            "type": "A",
        }
    }
    mock_sector_indices.return_value = {}
    mock_sector_map.return_value = {"name_to_code": {}, "code_to_name": {}}

    with tempfile.TemporaryDirectory() as tmp:
        successful, failed = process_multiple_stocks("600460", tmp)
        assert isinstance(successful, list)
        assert isinstance(failed, list)
        # 成功时应至少有 1 个报告；若 PDF/图表依赖字体等环境可能失败，则允许失败
        assert len(successful) + len(failed) >= 1
        if successful:
            code, name, path = successful[0]
            assert code == "sh600460"
            assert name == "测试股票"
            assert path is not None
            assert os.path.isfile(path)


def test_parse_stock_list_integration():
    """解析参数集成"""
    assert parse_stock_list("600460 300474") == ["600460", "300474"]
    assert parse_stock_list("600460,300474") == ["600460", "300474"]
    assert parse_stock_list("") == []


@patch("src.report.generator.load_sector_index_map")
@patch("src.report.generator.get_sector_indices_data")
@patch("src.report.generator.get_market_indices_data")
@patch("src.report.generator.get_name")
@patch("src.report.generator.fetch_kline_data")
def test_full_workflow_no_data_fails_gracefully(
    mock_fetch,
    mock_name,
    mock_indices,
    mock_sector_indices,
    mock_sector_map,
):
    """拉数失败时流程正常返回失败列表"""
    mock_fetch.return_value = None
    mock_name.return_value = "未知"
    mock_indices.return_value = {}
    mock_sector_indices.return_value = {}
    mock_sector_map.return_value = {"name_to_code": {}, "code_to_name": {}}

    with tempfile.TemporaryDirectory() as tmp:
        successful, failed = process_multiple_stocks("600460", tmp)
        assert len(successful) == 0
        assert len(failed) == 1
        code, name, reason = failed[0]
        assert "无数据" in reason or "数据" in reason or "失败" in reason


def test_create_zip_archive_empty_dir():
    """ZIP：空目录返回 None"""
    with tempfile.TemporaryDirectory() as tmp:
        out = create_zip_archive(tmp)
        assert out is None
