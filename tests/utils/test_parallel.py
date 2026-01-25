"""
测试并发处理模块
"""
import pytest
import time
from src.utils.parallel import (
    parallel_process,
    batch_process,
    parallel_map,
    ThreadSafeCounter
)


class TestParallelProcessing:
    """并发处理测试类"""
    
    def test_parallel_process(self):
        """测试基础并发处理"""
        def square(x):
            return x * x
        
        items = [1, 2, 3, 4, 5]
        results = parallel_process(items, square, max_workers=3)
        
        # 检查结果
        assert len(results) == len(items)
        for item, result, error in results:
            assert error is None
            assert result == item * item
    
    def test_parallel_process_with_error(self):
        """测试并发处理中的错误处理"""
        def failing_func(x):
            if x == 3:
                raise ValueError("Test error")
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        results = parallel_process(items, failing_func, max_workers=3)
        
        # 检查结果
        assert len(results) == len(items)
        # 找到失败的项目
        failed = [r for r in results if r[2] is not None]
        assert len(failed) == 1
        assert failed[0][0] == 3
    
    def test_batch_process(self):
        """测试分批并发处理"""
        def slow_task(x):
            time.sleep(0.1)
            return x * 2
        
        items = list(range(10))
        results = batch_process(items, slow_task, batch_size=5, max_workers=3)
        
        assert len(results) == len(items)
        for item, result, error in results:
            assert error is None
            assert result == item * 2
    
    def test_parallel_map(self):
        """测试并发映射"""
        def square(x):
            return x * x
        
        items = [1, 2, 3, 4, 5]
        results = parallel_map(items, square, max_workers=3)
        
        assert len(results) == len(items)
        # 并发处理结果顺序可能不同，需要排序比较
        assert sorted(results) == [1, 4, 9, 16, 25]
    
    def test_thread_safe_counter(self):
        """测试线程安全计数器"""
        counter = ThreadSafeCounter(0)
        
        # 单线程测试
        assert counter.increment() == 1
        assert counter.increment(5) == 6
        assert counter.get() == 6
        
        counter.reset()
        assert counter.get() == 0
