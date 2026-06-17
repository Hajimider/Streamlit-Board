import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from config import DB_CONFIG
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(
    page_title="销售数据分析看板",
    page_icon="📊",
    layout="wide"
)


# 缓存数据库连接
@st.cache_resource
def get_engine():
    url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
    return create_engine(url)


# 缓存数据查询（避免重复查询）
@st.cache_data(ttl=300)  # 缓存5分钟
def load_data(start_date, end_date, channels):
    engine = get_engine()

    # 构建渠道筛选条件
    channel_placeholder = ','.join([f"'{c}'" for c in channels])

    sql = f"""
    SELECT 
        DATE(order_date) as order_date,
        channel,
        COUNT(DISTINCT order_id) as order_cnt,
        SUM(amount) as gmv,
        COUNT(DISTINCT user_id) as user_cnt,
        AVG(amount) as avg_order_value
    FROM orders
    WHERE order_date BETWEEN %s AND %s
        AND channel IN ({channel_placeholder})
    GROUP BY DATE(order_date), channel
    ORDER BY order_date
    """

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=(start_date, end_date))

    return df


def main():
    st.title("📊 销售数据分析看板")
    st.markdown("---")

    # ==================== 侧边栏筛选 ====================
    st.sidebar.header("🔍 筛选条件")

    # 日期范围
    end_date = datetime.now().date() - timedelta(days=1)  # 默认昨天
    start_date = end_date - timedelta(days=30)

    date_range = st.sidebar.date_input(
        "日期范围",
        value=(start_date, end_date),
        max_value=datetime.now().date()
    )

    # 渠道多选
    channels = st.sidebar.multiselect(
        "渠道",
        options=['app', 'h5', 'pc'],
        default=['app', 'h5', 'pc']
    )

    # 指标选择
    metric = st.sidebar.selectbox(
        "核心指标",
        options=['gmv', 'order_cnt', 'user_cnt', 'avg_order_value'],
        format_func=lambda x: {
            'gmv': 'GMV (万元)',
            'order_cnt': '订单数',
            'user_cnt': '用户数',
            'avg_order_value': '客单价'
        }[x]
    )

    if len(date_range) != 2:
        st.warning("请选择完整的日期范围")
        return

    if not channels:
        st.warning("请至少选择一个渠道")
        return

    start_date = date_range[0].strftime('%Y-%m-%d')
    end_date = date_range[1].strftime('%Y-%m-%d')

    # ==================== 加载数据 ====================
    with st.spinner("数据加载中..."):
        df = load_data(start_date, end_date, channels)

    if df.empty:
        st.warning("所选日期范围内无数据")
        return

    # ==================== 核心指标卡片 ====================
    st.subheader("📈 核心指标概览")

    col1, col2, col3, col4 = st.columns(4)

    total_gmv = df['gmv'].sum()
    total_orders = df['order_cnt'].sum()
    total_users = df['user_cnt'].sum()
    avg_price = total_gmv / total_orders if total_orders > 0 else 0

    col1.metric("总 GMV", f"¥{total_gmv / 10000:.1f}万")
    col2.metric("总订单数", f"{total_orders:,}")
    col3.metric("总用户数", f"{total_users:,}")
    col4.metric("客单价", f"¥{avg_price:.0f}")

    st.markdown("---")

    # ==================== 趋势图（双轴） ====================
    st.subheader("📉 核心指标趋势")

    # 按日期聚合
    daily_df = df.groupby('order_date').agg({
        'gmv': 'sum',
        'order_cnt': 'sum',
        'user_cnt': 'sum'
    }).reset_index()

    # 双轴图
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=daily_df['order_date'],
        y=daily_df['order_cnt'],
        name='订单数',
        yaxis='y',
        line=dict(color='steelblue', width=2),
        marker=dict(size=6)
    ))

    fig.add_trace(go.Scatter(
        x=daily_df['order_date'],
        y=daily_df['gmv'] / 10000,
        name='GMV (万元)',
        yaxis='y2',
        line=dict(color='coral', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title='订单数 & GMV 趋势',
        xaxis=dict(title='日期'),
        yaxis=dict(
            title='订单数',
            title_font=dict(color='steelblue'),  # titlefont -> title_font
            tickfont=dict(color='steelblue')
        ),
        yaxis2=dict(
            title='GMV (万元)',
            title_font=dict(color='coral'),  # titlefont -> title_font
            tickfont=dict(color='coral'),
            overlaying='y',
            side='right'
        ),
        legend=dict(x=0.02, y=0.98),
        height=450,
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==================== 渠道分析 ====================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🥧 渠道 GMV 占比")
        channel_gmv = df.groupby('channel')['gmv'].sum().reset_index()
        fig_pie = px.pie(
            channel_gmv,
            values='gmv',
            names='channel',
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("📊 渠道 GMV 趋势")
        fig_line = px.line(
            df,
            x='order_date',
            y='gmv',
            color='channel',
            markers=True,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_line.update_layout(
            xaxis_title='日期',
            yaxis_title='GMV',
            height=400,
            legend_title='渠道'
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # ==================== 数据明细 ====================
    st.markdown("---")
    with st.expander("📋 查看数据明细"):
        st.dataframe(df, use_container_width=True)

        # 下载按钮
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 下载 CSV",
            data=csv,
            file_name=f"sales_data_{start_date}_{end_date}.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()