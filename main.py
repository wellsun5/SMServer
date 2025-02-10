import re
import socket
import json
import os
import sys
import logging
import argparse
import utils

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
        logging.info(f"Server is listening on port {port}...")
    except Exception as e:
        logging.error(f"Failed to bind or listen on port {port}: {e}")
        return

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            logging.info(f"Connection from {client_address}")

            data = client_socket.recv(1024)
            if not data:
                logging.warning("No data received, closing connection.")
                client_socket.close()
                continue

            text = data.decode('utf-8')
            logging.info(f"Received data: {text}")
            # 如果数据是以大括号包围的，去掉首尾的大括号
            text = text.strip()
            if text.startswith('{') and text.endswith('}'):
                text = text[1:-1]
                logging.info(f"text data: {text}")
            # 正则表达式匹配 . 前面的部分
            match = split_string_at_first_dot(text)

            if match:
                prefix, suffix = match  # 提取 . 前的部分
                if prefix == 'CALL':
                    # 处理 CALL 的情况
                    utils.caller_handler(suffix)
                elif prefix == 'SMS':
                    # 处理 SMS 的情况
                    # 调用外部函数来处理验证码
                    utils.copy_verification_code(suffix)
                else:
                    logging.warning(f"处理其他类型: {prefix}")
            else:
                logging.error("无法匹配到预期格式")

            client_socket.close()
        except Exception as e:
            logging.error(f"Error handling client connection: {e}")
            continue


def split_string_at_first_dot(text):
    """
    分割字符串，以第一个"."为界限。

    Args:
        text: 输入字符串。

    Returns:
        一个包含两个子字符串的元组，或者 None 如果字符串中没有"."。
    """
    if "." not in text:
        return None  # 或者抛出异常，取决于你的需求

    index = text.find(".")
    before_dot = text[:index]
    after_dot = text[index + 1:]
    return before_dot, after_dot


def get_config_path():
    # When running from a packaged .exe
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
        logging.info(f"Using port {port} from command line argument.")
    else:
        # 如果没有传递端口参数，读取配置文件中的端口
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
            return

    receive_message(port)


if __name__ == "__main__":
    main()
