"""
图表生成模块
创建K线图表和指数图表
"""

import os
from typing import Optional
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.font_manager as fm  # noqa: E402

from src.data.fetchers import normalize_beijing_time, is_intraday_data  # noqa: E402


def create_candle_chart(df: Optional[pd.DataFrame], title: str, filename: str, max_points: int = 60) -> bool:
    """创建K线图表（增强版，添加成交量和量比图表）

    Args:
        df: K线数据 DataFrame
        title: 图表标题
        filename: 保存文件路径
        max_points: 最大显示点数

    Returns:
        bool: 是否生成成功
    """
    if df is None or len(df) < 5:
        return False

    try:
        plot_data = df.tail(min(max_points, len(df))).copy()
        plot_data = normalize_beijing_time(plot_data)

        fig, axes = plt.subplots(4, 1, figsize=(12, 12), gridspec_kw={"height_ratios": [3, 1, 1, 1]})

        ax1, ax2, ax3, ax4 = axes

        # 设置中文字体，避免乱码
        font_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "SimHei.ttf"),
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
        font_set = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    fm.fontManager.addfont(font_path)
                    font_prop = fm.FontProperties(fname=font_path)
                    font_name = font_prop.get_name()
                    plt.rcParams["font.sans-serif"] = [font_name, "Arial", "DejaVu Sans"]
                    plt.rcParams["axes.unicode_minus"] = False
                    font_set = True
                    break
                except Exception:
                    continue
        if not font_set:
            plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False

        dates = plot_data.index.to_list()
        intraday = is_intraday_data(plot_data)
        x = np.arange(len(dates)) if intraday else mdates.date2num(dates)
        opens = plot_data["Open"].values
        highs = plot_data["High"].values
        lows = plot_data["Low"].values
        closes = plot_data["Close"].values
        volumes = plot_data["Volume"].values if "Volume" in plot_data.columns else np.zeros(len(dates))

        volume_ratios = plot_data["Volume_Ratio"].values if "Volume_Ratio" in plot_data.columns else None

        # 绘制K线
        for i, date in enumerate(dates):
            color = "red" if closes[i] >= opens[i] else "green"

            ax1.plot([x[i], x[i]], [highs[i], max(opens[i], closes[i])], color=color, linewidth=1)
            ax1.plot([x[i], x[i]], [min(opens[i], closes[i]), lows[i]], color=color, linewidth=1)

            from matplotlib.patches import Rectangle

            body_bottom = min(opens[i], closes[i])
            body_height = abs(closes[i] - opens[i])

            if body_height > 0:
                rect = Rectangle(
                    (x[i] - 0.3, body_bottom), 0.6, body_height, facecolor=color, edgecolor=color, alpha=0.8
                )
                ax1.add_patch(rect)

        if "MA5" in plot_data.columns:
            ax1.plot(x, plot_data["MA5"], "orange", linewidth=1.5, label="MA5")
        if "MA10" in plot_data.columns:
            ax1.plot(x, plot_data["MA10"], "blue", linewidth=1.5, label="MA10")
        if "MA20" in plot_data.columns:
            ax1.plot(x, plot_data["MA20"], "purple", linewidth=1.5, label="MA20")

        if "BB_Upper" in plot_data.columns:
            ax1.plot(x, plot_data["BB_Upper"], "gray", linewidth=1, label="BB Upper", alpha=0.5)
            ax1.plot(x, plot_data["BB_Middle"], "black", linewidth=1, label="BB Middle", alpha=0.5)
            ax1.plot(x, plot_data["BB_Lower"], "gray", linewidth=1, label="BB Lower", alpha=0.5)

        english_title = (
            title.replace("日线", "Daily").replace("周线", "Weekly").replace("月线", "Monthly").replace("分钟", "Min")
        )
        ax1.set_title(english_title, fontsize=16, fontweight="bold")
        ax1.set_ylabel("Price")
        ax1.legend(loc="upper left", fontsize="small")
        ax1.grid(True, alpha=0.3)

        if not intraday:
            ax1.xaxis_date()
            ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

        # MACD
        if "MACD" in plot_data.columns:
            macd_colors = ["red" if v >= 0 else "green" for v in plot_data["MACD"]]
            ax2.bar(x, plot_data["MACD"], color=macd_colors, alpha=0.7, width=0.8)
            ax2.plot(x, plot_data["DIF"], "black", linewidth=1.5, label="DIF")
            ax2.plot(x, plot_data["DEA"], "orange", linewidth=1.5, label="DEA")
            ax2.axhline(y=0, color="gray", linestyle="-", linewidth=0.5, alpha=0.5)

        ax2.set_ylabel("MACD")
        ax2.legend(loc="upper left", fontsize="small")
        ax2.grid(True, alpha=0.3)
        if not intraday:
            ax2.xaxis_date()
            ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        # KDJ
        if "K" in plot_data.columns and "D" in plot_data.columns and "J" in plot_data.columns:
            ax3.plot(x, plot_data["K"], "blue", linewidth=1.5, label="K")
            ax3.plot(x, plot_data["D"], "orange", linewidth=1.5, label="D")
            ax3.plot(x, plot_data["J"], "purple", linewidth=1.5, label="J")
            ax3.axhline(y=80, color="red", linestyle="--", linewidth=0.5, alpha=0.5)
            ax3.axhline(y=20, color="green", linestyle="--", linewidth=0.5, alpha=0.5)
            ax3.axhline(y=50, color="gray", linestyle="-", linewidth=0.5, alpha=0.3)

        ax3.set_ylabel("KDJ")
        ax3.set_ylim(-20, 120)
        ax3.legend(loc="upper left", fontsize="small")
        ax3.grid(True, alpha=0.3)
        if not intraday:
            ax3.xaxis_date()
            ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

        # 成交量+量比
        ax4_volume = ax4
        ax4_ratio = ax4.twinx()

        volume_colors = ["red" if closes[i] >= opens[i] else "green" for i in range(len(dates))]
        ax4_volume.bar(x, volumes, color=volume_colors, alpha=0.7, width=0.8, label="Volume")

        if "Volume_MA5" in plot_data.columns:
            ax4_volume.plot(x, plot_data["Volume_MA5"], "orange", linewidth=1.5, label="Volume MA5")
        if "Volume_MA10" in plot_data.columns:
            ax4_volume.plot(x, plot_data["Volume_MA10"], "blue", linewidth=1.5, label="Volume MA10")

        ax4_volume.set_xlabel("Date")
        ax4_volume.set_ylabel("Volume", color="black")
        ax4_volume.tick_params(axis="y", labelcolor="black")

        if max(volumes) > 10000:
            ax4_volume.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

        if volume_ratios is not None:
            ax4_ratio.plot(
                x, volume_ratios, "purple", linewidth=2, label="Volume Ratio", linestyle="-", marker="o", markersize=3
            )
            ax4_ratio.set_ylabel("Volume Ratio", color="purple")
            ax4_ratio.tick_params(axis="y", labelcolor="purple")

            ax4_ratio.axhline(y=1.0, color="gray", linestyle="--", linewidth=0.5, alpha=0.5, label="Ratio=1")
            ax4_ratio.axhline(y=1.5, color="orange", linestyle="--", linewidth=0.5, alpha=0.5, label="Ratio=1.5")
            ax4_ratio.axhline(y=0.5, color="blue", linestyle="--", linewidth=0.5, alpha=0.5, label="Ratio=0.5")

        lines1, labels1 = ax4_volume.get_legend_handles_labels()
        lines2, labels2 = ax4_ratio.get_legend_handles_labels()
        ax4_volume.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize="small")

        ax4_volume.set_title("Volume & Volume Ratio Analysis", fontsize=12, fontweight="bold")
        ax4_volume.grid(True, alpha=0.3)
        if not intraday:
            ax4_volume.xaxis_date()
            ax4_volume.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            plt.setp(ax4_volume.xaxis.get_majorticklabels(), rotation=45)
        else:
            tick_count = min(6, len(x))
            tick_positions = np.linspace(0, len(x) - 1, tick_count, dtype=int)
            tick_labels = [dates[i].strftime("%m-%d %H:%M") for i in tick_positions]
            for ax in [ax1, ax2, ax3, ax4_volume]:
                ax.set_xticks(tick_positions)
                ax.set_xticklabels(tick_labels, rotation=45)

        plt.tight_layout()
        plt.savefig(filename, dpi=120, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        if os.path.exists(filename) and os.path.getsize(filename) > 1024:
            print(f"   图表生成成功: {os.path.basename(filename)}")
            return True
        else:
            print("   图表生成失败")
            return False

    except Exception as e:
        print(f"   图表生成失败: {str(e)[:100]}")
        import traceback

        traceback.print_exc()
        return False


def create_indices_charts(indices_data: dict, temp_dir: str) -> int:
    """为所有指数生成图表

    Args:
        indices_data: 指数数据字典
        temp_dir: 临时目录路径

    Returns:
        int: 成功生成的图表数量
    """
    charts_created = 0

    for code, info in indices_data.items():
        df = info["data"]
        name = info["name"]

        if df is not None and len(df) >= 10:
            img_path = os.path.join(temp_dir, f"index_{code}.png")
            title = f"{name} 日线"

            if create_candle_chart(df, title, img_path, max_points=60):
                charts_created += 1

    return charts_created
