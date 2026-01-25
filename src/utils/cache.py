"""
数据缓存模块
提供文件缓存机制，支持TTL（生存时间），避免重复数据请求
"""
import os
import pickle
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache", default_ttl_hours: int = 1):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
            default_ttl_hours: 默认缓存生存时间（小时）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl_hours = default_ttl_hours
        
        # 元数据文件路径
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载缓存元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载缓存元数据失败: {e}")
        return {}
    
    def _save_metadata(self):
        """保存缓存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"保存缓存元数据失败: {e}")
    
    def _get_cache_key(self, key: str, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            key: 基础键名
            **kwargs: 额外的参数（用于区分不同的请求）
        
        Returns:
            str: 缓存键（文件名）
        """
        # 将参数排序后序列化，确保相同参数生成相同键
        params_str = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
        combined = f"{key}_{params_str}"
        
        # 使用MD5生成短文件名
        hash_obj = hashlib.md5(combined.encode('utf-8'))
        return f"{hash_obj.hexdigest()}.pkl"
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / cache_key
    
    def get(
        self,
        key: str,
        ttl_hours: Optional[int] = None,
        **kwargs
    ) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            key: 缓存键名
            ttl_hours: 缓存生存时间（小时），None使用默认值
            **kwargs: 额外的参数（用于区分不同的请求）
        
        Returns:
            缓存的数据，如果不存在或已过期返回None
        """
        cache_key = self._get_cache_key(key, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            logger.debug(f"缓存不存在: {key}")
            return None
        
        # 检查是否过期
        if cache_key in self.metadata:
            created_time = datetime.fromisoformat(self.metadata[cache_key]['created_at'])
            ttl = timedelta(hours=ttl_hours or self.default_ttl_hours)
            
            if datetime.now() - created_time > ttl:
                logger.debug(f"缓存已过期: {key} (创建于 {created_time})")
                self.delete(key, **kwargs)
                return None
        
        # 读取缓存文件
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            logger.debug(f"从缓存读取: {key}")
            return data
        except Exception as e:
            logger.warning(f"读取缓存失败: {key}, 错误: {e}")
            # 删除损坏的缓存文件
            if cache_path.exists():
                cache_path.unlink()
            if cache_key in self.metadata:
                del self.metadata[cache_key]
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_hours: Optional[int] = None,
        **kwargs
    ):
        """
        保存数据到缓存
        
        Args:
            key: 缓存键名
            value: 要缓存的数据
            ttl_hours: 缓存生存时间（小时），None使用默认值
            **kwargs: 额外的参数（用于区分不同的请求）
        """
        cache_key = self._get_cache_key(key, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            # 保存数据
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            
            # 更新元数据
            self.metadata[cache_key] = {
                'key': key,
                'created_at': datetime.now().isoformat(),
                'ttl_hours': ttl_hours or self.default_ttl_hours,
                'params': kwargs
            }
            self._save_metadata()
            
            logger.debug(f"保存到缓存: {key}")
        except Exception as e:
            logger.warning(f"保存缓存失败: {key}, 错误: {e}")
    
    def delete(self, key: str, **kwargs):
        """
        删除缓存
        
        Args:
            key: 缓存键名
            **kwargs: 额外的参数
        """
        cache_key = self._get_cache_key(key, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        if cache_path.exists():
            cache_path.unlink()
        
        if cache_key in self.metadata:
            del self.metadata[cache_key]
            self._save_metadata()
        
        logger.debug(f"删除缓存: {key}")
    
    def clear(self, pattern: Optional[str] = None):
        """
        清空缓存
        
        Args:
            pattern: 可选，如果提供则只删除匹配的缓存（支持通配符）
        """
        if pattern:
            # 删除匹配的缓存
            import fnmatch
            for cache_key in list(self.metadata.keys()):
                if fnmatch.fnmatch(self.metadata[cache_key]['key'], pattern):
                    cache_path = self._get_cache_path(cache_key)
                    if cache_path.exists():
                        cache_path.unlink()
                    del self.metadata[cache_key]
        else:
            # 清空所有缓存
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            self.metadata = {}
        
        self._save_metadata()
        logger.info(f"清空缓存: {pattern or '全部'}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_size = sum(
            f.stat().st_size
            for f in self.cache_dir.glob("*.pkl")
        )
        
        return {
            'total_files': len(list(self.cache_dir.glob("*.pkl"))),
            'total_size_mb': total_size / (1024 * 1024),
            'metadata_entries': len(self.metadata)
        }


# 全局缓存实例
_cache_instance: Optional[DataCache] = None


def get_cache(cache_dir: Optional[str] = None, default_ttl_hours: Optional[int] = None) -> Optional[DataCache]:
    """
    获取全局缓存实例（单例模式）
    
    Args:
        cache_dir: 缓存目录，如果为None则从配置加载
        default_ttl_hours: 默认TTL，如果为None则从配置加载
    
    Returns:
        DataCache: 缓存实例，如果缓存被禁用则返回None
    """
    global _cache_instance
    
    if _cache_instance is None:
        # 尝试从配置加载
        try:
            from src.config import Config
            config = Config()
            cache_config = config.get('cache', {})
            
            # 检查缓存是否启用
            if not cache_config.get('enabled', True):
                logger.info("缓存功能已禁用")
                return None
            
            cache_dir = cache_dir or cache_config.get('dir', 'cache')
            default_ttl_hours = default_ttl_hours or cache_config.get('default_ttl_hours', 1)
        except Exception:
            cache_dir = cache_dir or 'cache'
            default_ttl_hours = default_ttl_hours or 1
        
        _cache_instance = DataCache(cache_dir, default_ttl_hours)
    
    return _cache_instance
