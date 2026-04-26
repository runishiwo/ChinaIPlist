import requests
from netaddr import IPNetwork, cidr_merge
from datetime import datetime, timedelta, timezone
import os

# ================= 配置区 =================
SOURCE_FILE = "data/sources.txt"
OUT_V4 = "cn_v4.txt"
OUT_V6 = "cn_v6.txt"
OUT_ALL = "cnip.txt"

# 获取北京时间 (UTC+8)
def get_beijing_time():
    tz_bj = timezone(timedelta(hours=8))
    return datetime.now(tz_bj).strftime("%Y-%m-%d %H:%M:%S")

def fetch_ips(url):
    """
    拉取远程 IP 列表并进行基础清洗
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (GitHubActions; ChinaIPList-Builder)'
        }
        print(f"正在拉取: {url}")
        r = requests.get(url, timeout=30, headers=headers)
        if r.status_code == 200:
            return r.text.splitlines()
        else:
            print(f"::warning ::状态码异常 [{r.status_code}]: {url}")
    except Exception as e:
        print(f"::error ::请求失败: {url} -> {e}")
    return []

def main():
    v4_set = set()
    v6_set = set()
    now_str = get_beijing_time()

    # 1. 读取源文件
    if not os.path.exists(SOURCE_FILE):
        # 如果文件不存在，尝试创建一个示例或报错
        print(f"::error ::找不到源文件: {SOURCE_FILE}")
        return

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    # 2. 循环拉取并解析
    for url in urls:
        lines = fetch_ips(url)
        count = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith(("#", ";", "//")):
                continue
            
            try:
                # 预处理行内注释
                clean_ip = line.split('#')[0].strip()
                net = IPNetwork(clean_ip)
                if net.version == 4:
                    v4_set.add(net)
                elif net.version == 6:
                    v6_set.add(net)
                count += 1
            except:
                continue
        print(f"  -> 成功解析 {count} 条")

    print(f"\n正在进行 0 误伤聚合 (原始总数: {len(v4_set) + len(v6_set)})...")

    # 3. 0 误伤逻辑合并 (netaddr 自动处理包含和连续段)
    v4_merged = cidr_merge(list(v4_set))
    v6_merged = cidr_merge(list(v6_set))

    # 4. 写入结果 (带时间戳注释)
    # --- 写入 IPv4 ---
    with open(OUT_V4, "w", encoding="utf-8") as f:
        f.write(f"# CN IPv4 List | Last Update: {now_str} (CST)\n")
        f.write("\n".join(str(i) for i in v4_merged) + "\n")

    # --- 写入 IPv6 ---
    with open(OUT_V6, "w", encoding="utf-8") as f:
        f.write(f"# CN IPv6 List | Last Update: {now_str} (CST)\n")
        f.write("\n".join(str(i) for i in v6_merged) + "\n")

    # --- 写入全量文件 (V4 + V6) ---
    with open(OUT_ALL, "w", encoding="utf-8") as f:
        f.write(f"# CN All IP List | Last Update: {now_str} (CST)\n")
        for i in v4_merged:
            f.write(str(i) + "\n")
        for i in v6_merged:
            f.write(str(i) + "\n")

    # 5. 打印统计摘要
    print("\n" + "="*40)
    print(f"运行时间: {now_str}")
    print(f"聚合后 IPv4 条数: {len(v4_merged)}")
    print(f"聚合后 IPv6 条数: {len(v6_merged)}")
    print(f"总计规则条数: {len(v4_merged) + len(v6_merged)}")
    print("="*40)
    print("::notice ::所有文件已成功生成并注入北京时间戳。")

if __name__ == "__main__":
    main()
