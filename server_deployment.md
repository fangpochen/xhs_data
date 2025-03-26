# 维权数据采集脚本服务器部署指南

这个指南将帮助你在服务器上部署和运行小红书维权数据采集脚本。

## 1. 系统要求

- Linux 服务器 (Ubuntu 18.04+ 或 CentOS 7+ 推荐)
- Python 3.7+
- Node.js 18+
- 至少 2GB RAM
- 至少 20GB 磁盘空间 (视数据量增加)

## 2. 环境准备

### 2.1 安装 Python 依赖

```bash
# 更新包管理器
apt update  # Ubuntu/Debian
# 或
yum update  # CentOS/RHEL

# 安装 Python 和相关工具
apt install python3 python3-pip python3-venv  # Ubuntu/Debian
# 或
yum install python3 python3-pip  # CentOS/RHEL

# 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install -y nodejs  # Ubuntu/Debian
# 或
yum install -y nodejs  # CentOS/RHEL
```

### 2.2 创建项目目录

```bash
mkdir -p /opt/xhs_rights
cd /opt/xhs_rights
```

## 3. 项目部署

### 3.1 获取代码

```bash
# 克隆 Spider_XHS 项目
git clone https://github.com/cv-cat/Spider_XHS.git

# 复制我们的采集脚本到项目目录
cd /opt/xhs_rights
# 将xhs_rights_collector.py上传到此目录
```

### 3.2 配置 Python 虚拟环境

```bash
cd /opt/xhs_rights
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r Spider_XHS/requirements.txt
pip install schedule pandas argparse
```

### 3.3 配置 Node.js 环境

```bash
cd /opt/xhs_rights/Spider_XHS
npm install
```

### 3.4 配置小红书 Cookie

创建或编辑 `.env` 文件，填入你的小红书 Cookie:

```bash
cd /opt/xhs_rights
echo "COOKIES='你的小红书Cookie'" > Spider_XHS/.env
```

获取 Cookie 的方法:
1. 用浏览器访问小红书网页版并登录
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 筛选 "fetch" 类型的请求
5. 点击任意一个请求，查看 Headers 中的 Cookie 值
6. 复制完整的 Cookie 字符串

## 4. 运行脚本

### 4.1 手动运行（一次性执行）

```bash
cd /opt/xhs_rights
source venv/bin/activate

# 运行所有类别的数据采集
python xhs_rights_collector.py --mode once --category all

# 只运行医美类别的数据采集
python xhs_rights_collector.py --mode once --category medical_beauty

# 只运行男科类别的数据采集
python xhs_rights_collector.py --mode once --category male_health
```

### 4.2 设置定时任务（使用脚本内置的调度器）

```bash
cd /opt/xhs_rights
source venv/bin/activate

# 设置每天凌晨 3 点运行，每次采集 5 个关键词
nohup python xhs_rights_collector.py --mode schedule --schedule_time 03:00 --keywords_per_run 5 > /dev/null 2>&1 &
```

### 4.3 使用 Systemd 设置为系统服务（推荐）

创建服务文件:

```bash
cat > /etc/systemd/system/xhs-collector.service << 'EOF'
[Unit]
Description=XHS Rights Protection Data Collector
After=network.target

[Service]
User=root
WorkingDirectory=/opt/xhs_rights
ExecStart=/opt/xhs_rights/venv/bin/python /opt/xhs_rights/xhs_rights_collector.py --mode schedule --schedule_time 03:00 --keywords_per_run 5
Restart=on-failure
RestartSec=5s
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=xhs-collector

[Install]
WantedBy=multi-user.target
EOF
```

启用和管理服务:

```bash
# 启用服务开机自启
systemctl enable xhs-collector

# 启动服务
systemctl start xhs-collector

# 查看服务状态
systemctl status xhs-collector

# 查看日志
journalctl -u xhs-collector -f
```

## 5. 数据管理

### 5.1 数据目录结构

```
/opt/xhs_rights/data/rights_protection/
├── excel/                        # Excel 数据存储
│   ├── medical_beauty/          # 医美类别数据
│   ├── male_health/             # 男科类别数据
│   └── general_rights/          # 综合维权类别数据
├── media/                        # 媒体文件存储（图片和视频）
│   ├── medical_beauty/
│   ├── male_health/
│   └── general_rights/
└── logs/                         # 日志文件
```

### 5.2 定期备份

设置自动备份任务:

```bash
cat > /etc/cron.weekly/backup-xhs-data << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/xhs_data"
DATE=$(date +%Y%m%d)
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/xhs_rights_data_$DATE.tar.gz /opt/xhs_rights/data
find $BACKUP_DIR -name "xhs_rights_data_*.tar.gz" -mtime +30 -delete
EOF

chmod +x /etc/cron.weekly/backup-xhs-data
```

## 6. 监控和维护

### 6.1 检查磁盘空间

```bash
# 设置磁盘空间检查脚本
cat > /opt/xhs_rights/check_disk.sh << 'EOF'
#!/bin/bash
USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USAGE -gt 85 ]; then
    echo "警告: 磁盘使用率已超过 85%，请清理空间" | mail -s "服务器磁盘空间告警" your-email@example.com
fi
EOF

chmod +x /opt/xhs_rights/check_disk.sh

# 添加到 crontab
(crontab -l 2>/dev/null; echo "0 8 * * * /opt/xhs_rights/check_disk.sh") | crontab -
```

### 6.2 日志轮转

通过 loguru 的配置，脚本已经自带日志轮转功能，不需要额外配置。

## 7. 故障排除

### 7.1 脚本无法启动

- 检查 Python 环境: `python3 --version`
- 检查依赖是否安装: `pip list`
- 检查 .env 文件中的 Cookie 是否有效

### 7.2 采集数据失败

- Cookie 可能已过期，需要重新获取并更新
- 网络连接问题，检查服务器网络
- 小红书可能有反爬虫机制，尝试降低采集频率

### 7.3 服务自动停止

- 检查系统日志: `journalctl -u xhs-collector`
- 可能是内存不足，考虑增加服务器内存或减少采集频率

## 8. 联系与支持

如有问题，请联系项目维护者。 