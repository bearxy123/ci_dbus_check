#!/usr/bin/env python3 

import argparse
import os
import sys
import utils
import json
import requests

from c_check import c_checker
from go_check import go_checker
from cpp_check import cpp_checker
from log_module import info_log, error_log
from collections import namedtuple

CommitInfo = namedtuple('CommitInfo', ['repo_name', 'branch', 'committer', 'commit_event', 'commit_hash', 'commit_event_id', 'jenkins_url', 'email'])

def send_webhook_request(data, commit_info):
    """
    发送POST请求到指定的webhook地址。

    :param url: webhook地址
    :param data: 要发送的数据结构体
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    url = "https://cooperation.uniontech.com/api/workflow/hooks/NjZjNTg4YzUwYjEwOTIwMDc0MGZlMWQ0"  # 替换为你的webhook地址

    send_data = {
        'project_name': data['project_path'],
        'dbus_count': data['dbus_method_count'],
        'unsafe_count': data['unsafe_call_count'],
        'scan_result': data['scan_result'],
        'details': data['details'],
        'repo_name': commit_info["repo_name"],
        'branch': commit_info["branch"],
        'committer': commit_info["committer"],
        'commit_event': commit_info["commit_event"],
        'commit_hash': commit_info["commit_hash"],
        'commit_event_id': commit_info["commit_event_id"],
        'jenkins_url':commit_info['jenkins_url'],
        'email':commit_info['email']
    }

    try:
        response = requests.post(url, data=json.dumps(send_data), headers=headers)
        response.raise_for_status()  # 如果响应状态码不是200，抛出HTTPError异常
        return response.json()  # 返回响应的JSON数据
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def main():

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='D-Bus 检查.')
    parser.add_argument('--source_directory', type=str, help='源码路径')
    parser.add_argument('--commit_info_str', type=str, help='提交参数')
    
    args = parser.parse_args()
    
    # 获取源码路径
    source_directory = args.source_directory
    commit_info_str = args.commit_info_str
    # DEBUG Info
    # print(type(commit_info_str))
    # print("commit_info_str is ", commit_info_str)
    commit_info = json.loads(commit_info_str)
    
    # 检查源码路径是否存在
    if not os.path.exists(source_directory):
        error_log(f"Error: The directory '{source_directory}' does not exist.")
        sys.exit(1)
    
    language_check_functions = {
        'c': c_checker.check_dbus_in_c,
        'cpp': cpp_checker.check_dbus_in_cpp,
        'go': go_checker.check_dbus_in_go
    }

    # 检测语言类型
    try:
        info_log(f"开始检测...")
        language = utils.detect_language(source_directory)
        info_log(f"检测到项目语言类型为: {language}")
    except Exception as e:
        error_log(f"Error: 语言检测失败: {e}")
        sys.exit(1)
    
    # 根据语言类型调用相应的检查函数
    check_function = language_check_functions.get(language)
    if check_function is None:
        error_log(f"Error: 不支持的语言类型 '{language}'.")
        sys.exit(1)
    
    try:
        results, data = check_function(source_directory)

        result_sum = {
            'dbus_method_count': data['dbus_method_count'],
            'unsafe_call_count': data['unsafe_call_count'],
            'scan_result': data['scan_result']
        }

        if os.path.exists('result.json'):
        # 如果文件存在，删除文件
            os.remove('result.json')

        with open('result.json', 'w') as f:
            f.write(json.dumps(result_sum))

        if results == True:
            info_log(f"{data}")
            info_log(commit_info["repo_name"])

            info_log(f"{language.capitalize()} D-Bus 检查完成！")

            response_data = send_webhook_request(data, commit_info)
            if response_data:
                print(f"请求成功，响应数据: {response_data}")
            else:
                print("请求失败")

        else:
            info_log(f"{language.capitalize()} D-Bus 检查异常！")
            sys.exit(1)

    except Exception as e:
        error_log(f"Error: 检查过程出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
