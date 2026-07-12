# 服务器虚拟化取证 Skill — ESXi / Hyper-V / KVM

## 适用场景
服务器镜像取证、虚拟化平台分析、ESXi/Hyper-V/KVM 虚拟机提取、快照恢复、子虚拟机密码破解。

来源: 小谢取证"浅谈服务器虚拟化技术与仿真取证实战研究分析" + forensics-wiki 服务器取证

## 虚拟化平台识别

```bash
# 1. 识别虚拟化平台
mmls server.img                    # 查看分区
fls -o $OFFSET -r server.img | rg -i "vmware|esxi|hyper-v|kvm|qemu|xen"

# ESXi 特征文件
fls -o $OFFSET -r server.img | rg "\.vmdk$|\.vmx$|\.vmsd$|\.vmxf$|\.nvram$"

# Hyper-V 特征文件  
fls -o $OFFSET -r server.img | rg "\.vhdx$|\.avhdx$|\.vhd$"

# KVM/QEMU 特征文件
fls -o $OFFSET -r server.img | rg "\.qcow2$|\.qcow$|\.raw$|\.img$"

# 查找虚拟机配置文件
fls -o $OFFSET -r server.img | rg -i "vmx|vmware|virtual|machine|vm_config"
```

## ESXi 取证

```bash
# ESXi 目录结构
# /vmfs/volumes/<datastore>/<vm_name>/
#   ├── <vm_name>.vmx        # 虚拟机配置
#   ├── <vm_name>.vmdk       # 虚拟磁盘
#   ├── <vm_name>-flat.vmdk  # 实际数据
#   ├── <vm_name>.vmsd       # 快照定义
#   └── <vm_name>-000001.vmdk # 快照增量

# 1. 提取 VMX 配置（含密码提示）
icat -o $OFFSET server.img <inode> > vm_config.vmx
rg -i "password|guest|user|key" vm_config.vmx

# 2. 快照链分析
# .vmdk 文件中的 parentFileNameHint 指向父磁盘
rg "parentFileNameHint" *.vmdk

# 3. 虚拟机密码破解
# ESXi 6.x 密码在 /etc/shadow (SHA512)
icat -o $OFFSET server.img <inode> > esxi_shadow
hashcat -m 1800 esxi_shadow wordlist.txt

# 4. 日志分析
fls -o $OFFSET -r server.img | rg "vmkernel\.log|hostd\.log|vpxa\.log"
```

## Hyper-V 取证

```bash
# Hyper-V 目录结构
# C:\ProgramData\Microsoft\Windows\Hyper-V\
# C:\Users\Public\Documents\Hyper-V\Virtual hard disks\

# 1. VHDX 文件分析
# VHDX 是微软虚拟磁盘格式，可用 qemu-img 转换
qemu-img info disk.vhdx
qemu-img convert -f vhdx -O raw disk.vhdx disk.raw

# 2. 检查点/快照 (.avhdx)
fls -o $OFFSET -r server.img | rg "\.avhdx$"

# 3. 虚拟机配置
fls -o $OFFSET -r server.img | rg -i "Virtual Machines.*\.xml$"
icat ... > vm_config.xml
rg -i "password|user|key|secret" vm_config.xml
```

## KVM/QEMU 取证

```bash
# 1. QCOW2 镜像分析
qemu-img info disk.qcow2          # 查看信息（含 backing file 链）
qemu-img snapshot -l disk.qcow2   # 列出快照
qemu-img convert -f qcow2 -O raw disk.qcow2 disk.raw

# 2. Libvirt 配置
fls -o $OFFSET -r server.img | rg "/etc/libvirt/qemu/.*\.xml$"
icat ... > domain.xml
rg -i "password|passwd|secret" domain.xml

# 3. 磁盘 backing chain
# QCOW2 支持 backing file → 查看 backing 链可找到原始磁盘
qemu-img info --backing-chain disk.qcow2
```

## Docker 容器取证

