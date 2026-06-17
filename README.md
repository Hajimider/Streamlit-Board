```markdown
# 📊 销售数据分析看板

基于 Streamlit + MySQL 的交互式销售数据可视化工具。

---

## ✨ 功能

- 核心指标概览（GMV、订单数、用户数、客单价）
- 订单数与 GMV 双轴趋势图
- 渠道 GMV 占比饼图
- 渠道 GMV 趋势图
- 日期范围 + 渠道筛选
- CSV 数据导出

---

## 🚀 快速开始

### 1. 安装依赖

​```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

执行 `recouse_data.sql` 创建表并生成模拟数据：

```bash
mysql -u root -p < recouse_data.sql
```

### 3. 修改数据库配置

编辑 `config.py`，填写你的 MySQL 密码：

```python
DB_CONFIG = {
    'password': '你的密码',  # 修改这里
}
```

### 4. 运行应用

```bash
streamlit run app.py
```

浏览器访问 `http://localhost:8501`

---

## 📁 文件说明

| 文件               | 说明            |
| ------------------ | --------------- |
| `app.py`           | 主程序          |
| `config.py`        | 数据库配置      |
| `requirements.txt` | Python 依赖     |
| `recouse_data.sql` | 建表 + 模拟数据 |

---

## ☁️ 部署到 Streamlit Cloud

1. 将代码上传到 GitHub 仓库
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 选择仓库，点击 Deploy

⚠️ 云端部署需要公网可访问的数据库，建议使用 Supabase 或云数据库。

---

## 📦 依赖

- streamlit >= 1.28.0
- pandas >= 2.0.0
- plotly >= 5.14.0
- sqlalchemy >= 2.0.0
- pymysql >= 1.0.0