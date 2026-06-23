# 📋 Kanban Board

一个轻量级的看板任务管理系统，Flask 后端 + 单文件前端，开箱即用。

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-green?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ 特性

- **三列看板**：待办 / 进行中 / 已完成
- **拖拽排序**：桌面端拖拽卡片到不同列
- **移动端适配**：左右滑动切换任务状态，底部弹窗操作
- **深色/浅色主题**：支持自动、深色、浅色三种模式
- **归档系统**：已完成任务可归档，支持搜索和恢复
- **任务备注**：每个任务可添加多条带时间戳的备注
- **优先级标记**：高 / 普通 / 低三级优先级
- **Cron 助手**：内置定时统计脚本，支持午间汇报、日结、周总结
- **零依赖前端**：纯 vanilla JS，无需构建工具
- **JSON 存储**：数据以 JSON 文件存储，简单透明

## 🚀 快速开始

```bash
# 克隆仓库
git clone https://github.com/yabo083/kanban-board.git
cd kanban-board

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制示例数据（可选）
cp data/tasks.json.example data/tasks.json

# 启动
python app.py
```

打开浏览器访问 `http://localhost:8888`

## ⚙️ 配置

通过环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `KANBAN_DATA_FILE` | `./data/tasks.json` | 数据文件路径 |
| `KANBAN_PORT` | `8888` | 服务端口 |

示例：

```bash
# 自定义数据路径和端口
export KANBAN_DATA_FILE="/var/lib/kanban/tasks.json"
export KANBAN_PORT=3000
python app.py
```

## 📦 部署

### systemd 服务

```bash
sudo tee /etc/systemd/system/kanban.service << 'EOF'
[Unit]
Description=Kanban Board
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/kanban-board
ExecStart=/path/to/kanban-board/venv/bin/python3 app.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now kanban
```

### Docker

```bash
docker build -t kanban .
docker run -d -p 8888:8888 -v kanban-data:/app/data kanban
```

## 🕐 Cron 定时统计

内置 `cron_helper.py` 支持多种统计模式：

```bash
python cron_helper.py progress  # 午间进度检查
python cron_helper.py evening   # 晚间日结
python cron_helper.py weekly    # 周总结
python cron_helper.py archive   # 自动归档已完成任务
```

配合 crontab 使用：

```crontab
# 每天中午12点汇报进度
0 12 * * * cd /path/to/kanban && venv/bin/python cron_helper.py progress

# 每天晚上10点日结
0 22 * * * cd /path/to/kanban && venv/bin/python cron_helper.py evening

# 每周日晚上9点周总结
0 21 * * 0 cd /path/to/kanban && venv/bin/python cron_helper.py weekly
```

## 📡 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/tasks` | 获取任务列表（`?archived=true` 获取归档） |
| `POST` | `/api/tasks` | 创建任务 |
| `PATCH` | `/api/tasks/:id` | 更新任务 |
| `DELETE` | `/api/tasks/:id` | 删除任务 |
| `POST` | `/api/tasks/:id/archive` | 归档任务 |
| `POST` | `/api/tasks/:id/unarchive` | 取消归档 |
| `POST` | `/api/archive/batch` | 批量归档已完成任务 |
| `GET` | `/api/stats` | 获取统计数据 |

### 创建任务示例

```bash
curl -X POST http://localhost:8888/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "写 README", "description": "给开源项目写文档", "priority": "high"}'
```

## 📁 项目结构

```
kanban-board/
├── app.py              # Flask 后端
├── cron_helper.py      # 定时统计脚本
├── requirements.txt    # Python 依赖
├── static/
│   └── index.html      # 单文件前端（HTML + CSS + JS）
├── data/
│   └── tasks.json.example  # 示例数据
├── Dockerfile
└── README.md
```

## 🎨 界面预览

- 深色主题为主，支持浅色切换
- 卡片式布局，优先级颜色标记
- 移动端底部弹窗操作，滑动切换状态
- 归档视图支持搜索过滤

## 📄 License

MIT