```bash
# Docker 取证（竞赛中越来越多）
# 数据目录: /var/lib/docker/

# 1. 查找 Docker 相关文件
fls -o $OFFSET -r server.img | rg "docker|container"

# 2. 容器配置（含环境变量→可能含密码）
icat ... | python3 -m json.tool | rg -i "ENV|PASSWORD|SECRET|KEY|TOKEN"

# 3. 镜像层分析
# /var/lib/docker/overlay2/  → 分层文件系统
fls -o $OFFSET -r server.img | rg "overlay2"

# 4. Docker 日志
icat ... | rg -i "error|password|flag|ctf"
```

## 宝塔面板取证（国产服务器高频）

来源: 小谢取证"利用宝塔重构网站"

```bash
# 宝塔面板路径
# /www/server/panel/
# /www/wwwroot/                  # 网站根目录
# /www/server/data/              # 数据库

# 1. 宝塔配置（含面板密码）
fls -o $OFFSET -r server.img | rg "panel|宝塔|bt"
icat ... > /www/server/panel/data/default.db 2>/dev/null

# 2. 网站配置（Nginx/Apache）
fls -o $OFFSET -r server.img | rg "/www/server/panel/vhost/"

# 3. 数据库密码
icat ... | rg -i "DB_PASSWORD|db_password|mysql.*password"

# 4. 定时任务
icat ... | rg -i "cron|schedule|task"
```

## 国产操作系统取证（银河麒麟/UOS）

来源: 小谢取证"制作国产操作系统内存镜像"

```bash
# 银河麒麟 (Kylin) 特征
fls -o $OFFSET -r server.img | rg -i "kylin|neokylin|ubuntukylin"

# UOS (统信) 特征  
fls -o $OFFSET -r server.img | rg -i "uos|deepin|dde"

# 国产 OS 常见取证点
# /home/                        # 用户数据
# /var/log/                     # 系统日志（路径可能与标准 Linux 不同）
# /opt/apps/                    # UOS 应用商店安装路径
# /usr/share/applications/      # 桌面应用

# LiME 内存镜像采集（国产 OS 通用方法）
# 需要在仿真环境中编译 LiME 内核模块
```

## 仿真取证实战技巧

来源: 小谢取证"服务器虚拟化技术与仿真取证"

```bash
# 火眼仿真取证（BootMagixV4）
fireye-simulate     # 启动火眼仿真
# → 选择虚拟机配置文件 (.vmx / .vhdx / .qcow2)
# → 配置网络 (NAT/Bridge/Host-Only)
# → 启动虚拟机 → 进入系统直接查看

# VMware 仿真
# 1. 将 VMDK 转为 VMware 兼容格式
qemu-img convert -f raw -O vmdk disk.raw disk.vmdk

# 2. 创建 VMX 配置文件
cat > vm.vmx << 'EOF'
.encoding = "UTF-8"
config.version = "8"
virtualHW.version = "10"
scsi0.present = "TRUE"
scsi0.virtualDev = "lsilogic"
memsize = "4096"
scsi0:0.present = "TRUE"
scsi0:0.fileName = "disk.vmdk"
ethernet0.present = "TRUE"
ethernet0.connectionType = "nat"
guestOS = "other-linux"
EOF

# 3. 用 VMware/vmplayer 打开 vm.vmx
```

## 服务器 webshell 检测

```bash
# 1. 最近修改的脚本文件
fls -o $OFFSET -r server.img | rg "\.php$|\.jsp$|\.asp$|\.aspx$" 

# 2. 可疑 eval/base64 模式
icat ... | rg -i "(eval|exec|system|passthru|shell_exec|popen|proc_open|assert)\(.*\$_(GET|POST|REQUEST|COOKIE)"

# 3. 图片伪装 webshell
icat ... | rg -i "exif_imagetype|getimagesize|imagecreatefrom"

# 4. 日志中的 webshell 访问
icat ... | rg -i "POST.*\.php|\.jsp" | head -50
```

## 宝塔面板密码重置（如仿真后需要进入面板）

```bash
# 进入仿真系统后:
cd /www/server/panel && python3 tools.py panel <new_password>
# 或直接修改数据库
sqlite3 /www/server/panel/data/default.db "UPDATE users SET password='<hash>'"
bt 14    # 显示面板默认信息
```

