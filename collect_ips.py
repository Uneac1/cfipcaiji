import requests
import re
import os
import subprocess
import time
import concurrent.futures

# 目标URL列表
urls = [
    'https://ip.164746.xyz', 
    'https://cf.090227.xyz', 
    'https://stock.hostmonit.com/CloudFlareYes',
    'https://www.wetest.vip/page/cloudflare/address_v4.html'
]

# 正则表达式用于匹配IP地址
ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'

# 检查ip.txt文件是否存在,如果存在则删除它
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

# 使用集合存储IP地址实现自动去重
unique_ips = set()

# 获取 IP 地址
def fetch_ips_from_url(url):
    try:
        # 发送HTTP请求获取网页内容
        response = requests.get(url, timeout=5)
        
        # 确保请求成功
        if response.status_code == 200:
            # 获取网页的文本内容
            html_content = response.text
            
            # 使用正则表达式查找IP地址
            ip_matches = re.findall(ip_pattern, html_content, re.IGNORECASE)
            
            # 将找到的IP添加到集合中（自动去重）
            unique_ips.update(ip_matches)
    except requests.exceptions.RequestException as e:
        print(f'请求 {url} 失败: {e}')

# 使用并发处理来获取 IP 地址
with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(fetch_ips_from_url, urls)

# 定义一个函数来测试 IP 地址的延迟
def ping_ip(ip):
    try:
        # 使用 subprocess 运行 ping 命令（-c 1 表示只发送一个请求）
        result = subprocess.run(['ping', '-c', '1', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 提取响应时间
        if result.returncode == 0:
            # 获取 ping 输出中的延迟时间（单位毫秒）
            time_ms = re.search(r'time=(\d+)', result.stdout)
            if time_ms:
                return int(time_ms.group(1))
        return None  # 如果没有响应，返回 None
    except Exception as e:
        print(f"无法ping {ip}: {e}")
        return None

# 并行化 ping 测试
def filter_ips_by_latency(ip):
    latency = ping_ip(ip)
    if latency and 100 < latency < 400:
        return ip
    return None

# 使用线程池并发处理 ping 测试
valid_ips = []
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = executor.map(filter_ips_by_latency, unique_ips)

# 过滤掉返回值为 None 的项
valid_ips = [ip for ip in results if ip is not None]

# 将筛选后的 IP 地址写入文件
if valid_ips:
    with open('ip.txt', 'w') as file:
        file.write("\n".join(valid_ips) + "\n")
    print(f'已保存 {len(valid_ips)} 个符合条件的IP地址到 ip.txt 文件。')
else:
    print('未找到符合条件的IP地址。')
