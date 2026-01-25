"""
配置加载器
支持从YAML文件加载配置，并支持环境变量覆盖
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


class Config:
    """配置管理类（单例模式）"""

    _instance = None
    _config = None
    _config_path = None

    def __new__(cls, config_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config_path = config_path
        return cls._instance

    def _load_config_file(self) -> Dict[str, Any]:
        """从YAML文件加载配置"""
        if self._config is not None:
            return self._config

        # 确定配置文件路径
        if self._config_path:
            config_file = Path(self._config_path)
        else:
            # 默认查找顺序：config/config.yaml -> config/config.example.yaml
            project_root = Path(__file__).parent.parent.parent
            config_file = project_root / "config" / "config.yaml"

            if not config_file.exists():
                config_file = project_root / "config" / "config.example.yaml"

        if not config_file.exists():
            # 如果配置文件不存在，返回默认配置
            print(f"⚠️  配置文件不存在: {config_file}，使用默认配置")
            return self._get_default_config()

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}

            # 应用环境变量覆盖
            self._apply_env_overrides()

            return self._config
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "stocks": {"default": ["600460", "300474", "300623", "300420"]},
            "indicators": {
                "ma_windows": [5, 10, 20, 60, 250],
                "macd": {"fast": 12, "slow": 26, "signal": 9},
                "rsi": 14,
                "boll": 20,
                "kdj": 9,
                "wr": 14,
                "volume_ma": [5, 10],
            },
            "report": {"output_dir": "reports", "include_charts": True, "chart_dpi": 150},
            "data": {"kline": {"default_datalen": 150, "default_scale": 240}},
            "database": {"enabled": True, "path": "data/stock_data.db"},
            "delays": {"hk_stock": 3, "sector": 3, "normal": 1},
        }

    def _apply_env_overrides(self):
        """应用环境变量覆盖配置"""
        if not self._config:
            return

        # 支持通过环境变量覆盖股票列表
        env_stocks = os.getenv("TARGET_STOCKS")
        if env_stocks:
            stocks_list = [s.strip() for s in env_stocks.split(",")]
            if "stocks" not in self._config:
                self._config["stocks"] = {}
            self._config["stocks"]["default"] = stocks_list

        # 支持通过环境变量覆盖报告输出目录
        env_output_dir = os.getenv("REPORT_OUTPUT_DIR")
        if env_output_dir:
            if "report" not in self._config:
                self._config["report"] = {}
            self._config["report"]["output_dir"] = env_output_dir

        # 支持通过环境变量覆盖日志级别
        env_log_level = os.getenv("LOG_LEVEL")
        if env_log_level:
            if "logging" not in self._config:
                self._config["logging"] = {}
            self._config["logging"]["level"] = env_log_level

    def load(self) -> Dict[str, Any]:
        """加载配置"""
        return self._load_config_file()

    @property
    def stocks(self) -> List[str]:
        """获取目标股票列表"""
        config = self.load()
        return config.get("stocks", {}).get("default", [])

    @property
    def indicator_params(self) -> Dict[str, Any]:
        """获取技术指标参数"""
        config = self.load()
        indicators = config.get("indicators", {})

        # 转换MACD配置格式
        macd_config = indicators.get("macd", {})
        if isinstance(macd_config, dict):
            macd = [macd_config.get("fast", 12), macd_config.get("slow", 26), macd_config.get("signal", 9)]
        else:
            macd = macd_config if isinstance(macd_config, list) else [12, 26, 9]

        return {
            "ma_windows": indicators.get("ma_windows", [5, 10, 20, 60, 250]),
            "macd": macd,
            "rsi": indicators.get("rsi", 14),
            "boll": indicators.get("boll", 20),
            "kdj": indicators.get("kdj", 9),
            "wr": indicators.get("wr", 14),
            "volume_ma": indicators.get("volume_ma", [5, 10]),
        }

    @property
    def report_output_dir(self) -> str:
        """获取报告输出目录"""
        config = self.load()
        return config.get("report", {}).get("output_dir", "reports")

    @property
    def data_config(self) -> Dict[str, Any]:
        """获取数据获取配置"""
        config = self.load()
        return config.get("data", {})

    @property
    def delays(self) -> Dict[str, int]:
        """获取延迟配置"""
        config = self.load()
        return config.get("delays", {"hk_stock": 3, "sector": 3, "normal": 1})

    @property
    def chart_config(self) -> Dict[str, Any]:
        """获取图表配置"""
        config = self.load()
        report_config = config.get("report", {})
        return {
            "include_charts": report_config.get("include_charts", True),
            "chart_dpi": report_config.get("chart_dpi", 150),
            "max_points": report_config.get("max_points", {"day": 60, "week": 60, "month": 60, "minute": 100}),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔的嵌套键）"""
        config = self.load()
        keys = key.split(".")
        value = config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def reload(self):
        """重新加载配置"""
        self._config = None
        return self.load()
