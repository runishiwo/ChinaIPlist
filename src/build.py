import requests
from netaddr import IPNetwork, cidr_merge

SOURCE_FILE = "data/sources.txt"

OUT_V4 = "cn_v4.txt"
OUT_V6 = "cn_v6.txt"
OUT_ALL = "cnip.txt"


def fetch(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.text.splitlines()
    except Exception as e:
        print("fetch error:", url, e)
    return []


def main():
    v4_list = []
    v6_list = []

    # 读取所有源
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        urls = [i.strip() for i in f if i.strip()]

    # 拉取并解析
    for url in urls:
        print("fetch:", url)
        lines = fetch(url)

        for line in lines:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            try:
                net = IPNetwork(line)

                if net.version == 4:
                    v4_list.append(net)
                elif net.version == 6:
                    v6_list.append(net)

            except:
                continue

    # =========================
    # CIDR 合并压缩
    # =========================
    v4_merged = cidr_merge(v4_list)
    v6_merged = cidr_merge(v6_list)

    # 全量合并（V4 + V6）
    all_merged = cidr_merge(v4_list + v6_list)

    # =========================
    # 输出文件（根目录）
    # =========================
    with open(OUT_V4, "w", encoding="utf-8") as f:
        f.write("\n".join(str(i) for i in v4_merged))

    with open(OUT_V6, "w", encoding="utf-8") as f:
        f.write("\n".join(str(i) for i in v6_merged))

    with open(OUT_ALL, "w", encoding="utf-8") as f:
        f.write("\n".join(str(i) for i in all_merged))

    # =========================
    # 日志输出
    # =========================
    print("================================")
    print("V4 :", len(v4_merged))
    print("V6 :", len(v6_merged))
    print("ALL:", len(all_merged))
    print("================================")


if __name__ == "__main__":
    main()
