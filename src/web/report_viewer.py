#!/usr/bin/env python3
"""
股票分析报告 Web 查看器
提供 Web 界面浏览和下载生成的 PDF 报告
"""

import os
import glob
from datetime import datetime
from flask import Flask, render_template, send_file, jsonify
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = Flask(__name__)

# 报告目录（相对于项目根目录）
REPORTS_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")


def get_reports():
    """
    扫描 reports 目录，获取所有 PDF 报告
    返回按时间倒序排列的报告列表
    """
    reports = []

    if not os.path.exists(REPORTS_BASE_DIR):
        logger.warning(f"报告目录不存在: {REPORTS_BASE_DIR}")
        return reports

    # 扫描所有子目录中的 PDF 文件
    for pdf_path in glob.glob(os.path.join(REPORTS_BASE_DIR, "**/*.pdf"), recursive=True):
        try:
            stat = os.stat(pdf_path)
            file_size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime)

            # 从文件名提取信息（格式：股票名称_股票代码_时间戳.pdf）
            filename = os.path.basename(pdf_path)
            name_parts = filename.replace(".pdf", "").split("_")

            stock_name = name_parts[0] if len(name_parts) > 0 else "未知"
            stock_code = name_parts[1] if len(name_parts) > 1 else "未知"
            timestamp = "_".join(name_parts[2:]) if len(name_parts) > 2 else ""

            # 相对路径（用于下载）
            rel_path = os.path.relpath(pdf_path, REPORTS_BASE_DIR)

            reports.append(
                {
                    "filename": filename,
                    "path": rel_path,
                    "full_path": pdf_path,
                    "stock_name": stock_name,
                    "stock_code": stock_code,
                    "timestamp": timestamp,
                    "size": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "mtime": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    "mtime_obj": mtime,
                }
            )
        except Exception as e:
            logger.error(f"处理文件失败 {pdf_path}: {e}")

    # 按修改时间倒序排列（最新的在前）
    reports.sort(key=lambda x: x["mtime_obj"], reverse=True)

    return reports


@app.route("/")
def index():
    """主页：显示报告列表"""
    reports = get_reports()

    # 统计信息
    total_reports = len(reports)
    total_size = sum(r["size"] for r in reports)
    total_size_mb = round(total_size / (1024 * 1024), 2)

    # 按股票代码分组统计
    stock_stats = {}
    for report in reports:
        code = report["stock_code"]
        if code not in stock_stats:
            stock_stats[code] = {"count": 0, "name": report["stock_name"]}
        stock_stats[code]["count"] += 1

    return render_template(
        "reports.html",
        reports=reports,
        total_reports=total_reports,
        total_size_mb=total_size_mb,
        stock_stats=stock_stats,
    )


@app.route("/api/reports")
def api_reports():
    """API：返回报告列表 JSON"""
    reports = get_reports()
    # 移除 full_path 和 mtime_obj（不可序列化）
    for r in reports:
        r.pop("full_path", None)
        r.pop("mtime_obj", None)
    return jsonify(reports)


@app.route("/download/<path:filepath>")
def download(filepath):
    """下载报告文件"""
    full_path = os.path.join(REPORTS_BASE_DIR, filepath)

    # 安全检查：确保文件在 reports 目录内
    if not os.path.abspath(full_path).startswith(os.path.abspath(REPORTS_BASE_DIR)):
        return "禁止访问", 403

    if not os.path.exists(full_path):
        return "文件不存在", 404

    return send_file(full_path, as_attachment=True, download_name=os.path.basename(filepath))


@app.route("/view/<path:filepath>")
def view(filepath):
    """在线查看报告（返回 PDF 文件供浏览器预览）"""
    full_path = os.path.join(REPORTS_BASE_DIR, filepath)

    # 安全检查
    if not os.path.abspath(full_path).startswith(os.path.abspath(REPORTS_BASE_DIR)):
        return "禁止访问", 403

    if not os.path.exists(full_path):
        return "文件不存在", 404

    return send_file(full_path, mimetype="application/pdf")


@app.route("/health")
def health():
    """健康检查端点"""
    return jsonify({"status": "ok", "reports_dir": REPORTS_BASE_DIR})


if __name__ == "__main__":
    # 开发模式
    app.run(host="127.0.0.1", port=5000, debug=False)
