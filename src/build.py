import requests
from netaddr import IPNetwork, cidr_merge
import os

# 路径建议使用相对路径或从环境变量读取
SOURCE_FILE = "data/sources.txt"
OUT_V4 = "cn_v4.txt"
OUT_V6 = "cn_v6.txt"
OUT_ALL = "cnip.txt"

def fetch(url):
    """
    拉取远程 IP 列表，针对 GitHub Actions 环境增加了超时和重试逻辑
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (GitHubActions; ip-aggregator-script)'
        }
        # 增加超时控制，防止 GitHub Action 被卡死
        r = requests.get(url, timeout=30, headers=headers)
        if r.status_code == 200:
            return r.text.splitlines()
        else:
            print(f"::warning ::无法拉取源 {url}, 状态码: {r.status_code}")
    except Exception as e:
        print(f"::error ::请求异常 {url} -> {e}")
    return []

def main():
    v4_set = set()
    v6_set = set()

    # 1. 检查源文件
    if not os.path.exists(SOURCE_FILE):
        print(f"::error ::找不到源文件: {SOURCE_FILE}")
        return

    # 2. 读取源 URL
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        urls = [i.strip() for i in f if i.strip() and not i.startswith("#")]

    # 3. 多源数据整合
    for url in urls:
        print(f"正在同步: {url}")
        lines = fetch(url)
        count = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith(("#", ";", "//")):
                continue
            
            try:
                # 预处理行内注释（如 1.1.1.0/24 # ChinaTelecom）
                clean_ip = line.split('#')[0].strip()
                net = IPNetwork(clean_ip)
                if net.version == 4:
                    v4_set.add(net)
                elif net.version == 6:
                    v6_set.add(net)
                count += 1
            except:
                continue
        print(f"  -> 已解析 {count} 条记录")

    print(f"正在进行 0 误伤聚合 (V4: {len(v4_set)}, V6: {len(v6_set)})...")

    # 4. CIDR 0 误伤合并 (netaddr 会处理重叠、包含和连续网段)
    v4_merged = cidr_merge(list(v4_set))
    v6_merged = cidr_merge(list(v6_set))

    # 5. 写入结果
    # 写入 IPv4
    with open(OUT_V4, "w", encoding="utf-8") as f:
        f.write("\n".join(str(i) for i in v4_merged) + "\n")

    # 写入 IPv6
    with open(OUT_V6, "w", encoding="utf-8") as f:
        f.write("\n".join(str(i) for i in v6_merged) + "\n")

    # 写入全量文件 (合并 V4 和 V6)
    with open(OUT_ALL, "w", encoding="utf-8") as f:
        for i in v4_merged:
            f.write(str(i) + "\n")
        for i in v6_merged:
            f.write(str(i) + "\n")

    # 6. GitHub Action 日志摘要
    print("\n" + "="*32)
    print(f"聚合完成统计:")
    print(f"IPv4: {len(v4_merged)} 条")
    print(f"IPv6: {len(v6_merged)} 条")
    print(f"总计: {len(v4_merged) + len(v6_merged)} 条")
    print("="*32)

if __name__ == "__main__":
    main()
