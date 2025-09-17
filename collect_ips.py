import re
import os
import aiohttp
import asyncio
import subprocess
from aiohttp import ClientSession

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

# 异步获取 IP 地址
async def fetch_ips_from_url(session: ClientSession, url: str):
    try:
        async with session.get(url, timeout=4) as response:
            if response.status == 200:
                html_content = await response.text()
                ip_matches = re.findall(ip_pattern, html_content, re.IGNORECASE)
                unique_ips.update(ip_matches)
    except Exception:
        pass

# 获取 IP 地址的异步任务
async def fetch_all_ips():
    async with ClientSession() as session:
        tasks = [fetch_ips_from_url(session, url) for url in urls]
        await asyncio.gather(*tasks)

# 使用异步方式获取 IP 地址
asyncio.run(fetch_all_ips())

# 定义一个函数来异步测试 IP 地址的延迟
async def ping_ip(ip: str) -> int:
    try:
        result = await asyncio.to_thread(subprocess.run, ['ping', '-c', '1', '-W', '2', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            time_ms = re.search(r'time=(\d+)', result.stdout)
            if time_ms:
                return int(time_ms.group(1))
        return None
    except Exception:
        return None

# 异步过滤 IP 地址
async def filter_ips_by_latency(ip: str):
    latency = await ping_ip(ip)
    if latency and 100 < latency < 400:
        return ip
    return None

# 并发化 ping 测试
async def filter_valid_ips():
    tasks = [filter_ips_by_latency(ip) for ip in unique_ips]
    valid_ips = await asyncio.gather(*tasks)
    return [ip for ip in valid_ips if ip is not None]

# 获取有效的 IP 地址
valid_ips = asyncio.run(filter_valid_ips())

# 将筛选后的 IP 地址写入文件
if valid_ips:
    with open('ip.txt', 'w') as file:
        file.write("\n".join(valid_ips) + "\n")