## 提示
- **先仿真后静态** — 服务器比个人电脑更需要仿真（服务依赖复杂）
- **宝塔面板是国内比赛高频考点** — 记住 /www/server/panel/ 路径
- **Docker 容器密码常在环境变量中**
- **快照链 (Snapshot Chain) 可恢复被删除的数据**
- **ESXi shadow 可直接用 hashcat -m 1800 破解**

---

## E01 镜像 + 集群实战

### E01 直接分析 (Reasonix 可操作)
```bash
mmls disk.E01                             # 分区布局 (sleuthkit 原生支持)
fls -o $OFFSET -r disk.E01               # 文件列表
icat -o $OFFSET disk.E01 <inode> > file  # 提取文件
strings disk.E01 | rg -i "flag|ctf"      # 最快初扫
```
**决策**: strings 初扫 → 有明确目标 → CLI 提取。只有看 GUI 时才用 fireye-simulate。

### 服务器集群 (多 E01)
```bash
# 逐个识别角色
for e01 in *.E01; do
  fls -o $OFFSET -r "$e01" | rg "hostname|fstab|docker|nginx|mysql" 
done

# 跨服务器关联
python evidence_linker.py -e ./s1/ ./s2/ ./s3/

# 网络拓扑重建
icat ... /etc/hosts && icat ... /etc/nginx/sites-enabled/*
```

### 集群角色识别
| 发现 | 推断 |
|------|------|
| nginx + proxy_pass | 反向代理 |
| docker-compose 多 service | 微服务 |
| mysql bind-address=0.0.0.0 | 数据库节点 |
| redis slaveof | Redis 主从 |
| /etc/kubernetes/ | K8s 节点 |
| corosync + pacemaker | HA 集群 |

### RAID 重建
```bash
strings disk1.img | rg "mdadm|RAID"
# 检测后: mdadm --assemble --scan
```

### 案例: Web+DB+Cache 三层
```
server1: nginx → upstream backend { 10.0.1.2 }
server2: mysql → bind-address = 10.0.1.2
server3: redis → port 6379
→ 拓扑: LB(server1) → DB(server2) + Cache(server3)
```

---

## ⚡ Reasonix 可操作的新工具

### RAID 重建
```bash
python E:\CompetitionTools\scripts\raid_rebuild.py -d disk1.img disk2.img disk3.img --auto
python E:\CompetitionTools\scripts\raid_rebuild.py -d disk1.img disk2.img -t raid0 -s 65536
python E:\CompetitionTools\scripts\raid_rebuild.py -d disk1.img disk2.img disk3.img -t raid5 -m 2  # 缺盘恢复
```
支持: RAID 0/1/5 自动检测, 条带大小探测, 缺盘 XOR 恢复

### K8s/Docker Swarm 集群取证
```bash
python E:\CompetitionTools\scripts\k8s_forensics.py -d /mnt/node1/ /mnt/node2/ /mnt/node3/
```
自动提取: etcd secrets, ConfigMap, 环境变量密码, 集群拓扑重建

---

## vSAN + VCSA 集群 (2025 盘古石杯决赛)

来源: 取证与溯源公众号

### vSAN 集群架构
```
每台 ESXi 主机 3 块盘:
  盘1: 系统盘 (VMFSOS)
  盘2: 缓存盘 (vSAN Cache)
  盘3: 数据盘 (vSAN Data)

三个网络平面:
  Management: 192.168.10.0/24
  vSAN:       192.168.20.0/24
  vMotion:    192.168.30.0/24
```

### VCSA (vCenter Server Appliance)
```bash
# 关键信息
vcsa.pgs.cup                   # 主机名
5480                           # 管理页面端口
administrator@pgs.cup           # Web Client 登录
ntp.aliyun.com                  # 时间服务器
22:59                           # 每日备份时间
8.0.3.00500                     # 版本号
```

### 仿真要求
```
CPU: 8 核
RAM: 16 GB (vSAN 最低要求)
磁盘: SCSI 模式挂载 3 块 VMDK
网络: 3 块网卡对应 3 个网段
注意: esxi2/3 的 vSAN 网段容易配错 → 改为 192.168.20 段
```

