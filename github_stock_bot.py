#!/usr/bin/env python3
"""
股票分析报告生成器 - 主程序
提供命令行接口，调用各模块完成股票分析报告生成
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# 可选依赖检查
try:
    import akshare as ak
except Exception:
    ak = None

# 导入工具函数模块
# noqa: E402 - load_dotenv() 必须在导入前执行
from src.utils.code_normalizer import is_hk_stock, parse_stock_list  # noqa: E402
from src.utils.trading_hours import is_china_stock_market_open, is_hk_stock_market_open  # noqa: E402
from src.utils.gdrive_uploader import upload_to_gdrive  # noqa: E402
from src.notify.telegram import send_telegram_msg  # noqa: E402

# 导入报告生成模块
from src.report import process_multiple_stocks, create_zip_archive  # noqa: E402

# 导入配置管理模块
from src.config import Config  # noqa: E402

# 导入日志模块
from src.utils.logger import get_logger  # noqa: E402

# 初始化配置和日志
config = Config()
logger = get_logger(__name__)

# ==================== 主程序 ====================


def main(sector_input=None):
    """主程序

    Args:
        sector_input: 行业代码或名称（如 BK1031、光伏设备），可选
    """
    is_manual = "--mode" in sys.argv and "manual" in sys.argv
    target_stocks = config.stocks

    # 3. 如果不是手动点，而是 GitHub Actions 自动跑，则检查交易日状态
    if not is_manual:
        has_hk = any(is_hk_stock(code) for code in target_stocks)
        has_a = any(not is_hk_stock(code) for code in target_stocks)

        a_open = True
        hk_open = True

        if has_a:
            logger.info("🕒 正在检查 A 股交易日...")
            a_open = is_china_stock_market_open()
        if has_hk:
            logger.info("🕒 正在检查港股交易日...")
            hk_open = is_hk_stock_market_open()

        if not a_open and not hk_open:
            logger.info("☕ 今日为法定节假日或休市，跳过分析报告推送。")
            return

        # 过滤休市市场的股票
        filtered = []
        skipped = []
        for code in target_stocks:
            if is_hk_stock(code):
                if hk_open:
                    filtered.append(code)
                else:
                    skipped.append(code)
            else:
                if a_open:
                    filtered.append(code)
                else:
                    skipped.append(code)

        if skipped:
            logger.info(f"☕ 跳过休市市场股票: {', '.join(skipped)}")
        target_stocks = filtered

    # 3. 只有开盘或是手动触发，才会继续执行下面的逻辑...
    logger.info("🚀 市场已开盘或手动触发，开始分析任务...")
    logger.info("=" * 70)
    logger.info("📊 股票分析报告生成器 (增强版)")
    logger.info("数据来源: 新浪财经")
    logger.info("=" * 70)

    try:
        import matplotlib

        logger.info(f"✅ Matplotlib: {matplotlib.__version__}")
    except ImportError:
        logger.error("❌ 请安装matplotlib: pip install matplotlib")
        return

    required = ["requests", "pandas"]
    for lib in required:
        try:
            __import__(lib)
            logger.debug(f"✅ {lib}: 已安装")
        except ImportError:
            logger.error(f"❌ 请安装{lib}: pip install {lib}")
            return

    try:
        import numpy

        logger.debug(f"✅ numpy: {numpy.__version__}")
    except ImportError:
        logger.warning("⚠️  numpy未安装，某些功能可能受限，建议安装: pip install numpy")

    logger.info(f"\n🎯 目标股票列表: {target_stocks}")
    logger.info("🚀 开始自动化分析...\n")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    reports_base_dir = config.report_output_dir
    reports_dir = os.path.join(current_dir, reports_base_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(reports_dir, f"reports_{timestamp}")

    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"📁 创建报告文件夹: {output_dir}")
    except Exception as e:
        logger.error(f"❌ 无法创建报告文件夹: {e}", exc_info=True)
        return

    stocks_input = " ".join(target_stocks)
    successful_reports, failed_reports = process_multiple_stocks(stocks_input, output_dir, sector_input=sector_input)

    logger.info("\n" + "=" * 70)
    logger.info("📊 批量处理完成!")
    logger.info("=" * 70)

    if successful_reports:
        logger.info(f"✅ 成功生成 {len(successful_reports)} 个报告:")
        for code, name, path in successful_reports:
            logger.info(f"  - {name} ({code})")

    if failed_reports:
        logger.warning(f"❌ 失败 {len(failed_reports)} 个:")
        for code, name, reason in failed_reports:
            logger.warning(f"  - {name} ({code}): {reason}")

    # 上传到 Google Drive
    logger.info("📤 正在上传报告到 Google Drive...")
    upload_to_gdrive(output_dir)

    logger.info("\n" + "=" * 70)
    logger.info("📦 正在创建ZIP压缩包...")
    zip_file = create_zip_archive(output_dir)

    # 发送 Telegram 通知
    logger.info("\n📱 正在发送 Telegram 通知...")
    import glob

    pdf_files = sorted(glob.glob(os.path.join(output_dir, "*.pdf")))

    if pdf_files and os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        import requests

        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        success_count = 0

        # 发送开始通知
        send_telegram_msg(f"📊 开始生成股票分析报告\n\n共 {len(pdf_files)} 个报告")

        # 发送每个 PDF 文件
        for pdf_file in pdf_files:
            filename = os.path.basename(pdf_file)
            file_size_mb = os.path.getsize(pdf_file) / (1024 * 1024)

            if file_size_mb > 50:
                logger.warning(f"⚠️  跳过文件 {filename} (大小: {file_size_mb:.1f}MB，超过50MB限制)")
                continue

            try:
                with open(pdf_file, "rb") as f:
                    response = requests.post(
                        f"https://api.telegram.org/bot{token}/sendDocument",
                        data={"chat_id": chat_id},
                        files={"document": (filename, f, "application/pdf")},
                        timeout=30,
                    )
                    response.raise_for_status()
                    if response.json().get("ok"):
                        logger.info(f"✅ Telegram 发送成功: {filename}")
                        success_count += 1
                    else:
                        logger.error(f"❌ Telegram 发送失败: {filename}")
            except Exception as e:
                logger.error(f"❌ 发送 {filename} 到 Telegram 出错: {e}")

        # 发送完成通知
        if success_count > 0:
            send_telegram_msg(f"✅ 股票分析报告推送完成\n\n成功: {success_count}/{len(pdf_files)}")
    else:
        if not pdf_files:
            logger.warning("⚠️  未找到 PDF 文件，跳过 Telegram 发送")
        else:
            logger.warning("⚠️  Telegram 配置缺失，跳过发送")

    if zip_file:
        logger.info("\n🎉 所有任务完成!")
        logger.info(f"📁 报告文件夹: {output_dir}")
        logger.info(f"📦 ZIP压缩包: {zip_file}")
    else:
        logger.info(f"\n📁 报告保存在: {output_dir}")

    logger.info("\n👋 程序结束")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        import argparse

        parser = argparse.ArgumentParser()
        default_stocks = " ".join(config.stocks)
        parser.add_argument("--mode", choices=["manual", "telegram"], default="manual")
        parser.add_argument("--stocks", type=str, default=default_stocks)
        parser.add_argument("--sector", type=str, default=None, help="行业代码（如BK1031）或行业名称（如光伏设备）")
        parser.add_argument("--config", type=str, default=None, help="配置文件路径（可选）")
        args = parser.parse_args()

        # 如果指定了配置文件，重新加载配置
        if args.config:
            config = Config(config_path=args.config)

        if args.mode == "telegram":
            logger.warning("⚠️ Telegram模式需要配置环境变量")
        else:
            if args.stocks != default_stocks:
                target_stocks = parse_stock_list(args.stocks)
            else:
                target_stocks = config.stocks
            cfg = config.load()
            if "stocks" not in cfg:
                cfg["stocks"] = {}
            cfg["stocks"]["default"] = target_stocks
            config._config = cfg
            main(sector_input=args.sector)
    else:
        main()
