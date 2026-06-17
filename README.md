# 📊 销售数据分析看板

基于 Streamlit + SQLite 的交互式销售数据可视化工具，部署后可生成公网链接，分享给团队成员随时查看。

---

## ✨ 功能

- 核心指标概览（GMV、订单数、用户数、客单价）
- 订单数与 GMV 双轴趋势图
- 渠道 GMV 占比饼图
- 渠道 GMV 趋势图
- 日期范围 + 渠道筛选
- CSV 数据导出

---

## 🚀 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

浏览器访问 `http://localhost:8501`

---

## ☁️ 部署分享（推荐）

部署到 Streamlit Cloud，生成公网链接，**无需对方安装任何软件**，打开浏览器即可使用。

### 部署步骤

1. 将项目文件（含 `sales_data.db`）上传到 GitHub 仓库
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 用 GitHub 账号登录，点击 "New app"
4. 选择你的仓库和分支，主文件选 `app.py`
5. 点击 "Deploy"

### 分享链接

部署成功后，会生成一个公网链接，格式为：

```
https://你的应用名.streamlit.app
```

把链接发给任何人，打开就能用。

---

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `app.py` | 主程序 |
| `requirements.txt` | Python 依赖 |
| `sales_data.db` | SQLite 数据库（含模拟数据） |

---

## 📦 依赖

- streamlit >= 1.28.0
- pandas >= 2.0.0
- plotly >= 5.14.0
- sqlalchemy >= 2.0.0
