import requests
import re
import os
import subprocess
import time

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
        continue

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

# 测量每个 IP 的延迟并存储
ip_with_latency = []

for ip in unique_ips:
    print(f"正在 ping {ip}...")
    latency = ping_ip(ip)
    if latency is not None:
        ip_with_latency.append((ip, latency))

# 根据延迟时间升序排序（延迟低的排前）
sorted_ips_by_latency = sorted(ip_with_latency, key=lambda x: x[1])

# 只保留前 50 个延迟最低的 IP 地址
top_50_ips = sorted_ips_by_latency[:50]

# 将去重后的 IP 地址按延迟从低到高写入文件
if top_50_ips:
    with open('ip.txt', 'w') as file:
        for ip, latency in top_50_ips:
            file.write(f"{ip} - {latency}ms\n")
    print(f'已保存 {len(top_50_ips)} 个延迟最低的IP地址到 ip.txt 文件。')
else:
    print('未找到有效的IP地址。')
