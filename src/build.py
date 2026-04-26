import requests

SOURCE_FILE = "data/sources.txt"
OUTPUT_FILE = "output/cn_ip.txt"

def fetch(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.text.splitlines()
    except:
        pass
    return []

def main():
    cidrs = set()

    with open(SOURCE_FILE, "r") as f:
        urls = [i.strip() for i in f if i.strip()]

    for url in urls:
        print("fetch:", url)
        for line in fetch(url):
            line = line.strip()
            if "/" in line:
                cidrs.add(line)

    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(sorted(cidrs)))

    print("done:", len(cidrs))

if __name__ == "__main__":
    main()
