# 八字合盘匹配系统

![Version](https://img.shields.io/badge/version-1.0.0-purple)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-green)
![Vue](https://img.shields.io/badge/frontend-Vue%203%20%2B%20Vite-orange)

---

## 项目定位

> **「星海」——用八字命理，找到与你最合的那个人。**

本项目是一个**八字合盘匹配小工具**的功能模拟原型（MVP）。

核心逻辑：输入你的出生年月日时和性别，系统从万人八字库中，按**六维度合盘算法**为你匹配最合拍的人，并以**传统排盘表格式**直观展示对比结果。

```
输入：出生信息 + 性别
  ↓
排盘：调用 sxtwl 库计算四柱八字 + 十神 + 命卦 + 纳音
  ↓
匹配：六维度打分引擎（地支合冲 / 五行互补 / 天干合 / 日主关系 / 纳音 / 神煞）
  ↓
输出：Top-N 匹配结果 + 可视化合盘对比详情
```

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 🔮 出生信息输入 | 日期滚轮选择器 + 时辰滚轮（子时～亥时），交互流畅 |
| 🧮 八字自动排盘 | 基于 `sxtwl` 库，精确计算四柱、十神、命卦、生肖、格局 |
| ⚖️ 六维合盘算法 | 地支合冲、五行互补、天干合、日主关系、纳音、神煞，加权汇总 |
| 📊 合盘可视化对比 | 双盘式排盘表（年/月/日/时四柱并排），天干按五行发光着色 |
| 🌌 宇宙星空 UI | Canvas 粒子星空背景 + 毛玻璃卡片 + 暗色主题，神秘高级 |
| 📱 响应式设计 | 桌面端 / 平板 / 手机全适配 |

---

## 技术架构

```
bazi-match/
├── backend/                # FastAPI 后端
│   ├── main.py            # 接口入口（/api/match, /api/health）
│   ├── matcher.py         # 六维度合盘匹配引擎
│   ├── paipan.py        # 八字排盘（封装 sxtwl）
│   ├── models.py         # Pydantic 数据模型
│   ├── db.py             # SQLite 数据库操作
│   ├── config.py         # 维度权重 + 等级映射配置
│   └── seed.py          # 万人八字库种子数据
├── frontend/             # 前端（Vue 3 + Vite）
│   ├── index.html        # SPA 入口
│   ├── css/
│   │   ├── design-system.css  # 设计令牌（暗色主题）
│   │   └── style.css        # 组件样式 + 星空主题
│   └── js/
│       ├── app.js            # Vue 3 应用主逻辑
│       ├── bazi-utils.js    # 八字工具函数
│       └── particles.js     # Canvas 粒子星空动画
├── data/                  # SQLite 数据库文件
├── docs/                  # 设计文档（PRD / 技术方案 / 数据库设计）
└── frontend.bat / .sh    # 一键启停前端脚本
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+ / FastAPI / Uvicorn / SQLite |
| 排盘 | `sxtwl`（寿星天文历，支持八字精确排盘） |
| 前端 | Vue 3（CDN）+ Vite（构建） + Tailwind CSS |
| 动画 | Canvas 原生粒子系统（星空背景） |
| 部署 | 前端：`python -m http.server` 静态托管；后端：Uvicorn |

---

## 快速开始

### 1. 后端启动

```bash
cd backend
python -m venv venv311
# Windows:
venv311\Scripts\activate
# macOS/Linux:
# source venv311/bin/activate

pip install -r requirements.txt
python seed.py          # 初始化万人八字库（仅需执行一次）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端启动

```bash
# Windows:
frontend.bat start

# macOS/Linux:
./frontend.sh start
```

访问：**http://localhost:3000**

### 3. 停止服务

```bash
# Windows:
frontend.bat stop

# macOS/Linux:
./frontend.sh stop
```

---

## 六维度合盘算法说明

| 维度 | 权重 | 计算逻辑 |
|------|------|----------|
| 地支合冲 | ⭐⭐⭐⭐⭐ | 六合 +15/对，六冲 -20/对，三合局 +20/局 |
| 五行互补 | ⭐⭐⭐⭐ | 对方缺的五行，我方有则 +分，加权汇总 |
| 天干合 | ⭐⭐⭐ | 五合 +20/对 |
| 日主关系 | ⭐⭐⭐ | 日主天干五合/相生 +分，相克 -分 |
| 纳音 | ⭐⭐ | 纳音五行相同/相生 +分 |
| 神煞 | ⭐⭐ | 红鸾、天喜等吉煞 +分，孤辰、寡宿等凶煞 -分 |

最终汇总为 **0～100 分**，映射为：

| 分数段 | 等级 | 说明 |
|--------|------|------|
| 80+ | 🌟 大吉 | 天作之合，强烈推荐 |
| 65～79 | ✨ 中吉 | 较为合拍，值得发展 |
| 50～64 | 💫 小吉 | 有互补空间，可接触 |
| <50 | 🌑 平平 | 合盘较弱 |

---

## API 文档

### POST `/api/match`

**请求体：**
```json
{
  "birth_year": 1995,
  "birth_month": 6,
  "birth_day": 15,
  "birth_hour": 12,
  "gender": "男",
  "top_n": 5
}
```

**响应体：**
```json
{
  "success": true,
  "matched_users": [
    {
      "id": 42,
      "name": "张三",
      "gender": "女",
      "birth_date": "1996-03-22",
      "birth_hour": 14,
      "total_score": 78.5,
      "dimension_scores": { "地支合冲": 35, "五行互补": 22, ... },
      "level": "中吉",
      "comment": "地支六合，五行互补，较为合拍。",
      "bazi_data": { "tiangan_list": ["甲","乙",...], ... }
    }
  ]
}
```

### GET `/api/health`

健康检查，返回 `{"status": "ok"}`。

---

## 产品演进方向（「星海」完整版设想）

> 当前项目为**功能模拟原型**，完整版「星海」可延展为：

| 阶段 | 功能 |
|------|------|
| MVP（当前） | 个人八字输入 → 万人库匹配 → 合盘结果展示 |
| Phase 2 | 用户注册登录 / 个人八字档案 / 匹配历史 |
| Phase 3 | 双人合盘（输入双方出生信息）/ 合盘报告 PDF 导出 |
| Phase 4 | AI 合盘解读（LLM 生成自然语言报告）/ 社交匹配推荐 |

---

## 开发说明

```bash
# 前端构建（可选，当前为纯静态）
cd frontend
npm install
npm run build        # 输出到 dist/

# 运行测试
cd backend
pytest -v

# 覆盖测试
pytest --cov=backend --cov-report=html
```

---

## 许可证

MIT License —— 仅供学习交流使用，请勿用于商业目的。

> ⚠️ **免责声明**：本工具基于传统八字命理文化，仅供娱乐参考，不构成任何人生决策建议。

---

## 作者

UI Designer × CodeBuddy —— 2026

如有问题或建议，欢迎提 Issue ✨
