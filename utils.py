import re
import sys
import os
import pyperclip
from winotify import Notification, audio
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def extract_first_long_number(text):
    # 匹配长度大于等于4的数字字符串
    pattern = r'\d{4,}'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return None


def get_icon_path():
    # When running from a packaged .exe
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'favicon.ico')
    else:
        return os.path.join(os.path.dirname(__file__), 'favicon.ico')


def show_toast_notification(title, message):
    try:
        # 获取图标路径
        icon_path = get_icon_path()
        if not os.path.exists(icon_path):
            icon_path = ""  # 如果图标不存在则使用默认图标

        # 创建通知
        toast = Notification(
            app_id="SMSOTPServer",  # 应用标识名称
            title=title,
            msg=message,
            icon=icon_path,
            duration="long"  # short约为4.5秒，long约为9秒
        )

        # 设置通知声音
        toast.set_audio(audio.Default, loop=False)

        # 显示通知
        toast.show()

    except Exception as e:
        logging.error(f"通知显示失败: {str(e)}")


def caller_handler(text):
    # 显示通知
    show_toast_notification(
        f"联系电话: {text} 来了",
        f"原文: {text}"
    )


def copy_verification_code(text):
    number = extract_first_long_number(text)
    if number:
        # 复制到剪贴板
        pyperclip.copy(number)
        logging.info(f"已复制到剪贴板: {number}")

        # 处理文本，确保索引访问安全
        display_text = text
        if text.startswith('{') and text.endswith('}'):
            display_text = text[1:-1]

        # 显示通知
        show_toast_notification(
            f"验证码: {number} 复制成功",
            f"短信原文: {display_text}"
        )
        return number
    else:
        logging.warning("未找到符合条件的数字字符串")
        show_toast_notification("复制失败", "请检查短信验证码")
        return None


if __name__ == "__main__":
    test_text = "{这是一段包含验证码737363的测试文本}"
    copy_verification_code(test_text)
