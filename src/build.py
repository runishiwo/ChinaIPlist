import requests
from netaddr import IPNetwork, cidr_merge

SOURCE_FILE = "data/sources.txt"
OUT_V4 = "output/cn_v4.txt"
OUT_V6 = "output/cn_v6.txt"

def fetch(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.text.splitlines()
    except:
        pass
    return []

def main():
    v4 = []
    v6 = []

    with open(SOURCE_FILE, "r") as f:
        urls = [i.strip() for i in f if i.strip()]

    for url in urls:
        print("fetch:", url)
        for line in fetch(url):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                net = IPNetwork(line)
                if net.version == 4:
                    v4.append(net)
                else:
                    v6.append(net)
            except:
                continue

    v4 = cidr_merge(v4)
    v6 = cidr_merge(v6)

    with open(OUT_V4, "w") as f:
        f.write("\n".join(str(i) for i in v4))

    with open(OUT_V6, "w") as f:
        f.write("\n".join(str(i) for i in v6))

    print("v4:", len(v4), "v6:", len(v6))

if __name__ == "__main__":
    main()
