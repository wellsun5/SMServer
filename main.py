import re
import socket
#import json
import os
import sys
import logging
import argparse
import pyperclip
from winotify import Notification, audio

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def receive_message(port):
    # 创建socket对象
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 允许地址重用
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)
        logging.info(f"服务器正在监听端口：{port}...")
    except Exception as e:
        logging.error(f"绑定和监听端口失败： {port}: {e}")
        return

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            logging.info(f"有连接来自：{client_address}")
            client_socket.sendall("连接成功".encode('utf-8'))

            data = client_socket.recv(1024)
            if not data:
                logging.warning("没收到数据，关闭连接。")
                client_socket.close()
                continue

            text = data.decode('utf-8')
            text = text.strip()
            logging.info(f"收到的数据是：{text}")
            #print (text)
            # 如果数据是以大括号包围的，去掉首尾的大括号
            if text.startswith('{') and text.endswith('}'):
                text = text[1:-1]
            text = text.strip().replace('\\n', '\n')
            # 正则表达式匹配\n前面的部分
            match = split_string_at_first_slash(text)

            if match:
                prefix, suffix = match  # 提取应用包名
                if prefix == 'com.android.incallui':
                    show_toast(suffix)#来电
                elif prefix == 'com.zwfw.YueZhengYi':
                    show_toast(suffix)
                elif prefix == 'test':
                    show_toast(suffix)#测试
                elif prefix == 'com.android.mms':#短信
                    copy_verification_code(suffix)
                else:
                    logging.info(f"其他应用的消息：{suffix}")
                    #print(suffix)
            else:
                logging.error("分割处理失败！")

            client_socket.close()
            logging.info(f"来自{client_address} 的连接已关闭")
            print ("\n\n")
        except Exception as e:
            logging.error(f"处理客户端连接失败：{e}")
            continue


def split_string_at_first_slash(text):
    """
    分割字符串，以第一个"\n"为界限。
    Args:
        text: 输入字符串。
    Returns:
        一个包含两个子字符串的元组，或者 None 如果字符串中没有"\n"。
    """
    if "\n" not in text:
        return None  # 或者抛出异常，取决于你的需求

    index = text.find("\n")
    before_slash = text[:index]
    after_slash = text[index + 1:]
    return before_slash, after_slash


def get_config_path():
    # 当运行的是打包后的.exe文件时
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'config.json')  # Path to the extracted config.json
    else:
        return os.path.join(os.path.dirname(__file__), 'config.json')  # Normal script execution


def parse_args():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Start the server and listen on a specified port.")
    parser.add_argument('-p', '--port', type=int, help="Port to listen on", default=None)
    return parser.parse_args()


def main():
    # 解析命令行参数
    args = parse_args()

    # 如果命令行参数中有端口，优先使用命令行端口
    if args.port:
        port = args.port
        logging.info(f"从命令行参数获取使用端口： {port} ")
    else:
        port=65432
        """ # 如果没有传递端口参数，读取配置文件中的端口
        try:
            config_path = get_config_path()
            with open(config_path, 'r') as file:
                config = json.load(file)

            port = config['port']
            logging.info(f"Using port {port} from config file.")
        except FileNotFoundError:
            logging.error("Configuration file 'config.json' not found.")
            return
        except json.JSONDecodeError:
            logging.error("Error decoding the configuration file.")
            return
        except KeyError:
            logging.error("Missing 'port' key in the configuration file.")
            return
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return """

    receive_message(port)

def extract_code(text):
    # 匹配长度等于6的数字字符串
    pattern = r'验证码[\s\S]{0,2}(\d{4}|\d{6})'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def get_icon_path():
    # When running from a packaged .exe
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'favicon.ico')
    else:
        return os.path.join(os.path.dirname(__file__), 'favicon.ico')


def show_toast(title, message=""):
    try:
        # 获取图标路径
        icon_path = get_icon_path()
        if not os.path.exists(icon_path):
            icon_path = ""  # 如果图标不存在则使用默认图标

        # 创建通知
        toast = Notification(
            app_id="SMS server",  # 应用标识名称
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

def copy_verification_code(suffix):
    number = extract_code(suffix)
    if number:
        # 复制到剪贴板
        pyperclip.copy(number)
        logging.info(f"已复制到剪贴板: {number}")

        # 显示通知
        show_toast(
            f"验证码: {number} 复制成功",
            f"短信原文: {suffix}"
        )
        return number
    else:
        logging.warning("未找到符合条件的验证码")
        show_toast("验证码提取失败", f"原短信为：{suffix}")
        return None

if __name__ == "__main__":
    main()
