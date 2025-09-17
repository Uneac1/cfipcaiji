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

# 匹配IPv4地址的正则表达式
ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

# 删除旧的 ip.txt 文件
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

# 用集合存储IP地址，自动去重
unique_ips = set()

# 获取IP延迟（30秒内的平均延迟）
def get_ping_latency(ip: str, num_pings: int = 30) -> tuple[str, float]:
    latencies = []
    for _ in range(num_pings):
        try:
            start = time.time()
            requests.get(f"http://{ip}", timeout=5)
            latency = (time.time() - start) * 1000  # 毫秒
            latencies.append(round(latency, 3))
        except requests.RequestException:
            latencies.append(float('inf'))  # 请求失败返回无限延迟
    # 计算平均延迟
    avg_latency = sum(latencies) / len(latencies) if latencies else float('inf')
    return ip, avg_latency

# 从URLs抓取IP地址
def fetch_ips():
    for url in urls:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                ips = re.findall(ip_pattern, resp.text)
                unique_ips.update(ips)
        except requests.RequestException:
            continue

# 并发获取延迟并过滤掉高于18ms的IP
def fetch_valid_ip_delays() -> dict:
    ip_delays = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_ping_latency, ip): ip for ip in unique_ips}
        for future in futures:
            ip, latency = future.result()
            if latency <= 20:  # 过滤掉高于18ms的IP
                ip_delays[ip] = latency
    return ip_delays

# 主流程
fetch_ips()
ip_delays = fetch_valid_ip_delays()

# 写入文件，按延迟升序排序
if ip_delays:
    with open('ip.txt', 'w') as f:
        for ip, latency in sorted(ip_delays.items(), key=lambda x: x[1]):
            f.write(f'{ip} {latency}ms\n')
    print(f'已保存 {len(ip_delays)} 个延迟≤18ms的IP到 ip.txt')
else:
    print('未找到有效的IP地址')
