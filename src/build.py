import requests
from netaddr import IPNetwork, cidr_merge
import os

SOURCE_FILE = "data/sources.txt"

OUT_V4 = "cn_v4.txt"
OUT_V6 = "cn_v6.txt"
OUT_ALL = "cnip.txt"

def fetch(url):
    try:
        # 增加 User-Agent 模拟浏览器，防止部分源屏蔽 Python 爬虫
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, timeout=20, headers=headers)
        if r.status_code == 200:
            return r.text.splitlines()
    except Exception as e:
        print(f"fetch error: {url} -> {e}")
    return []

def main():
    # 使用 set 自动处理初始去重，减少内存占用并加速后续合并
    v4_set = set()
    v6_set = set()

    if not os.path.exists(SOURCE_FILE):
        print(f"错误: 找不到源文件 {SOURCE_FILE}")
        return

    # 读取所有源
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        urls = [i.strip() for i in f if i.strip() and not i.startswith("#")]

    # 拉取并解析
    for url in urls:
        print(f"正在拉取: {url}")
        lines = fetch(url)

        for line in lines:
            line = line.strip()
            # 过滤掉注释、空行以及包含特殊字符的行
            if not line or line.startswith("#") or line.startswith(";"):
                continue

            try:
                # 预处理可能带有的空格或引号
                clean_line = line.split('#')[0].strip() 
                net = IPNetwork(clean_line)

                if net.version == 4:
                    v4_set.add(net)
                elif net.version == 6:
                    v6_set.add(net)
            except:
                continue

    print("数据拉取完成，开始 0 误伤聚合...")

    # =========================
    # CIDR 合并压缩 (绝对精确)
    # =========================
    # cidr_merge 会自动处理包含关系（如 1.0.0.0/8 包含 1.1.1.0/24）和相邻关系
    v4_merged = cidr_merge(list(v4_set))
    v6_merged = cidr_merge(list(v6_set))

    # =========================
    # 输出文件
    # =========================
    # 写入 IPv4
    with open(OUT_V4, "w", encoding="utf-8") as f:
        f.write("\n".join(str(i) for i in v4_merged))

    # 写入 IPv6
    with open(OUT_V6, "w", encoding="utf-8") as f:
        f.write("\n".join(str(i) for i in v6_merged))

    # 写入全量 (V4 + V6)
    with open(OUT_ALL, "w", encoding="utf-8") as f:
        # 直接连接两个已合并的列表即可，不需要再次进行 cidr_merge 
        # 因为 V4 和 V6 永远不可能互相合并
        f.write("\n".join(str(i) for i in v4_merged))
        f.write("\n")
        f.write("\n".join(str(i) for i in v6_merged))

    # =========================
    # 日志输出
    # =========================
    print("================================")
    print(f"聚合后 IPv4 条数: {len(v4_merged)}")
    print(f"聚合后 IPv6 条数: {len(v6_merged)}")
    print(f"总计条数: {len(v4_merged) + len(v6_merged)}")
    print(f"结果已保存至: {OUT_V4}, {OUT_V6}, {OUT_ALL}")
    print("================================")

if __name__ == "__main__":
    main()
