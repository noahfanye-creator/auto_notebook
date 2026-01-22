#!/usr/bin/env python3
"""
数据可视化模块
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

class StockChart:
    """股票图表绘制器"""
    
    def __init__(self, style='seaborn'):
        plt.style.use(style)
    
    def plot_price(self, df, symbol, save_path=None):
        """绘制价格图表"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 绘制收盘价
        ax.plot(df.index, df['收盘'], label='收盘价', color='blue', linewidth=2)
        
        # 设置标题和标签
        ax.set_title(f'{symbol} 价格走势', fontsize=16, fontweight='bold')
        ax.set_xlabel('日期')
        ax.set_ylabel('价格 (USD)')
        
        # 格式设置
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # 日期格式
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"📊 图表已保存: {save_path}")
        
        return fig, ax
    
    def plot_with_volume(self, df, symbol, save_path=None):
        """绘制价格和成交量组合图表"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # 价格图表
        ax1.plot(df.index, df['收盘'], label='收盘价', color='blue', linewidth=2)
        ax1.set_title(f'{symbol} 价格走势与成交量', fontsize=16, fontweight='bold')
        ax1.set_ylabel('价格 (USD)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 成交量图表
        colors = ['green' if close >= open_ else 'red' 
                 for close, open_ in zip(df['收盘'], df['开盘'])]
        ax2.bar(df.index, df['成交量'], color=colors, alpha=0.6)
        ax2.set_ylabel('成交量')
        ax2.grid(True, alpha=0.3)
        
        # 日期格式
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"📊 组合图表已保存: {save_path}")
        
        return fig, (ax1, ax2)
