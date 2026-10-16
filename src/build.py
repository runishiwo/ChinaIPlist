import ipaddress
import os
import sys
from datetime import datetime, timedelta, timezone

import requests
from netaddr import IPNetwork, cidr_merge, AddrFormatError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ================= 配置区 =================
SOURCE_FILE = "data/sources.txt"
OUT_V4 = "cn_v4.txt"
OUT_V6 = "cn_v6.txt"
OUT_ALL = "cnip.txt"

# ---- 防呆阈值 ----
# 聚合后条数低于该值视为异常，直接中止构建（不写文件、不提交，保留线上旧列表）
MIN_V4_COUNT = 6000
MIN_V6_COUNT = 1000
# 与仓库中已有结果相比，允许的最大缩水比例（0.05 = 5%）
MAX_SHRINK_RATIO = 0.05

# 获取北京时间 (UTC+8)
def get_beijing_time():
    tz_bj = timezone(timedelta(hours=8))
    return datetime.now(tz_bj).strftime("%Y-%m-%d %H:%M:%S")

def build_session():
    """带自动重试的 requests Session，缓解单源网络抖动"""
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (GitHubActions; ChinaIPList-Builder)"
    })
    return session

def fetch_ips(session, url):
    """
    拉取远程 IP 列表。
    成功返回行列表；拉取失败返回 None（与"拉到空内容"区分，便于统计失败源）
    """
    try:
        print(f"正在拉取: {url}")
        r = session.get(url, timeout=(10, 30))
        if r.status_code == 200:
            return r.text.splitlines()
        print(f"::warning ::状态码异常 [{r.status_code}]: {url}")
    except Exception as e:
        print(f"::error ::请求失败: {url} -> {e}")
    return None

def parse_cidr(text):
    """
    解析单行 CIDR，返回规范网段的 netaddr IPNetwork；无法解析返回 None。
    注意：netaddr 的 IPNetwork 不校验主机位（1.2.3.4/24 会原样接受），
    因此这里统一用 ipaddress 非严格模式掩码到网段，杜绝畸形条目流入输出；
    netaddr 解析失败时再用 ipaddress 兜底，兼容个别源的特殊写法。
    """
    clean_ip = text.split('#')[0].strip()
    try:
        net = IPNetwork(clean_ip)
        return IPNetwork(str(ipaddress.ip_network(str(net), strict=False)))
    except (AddrFormatError, ValueError):
        pass
    try:
        return IPNetwork(str(ipaddress.ip_network(clean_ip, strict=False)))
    except ValueError:
        return None

def count_existing(path):
    """统计已有结果文件的条目数（跳过注释与空行），文件不存在返回 None"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip() and not line.startswith("#"))
    except OSError:
        return None

def main():
    session = build_session()
    v4_set = set()
    v6_set = set()
    now_str = get_beijing_time()

    # 1. 读取源文件
    if not os.path.exists(SOURCE_FILE):
        print(f"::error ::找不到源文件: {SOURCE_FILE}")
        sys.exit(1)

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    # 2. 循环拉取并解析
    failed_sources = []
    for url in urls:
        lines = fetch_ips(session, url)
        if lines is None:
            failed_sources.append(url)
            print("  -> 拉取失败（已自动重试），跳过")
            continue
        count = dropped = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith(("#", ";", "//")):
                continue
            net = parse_cidr(line)
            if net is None:
                dropped += 1
                continue
            if net.version == 4:
                v4_set.add(net)
            elif net.version == 6:
                v6_set.add(net)
            count += 1
        print(f"  -> 成功解析 {count} 条" + (f"，丢弃 {dropped} 条无法解析" if dropped else ""))
        if count == 0:
            # 拉到了内容但一条都没解析出来，同样按失败源记录
            failed_sources.append(url)

    # 3. 0 误伤逻辑合并 (netaddr 自动处理包含和连续段)
    v4_merged = cidr_merge(list(v4_set))
    v6_merged = cidr_merge(list(v6_set))

    # 4. 防呆校验：任何异常都直接中止，绝不写文件、绝不提交，保留线上旧列表
    if not v4_merged or not v6_merged:
        print(f"::error ::聚合结果为空（IPv4={len(v4_merged)} IPv6={len(v6_merged)}），疑似全部源失效，终止构建")
        sys.exit(1)

    if len(v4_merged) < MIN_V4_COUNT or len(v6_merged) < MIN_V6_COUNT:
        print(f"::error ::聚合条数低于安全阈值（IPv4={len(v4_merged)}/{MIN_V4_COUNT} "
              f"IPv6={len(v6_merged)}/{MIN_V6_COUNT}），终止构建")
        sys.exit(1)

    prev_v4 = count_existing(OUT_V4)
    prev_v6 = count_existing(OUT_V6)
    for name, old, cur in (("IPv4", prev_v4, len(v4_merged)), ("IPv6", prev_v6, len(v6_merged))):
        if old and cur < old * (1 - MAX_SHRINK_RATIO):
            print(f"::error ::{name} 条数从 {old} 缩水到 {cur}（超过 {MAX_SHRINK_RATIO:.0%}），"
                  f"疑似源大面积失效，终止构建")
            sys.exit(1)

    if failed_sources:
        print(f"::error ::本次有 {len(failed_sources)}/{len(urls)} 个源未贡献数据: {failed_sources}")

    # 5. 写入结果 (带时间戳注释)
    # --- 写入 IPv4 ---
    with open(OUT_V4, "w", encoding="utf-8") as f:
        f.write(f"# CN IPv4 List | Last Update: {now_str} (UTC+8)\n")
        f.write("\n".join(str(i) for i in v4_merged) + "\n")

    # --- 写入 IPv6 ---
    with open(OUT_V6, "w", encoding="utf-8") as f:
        f.write(f"# CN IPv6 List | Last Update: {now_str} (UTC+8)\n")
        f.write("\n".join(str(i) for i in v6_merged) + "\n")

    # --- 写入全量文件 (V4 + V6) ---
    with open(OUT_ALL, "w", encoding="utf-8") as f:
        f.write(f"# CN All IP List | Last Update: {now_str} (UTC+8)\n")
        for i in v4_merged:
            f.write(str(i) + "\n")
        for i in v6_merged:
            f.write(str(i) + "\n")

    # 6. 打印统计摘要
    print("\n" + "=" * 40)
    print(f"运行时间: {now_str}")
    print(f"聚合后 IPv4 条数: {len(v4_merged)}")
    print(f"聚合后 IPv6 条数: {len(v6_merged)}")
    print(f"总计规则条数: {len(v4_merged) + len(v6_merged)}")
    if failed_sources:
        print(f"异常源数量: {len(failed_sources)}/{len(urls)}（见上方 ::error 标注）")
    print("=" * 40)
    print("::notice ::所有文件已成功生成并注入北京时间戳。")

if __name__ == "__main__":
    main()
