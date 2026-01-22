"""
API失败处理：管理API调用失败计数和用户确认
"""
import threading
from typing import Callable, Optional


class APIConfirmationRequired(Exception):
    """需要用户确认是否继续API调用的异常"""
    def __init__(self, failure_count: int, error_message: str):
        self.failure_count = failure_count
        self.error_message = error_message
        super().__init__(f"API调用已连续失败{failure_count}次，需要用户确认是否继续")


class APIFailureHandler:
    """API失败处理器（单例模式）"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.failure_count = 0
            self.confirmation_callback: Optional[Callable[[int, str], bool]] = None
            self._lock = threading.Lock()
            self._initialized = True
    
    def set_confirmation_callback(self, callback: Callable[[int, str], bool]):
        """
        设置用户确认回调函数
        
        Args:
            callback: 回调函数，接收(failure_count, error_message)参数，返回True继续，False停止
        """
        self.confirmation_callback = callback
    
    def record_success(self):
        """记录API调用成功，重置失败计数"""
        with self._lock:
            self.failure_count = 0
    
    def record_failure(self, error_message: str = "") -> bool:
        """
        记录API调用失败
        
        Args:
            error_message: 错误消息
            
        Returns:
            True: 继续调用
            False: 停止调用
            
        Raises:
            APIConfirmationRequired: 需要用户确认时抛出
        """
        with self._lock:
            self.failure_count += 1
            
            # 每3次失败后询问用户
            if self.failure_count % 3 == 0:
                if self.confirmation_callback:
                    # 有回调函数，调用它获取用户确认
                    should_continue = self.confirmation_callback(self.failure_count, error_message)
                    if not should_continue:
                        # 用户选择停止，重置计数并返回False
                        self.failure_count = 0
                        return False
                    # 用户选择继续，重置计数
                    self.failure_count = 0
                    return True
                else:
                    # 没有回调函数，抛出异常让上层处理
                    raise APIConfirmationRequired(self.failure_count, error_message)
            
            return True
    
    def get_failure_count(self) -> int:
        """获取当前失败计数"""
        with self._lock:
            return self.failure_count
    
    def reset(self):
        """重置失败计数"""
        with self._lock:
            self.failure_count = 0


# 全局单例实例
api_failure_handler = APIFailureHandler()

