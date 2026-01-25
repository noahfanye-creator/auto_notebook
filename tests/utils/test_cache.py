"""
测试缓存模块
"""

import pytest
import pandas as pd
import time
from src.utils.cache import DataCache, get_cache


class TestDataCache:
    """数据缓存测试类"""

    @pytest.fixture
    def cache(self, tmp_path):
        """创建临时缓存实例"""
        cache_dir = tmp_path / "test_cache"
        return DataCache(str(cache_dir), default_ttl_hours=1)

    def test_cache_set_and_get(self, cache):
        """测试缓存保存和读取"""
        test_data = pd.DataFrame({"value": [1, 2, 3]})

        # 保存
        cache.set("test_key", test_data, symbol="sh600460", scale=240)

        # 读取
        result = cache.get("test_key", symbol="sh600460", scale=240)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert list(result["value"]) == [1, 2, 3]

    def test_cache_key_generation(self, cache):
        """测试缓存键生成"""
        key1 = cache._get_cache_key("test", symbol="sh600460", scale=240)
        key2 = cache._get_cache_key("test", symbol="sh600460", scale=240)
        key3 = cache._get_cache_key("test", symbol="sh600460", scale=30)

        # 相同参数应生成相同键
        assert key1 == key2
        # 不同参数应生成不同键
        assert key1 != key3

    def test_cache_ttl_expiration(self, cache):
        """测试TTL过期"""
        test_data = pd.DataFrame({"value": [1, 2, 3]})

        # 保存（1秒TTL）
        cache.set("ttl_test", test_data, ttl_hours=1 / 3600, symbol="test")

        # 立即读取（应该成功）
        result = cache.get("ttl_test", ttl_hours=1 / 3600, symbol="test")
        assert result is not None

        # 等待2秒后读取（应该失败）
        time.sleep(2)
        result = cache.get("ttl_test", ttl_hours=1 / 3600, symbol="test")
        assert result is None

    def test_cache_delete(self, cache):
        """测试缓存删除"""
        test_data = pd.DataFrame({"value": [1, 2, 3]})

        # 保存
        cache.set("delete_test", test_data, symbol="test")

        # 删除
        cache.delete("delete_test", symbol="test")

        # 读取应该失败
        result = cache.get("delete_test", symbol="test")
        assert result is None

    def test_cache_stats(self, cache):
        """测试缓存统计"""
        test_data = pd.DataFrame({"value": [1, 2, 3]})

        # 保存几个缓存
        for i in range(3):
            cache.set(f"test_{i}", test_data, symbol=f"stock_{i}")

        stats = cache.get_stats()

        assert stats["total_files"] == 3
        assert stats["metadata_entries"] == 3
        assert stats["total_size_mb"] > 0

    def test_get_cache_singleton(self):
        """测试缓存单例模式"""
        cache1 = get_cache()
        cache2 = get_cache()

        # 应该是同一个实例
        assert cache1 is cache2
