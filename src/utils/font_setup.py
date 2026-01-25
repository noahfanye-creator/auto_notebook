"""
字体设置模块
适配macOS/Linux环境的中文字体配置
"""

import os
import sys
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def setup_fonts() -> str:
    """
    设置字体（适配macOS/Linux环境）

    Returns:
        str: 可用的字体名称
    """
    print("📱 系统字体配置...")

    font_name = "Helvetica"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取项目根目录（向上两级）
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

    # 优先使用项目内置中文字体
    local_font = os.path.join(project_root, "SimHei.ttf")
    if os.path.exists(local_font):
        try:
            pdfmetrics.registerFont(TTFont("SimHeiLocal", local_font))
            font_name = "SimHeiLocal"
            print("✅ 使用本地字体: SimHei.ttf")
            return font_name
        except Exception as e:
            print(f"⚠️  本地字体注册失败: {e}")

    # macOS字体
    if sys.platform == "darwin":
        mac_fonts = [
            ("/System/Library/Fonts/PingFang.ttc", "PingFang"),
            ("/System/Library/Fonts/STHeiti Light.ttc", "STHeiti"),
            ("/System/Library/Fonts/Hiragino Sans GB.ttc", "Hiragino"),
            ("/Library/Fonts/Arial Unicode.ttf", "ArialUnicode"),
        ]
        for font_path, font_alias in mac_fonts:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_alias, font_path))
                    font_name = font_alias
                    print(f"✅ 成功注册字体: {font_alias}")
                    return font_name
                except Exception as e:
                    print(f"⚠️  字体注册失败 {font_alias}: {e}")

    # Linux字体
    linux_fonts = [
        ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "WenQuanYiZenHei"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans"),
    ]
    for font_path, font_alias in linux_fonts:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_alias, font_path))
                font_name = font_alias
                print(f"✅ 成功注册字体: {font_alias}")
                return font_name
            except Exception as e:
                print(f"⚠️  字体注册失败 {font_alias}: {e}")

    # 兜底CID字体
    try:
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont

        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        font_name = "STSong-Light"
        print("✅ 使用STSong-Light CID字体")
    except:
        print("⚠️  所有中文字体尝试失败,使用默认Helvetica")

    return font_name