### vSAN 关键信息提取
```bash
# 集群名: Cluster_Pguscup
# 磁盘组内 ISO: 2 个
# 虚拟机数量: 5 台 (含 2 台 vCLS 代理虚拟机)
# 虚拟机存储名: win11 (市场PC)
# vSAN 端口组: DSwitch-vSAN (8 上行端口)
# vSAN 集群类型: HCI (超融合)
# vSAN 许可密钥前5位: MG292
```

### vCLS 代理虚拟机
```
vSphere Cluster Services (vCLS):
  大小 0B, 用于 DRS + HA
  vCenter 宕机后集群服务仍可运行
  每集群自动部署, 不是真实业务 VM
```

### DNS 服务器取证
```bash
# DNS 记录: 8 条自建 A 记录
#   主机映射: dc/ftp/meeting/esxi1-3/vcsa/baocai
#   ftp → 192.168.10.99

# 系统信息:
#   Build: 17763
#   初始安装: 2025-05-03 15:45:38
```

### PHP 备份脚本分析 (CMS 网站)
```php
// 加密密钥按月生成
$base_key = 'cmf_backup_key_' . date('Ym');
$key = hash('sha256', $base_key, true);
// AES-256-CBC 加密, IV 以 base64 存储在文件头

// "2027年6月"的密钥:
echo hash('sha256', 'cmf_backup_key_202706');
// = 6863bd7f968ad31a7f389843845688bf2bca0832ff4460df41736465aa619dbf
```

### bcrypt 密码分析
```bash
# $2a$10$tcB68DmUWKZZmOv8HrDNnOTJbFqSsYD3olu3qnGix7.tw/Tbl7/qu
#   $2a$           = 算法版本
#   10$             = 成本参数
#   tcB68DmUWKZZmOv8HrDNnO = 22 字符盐值
#   TJbFqSsYD3olu3qnGix7.tw/Tbl7/qu = 31 字符哈希
```

---

## 历史命令审计 + 多检材联动 (长安杯2022)

### 1000条history重建网站架构
```bash
# 1. jar包启动: java -jar xxx.jar → /web/app/ 目录
# 2. npm run dev → 前端端口 (package.json → devServer.port)
# 3. jd-gui 反编译jar → application.properties → 数据库配置
# 4. 多检材联动: 浏览器历史 → 补全端口/密码/下载记录
# 5. Xshell/Xftp 会话记录 → 远程连接IP
```

### VeraCrypt PIM (Personal Iterations Multiplier)
```bash
# 密码+PIM 双重保护: 密码常为中文诗句拼音
# "五花马千金裘" → "5FlowerMa)(ThousandGoldQiu]" + PIM:88
# PIM 来源: 检材照片/U盘/手机图片 → 枚举 (15/30/88常见)
# 加载U盘: CSI挂载虚拟磁盘 → VC选择设备 → 输入密码+PIM

---

## ⚡ 服务器取证核心原则 (2026盘古石教训)

### 仿真优先，不是裸读优先
```
❌ 试图解析 LVM metadata 字节码 → 浪费时间
❌ 逐扇区搜索 ext4 superblock → 找不到
✅ VMware 建虚拟机 → 挂载 E01 → 开机 → 直接看

手机/汽车 = 解析可行 (单个文件系统/flash)
服务器     = 仿真必须 (LVM + Ceph + 网络 + 多节点)
```

### PVE 集群恢复流程
```bash
# 1. VMware 建三台虚拟机，挂载 disk01 (系统) + disk02 (Ceph)
# 2. 修复 /etc/network/interfaces (ens36 → vmbr0)
# 3. ip addr add 旧IP → ceph-mon → ceph-osd 启动
# 4. qm start 100 --memory 1024 --cores 1 --kvm 0  (TCG软模拟)
# 5. RBD export → qemu-nbd 挂载 → mount LVM
# 6. MySQL 导入 → 查数据答题
```

### 需要仿真才能回答的题型
```
PVE/ESXi 版本号  → pveversion / esxcli
集群名/节点名    → /etc/pve/corosync.conf 或 hostname
虚拟机信息        → qm list / qm config
数据库分析        → MySQL 查询 (需启动VM)
网络配置          → ip addr / interfaces
```
```
