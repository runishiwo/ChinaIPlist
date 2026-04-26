# CNIP List Auto Build

本项目用于每日自动汇总中国大陆 IP 段（IPv4 / IPv6），并进行 CIDR 去重与合并，生成统一 CNIP 列表。

---

## 📦 输出文件

- `cn_v4.txt` → IPv4 中国 IP 段
- `cn_v6.txt` → IPv6 中国 IP 段
- `cnip.txt` → IPv4 + IPv6 合并去重结果

---

## 🔄 数据来源

本项目数据来源于以下公开项目，仅用于聚合与整理：

- 17mon China IP List  
  https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt  

- gaoyifan China Operator IP  
  https://github.com/gaoyifan/china-operator-ip  

- IPdeny Country IP Blocks  
  https://www.ipdeny.com/ipblocks/data/countries/cn.zone  

- SnowCore8 IPChinaList  
  https://github.com/SnowCore8/IPChinaList  

- IWIK IP Country List  
  http://www.iwik.org/ipcountry/CN.cidr  

- Loyalsoldier GeoIP CN List  
  https://github.com/Loyalsoldier/geoip  

---

## ⚙️ 处理方式

- 使用 `netaddr` 进行 CIDR 解析
- IPv4 / IPv6 分离处理
- 自动 CIDR merge 去重
- 最终合并生成 cnip.txt

---

## ⚠️ 免责声明

本项目仅用于网络研究与学习用途。

所有 IP 数据均来自公开项目，本项目不拥有任何原始数据版权。

如有侵权，请联系删除相关来源。

---

## ❤️ 致谢

感谢以下项目的开源贡献者：

- 17mon
- gaoyifan
- IPdeny
- SnowCore8
- IWIK
- Loyalsoldier

没有这些项目，本工具无法实现。

---

## 📅 更新方式

本项目通过 GitHub Actions 每日自动更新。
