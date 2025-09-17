import requests
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor

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

# 用来存储IP地址和它们对应的延迟
ip_delays = {}

# 获取每个IP地址的延迟，单位为毫秒，并保留三位小数
def get_ping_latency(ip):
    try:
        start_time = time.time()
        response = requests.get(f"http://{ip}", timeout=5)
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # 转换为毫秒
        return ip, round(latency, 3)  # 保留三位小数
    except requests.exceptions.RequestException:
        return ip, float('inf')  # 如果请求失败，返回一个很大的延迟

# 使用线程池来并发获取IP地址和测量延迟
def fetch_ips_and_latency():
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {executor.submit(get_ping_latency, ip): ip for ip in unique_ips}
        for future in future_to_ip:
            ip, latency = future.result()
            if latency <= 400:  # 如果延迟低于400ms
                ip_delays[ip] = latency

# 获取IP地址列表
def get_ip_addresses_from_urls():
    for url in urls:
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

# 主程序流程
get_ip_addresses_from_urls()
fetch_ips_and_latency()

# 将IP和延迟（单位：毫秒）写入文件
if ip_delays:
    with open('ip.txt', 'w') as file:
        for ip, latency in ip_delays.items():
            file.write(f'{ip} {latency}ms\n')  # 延迟单位为毫秒，保留三位小数
    print(f'已保存 {len(ip_delays)} 个IP和延迟到ip.txt文件。')
else:
    print('未找到有效的IP地址。')
