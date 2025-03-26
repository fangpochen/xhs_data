# 小红书维权数据分析系统

基于Spider_XHS爬虫项目打造的维权数据采集与分析系统，专注于医美和男科领域的消费维权数据收集和分析。

## 项目概述

本项目旨在帮助消费者了解医美和男科领域的常见维权问题，提供数据支持和维权指导。系统自动采集小红书上的维权相关数据，进行结构化存储和深度分析，生成可视化报告，为消费者维权提供参考。

## 功能特性

- **自动数据采集**：定时从小红书采集医美和男科领域的维权相关内容
- **多维度分析**：文本内容分析、用户行为分析、热度趋势分析
- **可视化报告**：自动生成数据分析报告，包含词云图、统计图表等
- **服务器部署**：支持远程服务器部署，定时执行采集任务
- **行业词库**：内置医美和男科领域专业词汇库，提高分析准确性

## 文件结构

```
/
├── Spider_XHS/                  # 小红书爬虫基础项目
├── xhs_rights_collector.py      # 维权数据采集脚本
├── analyze_rights_data.py       # 数据分析脚本
├── industry_dict.txt            # 行业专用词典
├── server_deployment.md         # 服务器部署指南
├── PROJECT_RULES.md             # 项目规则文档
└── README.md                    # 项目说明文档
```

## 快速开始

### 1. 环境准备

- Python 3.7+
- Node.js 18+
- 安装依赖包：

```bash
# 克隆仓库
git clone https://github.com/cv-cat/Spider_XHS.git

# 安装Python依赖
pip install -r Spider_XHS/requirements.txt
pip install schedule pandas matplotlib jieba wordcloud

# 安装Node.js依赖
cd Spider_XHS
npm install
cd ..
```

### 2. 配置小红书Cookie

在Spider_XHS目录下的`.env`文件中添加你的小红书Cookie：

```bash
COOKIES='你的小红书Cookie字符串'
```

获取Cookie的方法：
1. 登录小红书网页版
2. 按F12打开开发者工具
3. 切换到Network标签
4. 筛选fetch类型请求
5. 点击任意请求，在Headers中找到Cookie值
6. 复制完整Cookie字符串

### 3. 运行数据采集

```bash
# 一次性运行采集所有类别的数据
python xhs_rights_collector.py --mode once --category all

# 只采集医美类别数据
python xhs_rights_collector.py --mode once --category medical_beauty

# 只采集男科类别数据
python xhs_rights_collector.py --mode once --category male_health

# 定时执行采集任务
python xhs_rights_collector.py --mode schedule --schedule_time 03:00 --keywords_per_run 5
```

### 4. 数据分析

```bash
# 分析采集到的数据
python analyze_rights_data.py

# 指定数据目录
python analyze_rights_data.py --data_dir /path/to/data
```

### 5. 查看分析结果

分析结果将保存在`data/rights_protection/analysis/`目录下：
- `report.html` - 完整的分析报告
- `wordcloud.png` - 关键词词云图
- `category_distribution.png` - 类别分布图
- `keyword_distribution.png` - 关键词分布图
- `top_users.png` - 最活跃用户图
- `analysis_data.json` - 分析数据JSON格式

## 服务器部署

请参考 [server_deployment.md](server_deployment.md) 文件，了解如何在服务器上部署和运行本系统。

## 注意事项

1. 本项目仅供学习和研究使用，请勿用于商业目的
2. 请遵守小红书平台的使用条款和规则
3. 采集频率不宜过高，建议设置合理的时间间隔
4. 请勿爬取或使用涉及用户隐私的数据
5. Cookie需要定期更新，失效后需重新获取

## 维权建议

如果您是医美或男科领域的消费者，在遇到消费纠纷时：

1. 保存所有证据，包括聊天记录、合同、付款凭证等
2. 与商家进行协商沟通，表明自己的诉求
3. 协商不成可向消费者协会或市场监督管理部门投诉
4. 必要时可通过法律途径维护自身权益

## 贡献指南

欢迎对本项目进行改进和完善：

1. Fork本仓库
2. 创建你的特性分支 (git checkout -b feature/your-feature)
3. 提交你的更改 (git commit -m 'Add some feature')
4. 推送到分支 (git push origin feature/your-feature)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见 LICENSE 文件 