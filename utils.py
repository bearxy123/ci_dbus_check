#!/usr/bin/env python3 
import re
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from log_module import info_log, error_log

# 定义项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# 定义各子目录路径
GO_CHECK_DIR = os.path.join(PROJECT_ROOT, 'go_check')
C_CHECKER_DIR = os.path.join(PROJECT_ROOT, 'c_check')
CPP_CHECKER_DIR = os.path.join(PROJECT_ROOT, 'cpp_check')

# 定义CPP中的dbus方法文件路径
XML_PATH = PROJECT_ROOT + '/cpp_check/cpp_dbus_xml'
# 定义不安全函数的配置文件路径
CPP_UNSAFE_CONF_PATH = os.path.join(PROJECT_ROOT, 'cpp_check/cpp_unsafe_functions.conf')
C_UNSAFE_CONF_PATH = os.path.join(PROJECT_ROOT, 'c_check/c_unsafe_functions.conf')

# 定义go文件的位置
GO_FILE_PATH = os.path.join(GO_CHECK_DIR, 'dbus_method_check.go')

# 文件查找和遍历，需要写一个通用函数 --todo
def find_functions_in_file(file_path, pattern):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
    return re.findall(pattern, content)

# 解析xml文件生成字典的函数  --todo
def parse_dbus_xml(XML_PATH):
    excluded_interfaces = {
        "org.freedesktop.DBus.Peer",
        "org.freedesktop.DBus.Introspectable",
        "org.freedesktop.DBus.Properties"
    }

    interface_methods = {}

    for filename in os.listdir(XML_PATH):
        if filename.endswith('.xml'):
            file_path = os.path.join(XML_PATH, filename)
            tree = ET.parse(file_path)
            root = tree.getroot()

            for interface in root.findall('interface'):
                interface_name = interface.get('name')
                if interface_name not in excluded_interfaces:
                    methods = [method.get('name') for method in interface.findall('method')]
                    if methods:
                        if interface_name in interface_methods:
                            interface_methods[interface_name].extend(methods)
                        else:
                            interface_methods[interface_name] = methods

    return interface_methods

# 写一个函数判断源码目录中使用的编程语言c还是go还是c++,返回值为'c'或'go'或'cpp'，如果都不是，则返回'unknown'
def detect_language(source_dir):
    c_extensions = {'.c', '.h'}
    cpp_extensions = {'.cpp', '.hpp', '.cxx', '.hxx', '.cc', '.hh'}
    go_extensions = {'.go'}

    c_files = set()
    cpp_files = set()
    go_files = set()

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_ext = os.path.splitext(file)[1]
            if file_ext in c_extensions:
                c_files.add(file_ext)
            elif file_ext in cpp_extensions:
                cpp_files.add(file_ext)
            elif file_ext in go_extensions:
                go_files.add(file_ext)

    if go_files:
        return 'go'
    elif cpp_files:
        return 'cpp'
    elif c_files:
        return 'c'
    else:
        return 'unknown'


def check_and_install():
    system_packages = ['clang-7', 'libclang-dev', 'llvm-7', 'python3-pip', 'golang']
    python_modules = ['clang']
    all_installed = True  # 标记所有包和模块是否成功安装

    # 检查和安装系统包
    for package in system_packages:
        try:
            # 检查包是否已安装
            subprocess.check_call(['sudo', 'dpkg', '-s', package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # print(f'{package} 已安装')
        except subprocess.CalledProcessError:
            # 如果包未安装，则安装
            info_log(f'{package} 未安装，正在安装...')
            try:
                subprocess.check_call(['sudo', 'apt-get', 'install', '-y', package])
            except subprocess.CalledProcessError as e:
                error_log(f'安装 {package} 时出错: {e}')
                all_installed = False

    # 检查和安装Python模块
    for module in python_modules:
        try:
            __import__(module)
            # print(f'Python模块 {module} 已安装')
        except ImportError:
            info_log(f'Python模块 {module} 未安装，正在安装...')
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', module])
            except subprocess.CalledProcessError as e:
                error_log(f'安装 Python 模块 {module} 时出错: {e}')
                all_installed = False

    if all_installed:
        return True
    else:
        return False

def load_list_from_text(file_path):
    """
    从纯文本配置文件中读取每行作为列表元素。

    :param file_path: 配置文件路径
    :return: 列表数据，如果文件读取错误则返回空列表
    """
    try:
        with open(file_path, 'r') as file:
            # 读取每行并去除首尾空白字符，然后返回作为列表
            return [line.strip() for line in file if line.strip()]
    except IOError as e:
        print(f"读取纯文本配置文件时发生错误: {e}")
        return []

