import requests
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess

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

# 获取IP延迟（通过 ping 命令，5次ping，每次间隔1秒，计算平均延迟）
def get_ping_latency(ip: str, num_pings: int = 9, interval: int = 1) -> tuple[str, float]:
    try:
        # 执行 ping 命令
        result = subprocess.run(
            ["ping", "-c", str(num_pings), "-i", str(interval), ip],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            # 提取 ping 命令输出中的延迟
            lines = result.stdout.splitlines()
            latencies = [float(re.search(r'time=(\d+\.\d+)', line).group(1)) for line in lines if "time=" in line]
            avg_latency = sum(latencies) / len(latencies) if latencies else float('inf')
            return ip, avg_latency
        else:
            return ip, float('inf')
    except subprocess.TimeoutExpired:
        return ip, float('inf')
    except Exception as e:
        print(f"Error while pinging {ip}: {e}")
        return ip, float('inf')

# 从URLs抓取IP地址，避免无效请求并提高异常处理
def fetch_ips():
    for url in urls:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                ips = re.findall(ip_pattern, resp.text)
                unique_ips.update(ips)
        except requests.RequestException as e:
            print(f"警告: 获取IP失败，URL: {url}, 错误: {e}")

# 并发获取延迟
def fetch_ip_delays() -> dict:
    ip_delays = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_ping_latency, ip): ip for ip in unique_ips}
        for future in as_completed(futures):  # 使用as_completed更高效
            ip, latency = future.result()
            ip_delays[ip] = latency  # 保存所有IP的延迟
    return ip_delays

# 主流程
fetch_ips()
ip_delays = fetch_ip_delays()

# 只保存延迟最低的前20个IP地址
if ip_delays:
    top_ips = sorted(ip_delays.items(), key=lambda x: x[1])[:5]  # 按延迟升序排列并选择前20个
    
    # 写入文件
    with open('ip.txt', 'w') as f:
        for ip, latency in top_ips:
            f.write(f'{ip} {latency}ms\n')
    print(f'已保存 {len(top_ips)} 个IP到 ip.txt')
else:
    print('未找到有效的IP地址')
