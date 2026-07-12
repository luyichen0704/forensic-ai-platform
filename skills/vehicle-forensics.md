# Vehicle / IoT Forensics Skill — 车联网取证

## 适用场景
车辆碰撞事故分析、CAN 总线攻防、ECU 固件逆向、ADAS 恶意篡改、T-BOX 远程控制取证。

来源: 2026 盘古石杯 IoT/Car 部分 (Cookie4N6)

## 车联网取证关键组件

```
车辆取证检材通常包含:
┌─────────────────────────────────────────────┐
│ car.E01 → 车辆电子系统镜像                    │
│   ├── system.dlt          ← 系统诊断日志      │
│   ├── gateway_ecu.bin     ← 网关固件          │
│   ├── engine_ecu.bin      ← 发动机控制固件     │
│   ├── bcm_ecu.bin         ← 车身控制模块      │
│   ├── adas_firmware.bin   ← ADAS 固件         │
│   ├── tbox/               ← T-BOX 远程通信    │
│   ├── dashcam/            ← 行车记录仪        │
│   └── databases/          ← 车机浏览器/蓝牙DB  │
└─────────────────────────────────────────────┘
```

## DLT 日志分析 (Diagnostic Log and Trace)

```bash
# DLT 是车载诊断日志标准格式
# system.dlt 包含所有 ECU 通信记录

# 关键搜索模式
strings system.dlt | rg -i "CRC|error|fault|collision|brake|throttle|steering"
strings system.dlt | rg -i "LKA|ADAS|override|inject|spoof|attack"
strings system.dlt | rg -i "msg 0x[0-9A-F]{3}"        # CAN 报文 ID

# 典型攻击日志模式:
# "CGW ROUT ERR Invalid CRC on msg 0x0A0"  → CAN 注入攻击
# "Override Active"                        → 人机争夺方向盘
# "LKA steering -45deg"                   → ADAS 恶意转向请求
```

### DLT 严重级别
```
INFO  → 正常信息
WARN  → 警告 (ADAS 异常请求)
ERR   → 错误 (CRC 校验失败 = 注入)
FATL  → 致命 (碰撞确认)
```

## CAN 总线分析

```bash
# CAN ID 格式: 0xXXX (11-bit) 或 0xXXXXXXX (29-bit)
# 动力总成总线常见 ID:
#   0x0A0 - 转向控制
#   0x1xx - 制动/油门
#   0x2xx - 轮速传感器
#   0x3xx - 发动机 RPM

# 攻击特征:
# 1. CRC 校验失败 → 报文被篡改
# 2. 异常高频率 → 同频注入压制原车信号  
# 3. MAC 认证缺失 → 安全协议缺陷
# 4. 非预期 ID 出现 → 恶意指令注入
```

## ECU 固件分析

```bash
# 网关固件 (gateway_ecu.bin)
strings gateway_ecu.bin | rg -i "key|seed|master|crypto|auth"
strings gateway_ecu.bin | rg -i "[0-9A-F]{16}"       # 16位 hex seed

# 发动机固件 (engine_ecu.bin)
strings engine_ecu.bin | rg -i "limit|max|speed|RPM|restrict|flag"
strings engine_ecu.bin | rg -i "LIVE_TEACH|SPEED_LIMIT|GOVERNOR"

# ADAS 固件
strings adas_firmware.bin | rg -i "threshold|min_speed|trigger|km/h"
# 查找恶意代码触发条件: 最低车速阈值
```

## T-BOX 取证 (远程通信盒)

```bash
# T-BOX = Telematics Box = 车联网网关
# 关键路径:
fls -r car.E01 | rg -i "tbox|telematics|comm"

# 通信日志 PCAP
tshark -r telemetry.pcap -Y "http" -T fields -e http.host -e http.request.uri

# 恶意回连检测:
# - HTTP GET 伪装成媒体流 → /media/audio/playlist_1.m3u8
# - 反向 Shell: "Reverse shell connected... root@starOS:~#"
# - 下载恶意固件: http://C2_IP/malicious.bin

# VPN/代理配置
icat ... /tbox/conf/interfaces | rg -i "vpn|proxy|tunnel|remote"
```

## 升级日志分析

```bash
# update.log 关键模式
strings update.log | rg -i "force|bypass|signature|ignore|flash"
# "Signature bypass flag is active (-f force)" → 强制忽略签名刷入恶意固件
```

## 车机数据库分析

```bash
# 浏览器历史 → 黑客访问的仓库
sqlite3 History.db "SELECT url FROM urls WHERE url LIKE '%github%'"

# 蓝牙连接历史  
sqlite3 bluetooth.db "SELECT name, address, last_connected FROM devices"

# 导航记录
sqlite3 navigation.db "SELECT * FROM routes ORDER BY timestamp DESC"
```

## EDR 数据提取 (事件数据记录器)

```bash
# EDR = Event Data Recorder = 车辆"黑匣子"
# 记录碰撞前后数秒的车辆状态

# 关键数据:
# - 纵向车速 (采样点 0 = 碰撞瞬间)
# - 制动踏板状态
# - 油门踏板百分比
# - 方向盘角度
# - 安全带状态
# - 气囊展开时间
```

## OBD 冻结帧

```bash
# Freeze Frame: 故障发生时 ECU 自动记录的参数快照
# engine_ecu.bin → 搜索 RPM/speed 值
strings engine_ecu.bin | rg -i "rpm|freeze|frame|snapshot"
```

## 行车记录仪

```bash
# metadata.json → 碰撞加速度 + 完整性校验
icat ... dashcam/metadata.json
# 检测: "integrity_check": "FAILED" → 数据被篡改
```

## NFC/PKE 钥匙取证

```bash
# PKE = Passive Keyless Entry
# RF 日志 → 寻找被克隆的钥匙 ID
strings pke_rf.log | rg -i "KEY_ID|clone|unauthorized|NFC"

# 克隆检测: 同一时间两个不同 ID 出现
```

## 车辆取证攻击链重建

```
1. 黑客访问 GitHub 仓库 → 获取 exploit 代码
2. 蓝牙连接车辆 → 近场攻击
3. 通过 T-BOX 远程建立 Reverse Shell (root)
4. systemctl stop sec_monitor → 停止安全监护进程
5. 强制刷入恶意固件 (-f force 跳过签名)
6. 固件中隐藏的恶意代码在 >X km/h 时触发
7. ADAS 发出 -45° 异常转向 → 驾驶员干预 (Override Active)
8. CAN 总线被注入恶意 0x0A0 报文 → CRC 错误
9. 碰撞发生 → EDR 记录数据

收集证据链:
  GitHub URL → 蓝牙 MAC → Reverse Shell IP → 恶意固件 hash → CAN ID → EDR 速度
```

## 快速检查清单

```
□ system.dlt → 搜索 "CRC|override|collision|FATL"
□ CAN 报文 → 检查异常 ID / CRC 失败 / MAC 缺失
□ gateway_ecu.bin → 提取 Master Key Seed (16 位 hex)
□ engine_ecu.bin → 查找速度限制标志 / RPM 冻结帧
□ adas_firmware.bin → 查找触发阈值 (km/h)
□ T-BOX telemetry.pcap → 找 C2 通信 / Reverse Shell
□ update.log → 找 force bypass 签名
□ 车机数据库 → 浏览器 GitHub URL / 蓝牙设备
□ dashcam metadata.json → 完整性校验
□ PKE RF 日志 → 被克隆的钥匙 ID
```
