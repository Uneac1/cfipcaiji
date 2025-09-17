import re
import os
import requests
import subprocess

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

# 同步获取 IP 地址
def fetch_ips_from_url(url):
    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            html_content = response.text
            ip_matches = re.findall(ip_pattern, html_content, re.IGNORECASE)
            unique_ips.update(ip_matches)
    except Exception:
        pass

# 获取所有 IP 地址
for url in urls:
    fetch_ips_from_url(url)

# 定义一个函数来同步测试 IP 地址的延迟
def ping_ip(ip):
    try:
        result = subprocess.run(['ping', '-c', '1', '-W', '2', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            time_ms = re.search(r'time=(\d+)', result.stdout)
            if time_ms:
                return int(time_ms.group(1))
        return None
    except Exception:
        return None

# 同步过滤 IP 地址
def filter_ips_by_latency(ip):
    latency = ping_ip(ip)
    if latency and 100 < latency < 400:
        return ip
    return None

# 过滤有效的 IP 地址
valid_ips = [ip for ip in unique_ips if filter_ips_by_latency(ip)]

# 将筛选后的 IP 地址写入文件
if valid_ips:
    with open('ip.txt', 'w') as file:
        file.write("\n".join(valid_ips) + "\n")
