"""
并发处理模块
提供并行处理功能，提升批量处理效率
"""
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Callable, Any, Tuple, Optional
import threading
from functools import wraps

from src.utils.logger import get_logger

logger = get_logger(__name__)


def parallel_process(
    items: List[Any],
    func: Callable,
    max_workers: Optional[int] = None,
    use_processes: bool = False,
    timeout: Optional[float] = None
) -> List[Tuple[Any, Any, Optional[Exception]]]:
    """
    并行处理多个项目
    
    Args:
        items: 要处理的项目列表
        func: 处理函数，接受单个项目作为参数，返回处理结果
        max_workers: 最大并发数，None则使用默认值
        use_processes: 是否使用进程池（默认使用线程池）
        timeout: 单个任务超时时间（秒）
    
    Returns:
        List[Tuple[item, result, error]]: 处理结果列表，每个元素为(原始项目, 处理结果, 异常)
    """
    if not items:
        return []
    
    # 确定最大并发数
    if max_workers is None:
        max_workers = min(len(items), 5)  # 默认最多5个并发
    
    results = []
    executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    
    with executor_class(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_item = {
            executor.submit(func, item): item
            for item in items
        }
        
        # 收集结果
        for future in as_completed(future_to_item, timeout=timeout):
            item = future_to_item[future]
            try:
                result = future.result(timeout=timeout)
                results.append((item, result, None))
                logger.debug(f"✅ 处理完成: {item}")
            except Exception as e:
                logger.error(f"❌ 处理失败 {item}: {e}", exc_info=True)
                results.append((item, None, e))
    
    return results


def parallel_map(
    items: List[Any],
    func: Callable,
    max_workers: Optional[int] = None,
    use_processes: bool = False
) -> List[Any]:
    """
    并行映射处理（简化版本，只返回结果）
    
    Args:
        items: 要处理的项目列表
        func: 处理函数
        max_workers: 最大并发数
        use_processes: 是否使用进程池
    
    Returns:
        List[Any]: 处理结果列表（失败的项目返回None）
    """
    results = parallel_process(items, func, max_workers, use_processes)
    return [result if error is None else None for _, result, error in results]


class ThreadSafeCounter:
    """线程安全的计数器"""
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self, amount: int = 1) -> int:
        """增加计数并返回新值"""
        with self._lock:
            self._value += amount
            return self._value
    
    def get(self) -> int:
        """获取当前值"""
        with self._lock:
            return self._value
    
    def reset(self):
        """重置计数器"""
        with self._lock:
            self._value = 0


def batch_process(
    items: List[Any],
    func: Callable,
    batch_size: int = 5,
    max_workers: Optional[int] = None,
    delay_between_batches: float = 0
) -> List[Tuple[Any, Any, Optional[Exception]]]:
    """
    分批并发处理（避免过多并发导致API限制）
    
    Args:
        items: 要处理的项目列表
        func: 处理函数
        batch_size: 每批处理的数量
        max_workers: 每批的最大并发数
        delay_between_batches: 批次之间的延迟（秒）
    
    Returns:
        List[Tuple[item, result, error]]: 处理结果列表
    """
    all_results = []
    total = len(items)
    
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        logger.info(f"📦 处理批次 {batch_num}/{total_batches} ({len(batch)} 个项目)")
        
        # 处理当前批次
        batch_results = parallel_process(batch, func, max_workers)
        all_results.extend(batch_results)
        
        # 批次间延迟（最后一批不需要延迟）
        if delay_between_batches > 0 and i + batch_size < total:
            import time
            logger.debug(f"💤 批次间延迟 {delay_between_batches} 秒...")
            time.sleep(delay_between_batches)
    
    return all_results


def retry_on_failure(max_retries: int = 3, delay: float = 1):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️  第 {attempt + 1} 次尝试失败，{delay}秒后重试: {e}")
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ 重试 {max_retries} 次后仍失败: {e}")
            raise last_exception
        return wrapper
    return decorator
