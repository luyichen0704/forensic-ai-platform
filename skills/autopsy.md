# Autopsy Skill — GUI 法证平台

## 适用场景
GUI 磁盘/手机分析、时间线可视化、通信记录提取、批量自动化报告。

## 安装

```powershell
winget install SleuthKit.Autopsy
# 安装路径: C:\Program Files\Autopsy-4.22.1\bin\autopsy64.exe
```

## 启动

```powershell
# GUI 模式（日常分析）
C:\Program Files\Autopsy-4.22.1\bin\autopsy64.exe

# 命令行模式（自动化）
autopsy64.exe --createCase --caseDir=C:\cases\case1 --ingest
```

## 核心功能模块

### 1. 案件管理
```
创建新案件 → 添加证据源（磁盘镜像/手机镜像/文件夹）
→ 自动运行 Ingest 模块 → 生成索引数据库
→ 所有分析模块共享同一个案件数据库
```

### 2. 磁盘/文件系统分析
- 自动识别分区表 → MBR/GPT → 挂载为虚拟设备
- 文件系统解析：NTFS/EXT4/FAT/HFS+ 等
- 已删除文件恢复（底层调用 TSK）
- 文件签名检测（MIME 类型 vs 扩展名不匹配高亮）
- 压缩包/归档递归展开

### 3. 时间线视图
- 所有文件 MACB 时间合并为一条时间线
- 支持拖动缩放、按时间范围过滤
- 按事件类型着色（文件创建/修改/访问/删除）

### 4. 关键词搜索
- 索引化全文搜索（基于 Solr/Lucene）
- 正则表达式支持
- 日期范围 + 文件类型 + 路径 组合过滤
- 搜索结果高亮并定位到原始文件

### 5. 通信分析（手机/桌面）
| 数据源 | 提取内容 |
|--------|---------|
| 微信 | 联系人/聊天记录/图片/语音 |
| QQ | 好友/群聊/文件传输 |
| Telegram | 会话/消息/媒体 |
| 短信/彩信 | 收发时间/号码/内容 |
| 通话记录 | 来电/去电/时长/归属地 |
| 邮件 | PST/OST/EML 解析 |

### 6. 媒体分析
- 图片：缩略图网格 + EXIF/GPS 面板 + 人脸检测
- 视频：内置播放器 + 逐帧分析
- 文档：PDF/Office 内容预览

### 7. 报告生成
- HTML 报告（含缩略图/时间线/图表）
- PDF 报告（适合打印/存档）
- Excel 导出（文件清单/通信记录）
- KML 导出（地理位置可视化）

## 与 TSK CLI 工具配合

```
CLI (TSK) 擅长:                    GUI (Autopsy) 擅长:
├─ 批量脚本自动化                   ├─ 可视化概览
├─ 管道组合 (mmls|fls|icat|strings) ├─ 时间线快速定位
├─ 精细控制（inode级操作）          ├─ 通信记录直观浏览
└─ 远程/终端环境                    └─ 一键报告生成

最佳实践:
1. 先用 Autopsy 做全景扫描 → 发现可疑区域
2. 再用 TSK CLI 精细提取 → 导出证据文件
3. 最后用 Autopsy 生成报告
```

## 常见 Ingest 模块

| 模块 | 功能 |
|------|------|
| Recent Activity | 最近活动提取（浏览器/文档/下载） |
| Hash Lookup | NSRL/自定义哈希库比对 |
| File Type Identification | 文件扩展名 vs 实际类型检测 |
| Embedded File Extraction | ZIP/RAR/DOCX 内嵌文件提取 |
| Exif Parser | 图片 EXIF/GPS 元数据 |
| Keyword Search | 预定义关键词索引 |
| Email Parser | PST/OST/MBOX 邮件解析 |
| PhotoRec Carver | 文件头特征雕刻（需插件） |
| Android Analyzer | APK/短信/通话/联系人提取 |
| iOS Analyzer | iTunes 备份/iCloud 数据解析 |
| GPX Parser | GPS 轨迹提取 |
| Interesting Files | 可疑文件自动标记 |

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+N | 新建案件 |
| Ctrl+O | 打开案件 |
| Ctrl+F | 关键词搜索 |
| Ctrl+T | 时间线视图 |
| F5 | 刷新当前视图 |
| Del | 标记/取消标记 |
| Ctrl+E | 导出文件 |

## 实用技巧

1. **大镜像先建索引再分析**：100GB+ 镜像全程搜索会很慢，先用 Ingest 建好索引
2. **时间线过滤找关键点**：把时间线缩放到事件发生前后 1 小时，快速定位嫌疑人操作
3. **通信分析导出 CSV**：用报告模块导出通信记录为 CSV → Python pandas 做关联分析
4. **MCP Server**：4.23.0 版本支持 AI 工具直接调用 Autopsy API，实现自动化分析流水线
5. **插件市场**：Tools → Plugin Manager → 搜索安装社区插件（300+）

## 已知限制

- 不支持 E01 直接打开（需先转 RAW 或通过 AIM 挂载）
- 大文件（>500GB）扫描耗时较长
- 中文搜索需要配置分词器
- WSL 环境下 GUI 需要 X11 转发
