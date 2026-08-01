# Job Data ETL

## 项目简介

使用 Python + Pandas 对招聘数据进行 ETL 清洗、统计分析与报告生成，并支持可配置清洗规则（YAML）。

---

## 技术栈

- Python
- Pandas
- Typer（CLI）
- PostgreSQL（可选入库）
- Git / GitHub

---

## 项目结构

```text
DE/
├── data/
│   ├── raw/
│   │   └── DataAnalyst.csv
│   └── clean/
│       └── jobs_clean.csv
├── artifacts/                  # Top 岗位/技能报告输出目录（按时间戳）
├── clean.py                    # 清洗模块（核心函数拆分）
├── clean_config.yaml           # 清洗配置
├── pipeline.py                 # 编排入口（清洗 + 可选入库 + 报告）
├── load_to_postgres.py         # PostgreSQL 入库
├── analysis.sql                # SQL 分析脚本
└── .gitignore

核心功能
支持 YAML 配置化清洗规则
清洗函数按职责拆分（加载、列处理、无效值替换、公司名清洗、薪资清洗、去重、保存）
生成基础 Markdown 报告
生成“每公司 Top 岗位 / Top 技能”报告（可选）
可选写入 PostgreSQL
清洗规则（当前）
删除无用列（如 Unnamed: 0）
替换无效值（如 -1 -> null）
公司名按换行符截断（保留第一段）
薪资字段移除 (Glassdoor est.)
去重
关键列缺失率统计与告警
如何运行
1. 激活虚拟环境（Windows PowerShell
cd D:\桌面\DE
Activate.ps1

2. 仅跑清洗 + 报告（不入库，推荐先这样验收）
python pipeline.py --skip-load --include-top-reports --append-to-report

3. 跑完整流程（包含入库）
python pipeline.py --include-top-reports --append-to-report
入库依赖数据库配置（可通过 .env 或系统环境变量设置）。

输出结果
清洗结果：data/clean/jobs_clean.csv
主报告：report.md
Top 报告：artifacts/{timestamp}/company_top_jobs.csv、company_top_jobs.md
若存在 Skill 列，还会输出对应 skills 报告

项目流程
读取原始 CSV
↓
按配置执行清洗（列处理 / 无效值处理 / 文本清洗）
↓
去重
↓
保存 clean CSV
↓
生成基础统计报告
↓
（可选）生成每公司 Top 岗位/技能报告
↓
（可选）写入 PostgreSQL

结果校验（面试可说）
清洗后数据维度：2253 x 15
Unnamed: 0 已删除
Company Name 无换行残留
Salary Estimate 无 Glassdoor est. 残留
关键列缺失率已输出到日志
难点与优化
CSV 在 Excel/WPS 预览“看起来乱”通常是导入参数问题（应使用 UTF-8 + 逗号分隔导入）
入库阶段当前为追加写入，可进一步做幂等（唯一键 + upsert）
可扩展技能抽取逻辑（从 Job Description 自动抽取 Skill）
后续计划
增加自动化测试（单元测试 + 集成测试）
增加 requirements.txt 与一键启动脚本
增加更完整的数据质量指标（异常值、分布漂移）
```
