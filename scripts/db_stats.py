#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库统计工具
查看本地数据库的积累情况
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.database import get_stock_db
from src.config import Config


def main():
    """显示数据库统计信息"""
    print("=" * 70)
    print("📊 本地数据库统计信息")
    print("=" * 70)
    
    config = Config()
    db_cfg = config.get('database', {})
    
    if not db_cfg.get('enabled', False):
        print("❌ 数据库功能未启用")
        print("请在 config/config.yaml 中设置 database.enabled: true")
        return
    
    db_path = db_cfg.get('path', 'data/stock_data.db')
    print(f"📁 数据库路径: {db_path}")
    
    db = get_stock_db()
    if db is None:
        print("❌ 无法连接数据库")
        return
    
    try:
        stats = db.get_stats()
        
        print("\n📈 K线数据统计:")
        print(f"  总记录数: {stats.get('total_kline_records', 0):,} 条")
        print(f"  股票数量: {stats.get('total_stocks', 0)} 只")
        
        print("\n📊 市场指数数据统计:")
        print(f"  总记录数: {stats.get('total_index_records', 0):,} 条")
        print(f"  指数数量: {stats.get('total_indices', 0)} 个")
        
        if 'db_size_mb' in stats:
            print(f"\n💾 数据库大小: {stats['db_size_mb']:.2f} MB")
        
        # 查询元数据表
        try:
            import sqlite3
            conn = db.conn
            cursor = conn.execute("""
                SELECT code, stock_name, market_type, last_update_date, data_count, last_success_at
                FROM meta_info
                ORDER BY last_success_at DESC
                LIMIT 20
            """)
            
            rows = cursor.fetchall()
            if rows:
                print("\n📋 最近更新的股票（前20只）:")
                print(f"{'代码':<12} {'名称':<20} {'市场':<8} {'最后更新':<20} {'数据量':<10}")
                print("-" * 80)
                for row in rows:
                    code = row[0] or ''
                    name = (row[1] or '')[:18] if row[1] else ''
                    market = row[2] or ''
                    update_date = row[3] or ''
                    count = row[4] or 0
                    print(f"{code:<12} {name:<20} {market:<8} {update_date:<20} {count:<10}")
        except Exception as e:
            print(f"\n⚠️  查询元数据失败: {e}")
        
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
