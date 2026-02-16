import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="Material Control System", layout="wide", page_icon="📦")

# --- Custom CSS เพื่อความสวยงาม ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- ฟังก์ชันจัดการข้อมูล ---
@st.cache_data
def load_and_clean_data():
    # โหลดไฟล์ (ใช้ชื่อไฟล์ที่คุณส่งมาล่าสุด)
    df = pd.read_csv("PR of Material Control_16.02.26.XLSX - Sheet1.csv")
    
    # แปลงวันที่
    df['Requisition date'] = pd.to_datetime(df['Requisition date'], errors='coerce')
    df['Received Date'] = pd.to_datetime(df['Received Date'], errors='coerce')
    
    # คำนวณสถานะ (Logic: Received > PO Issued > PR Pending)
    def check_status(row):
        if pd.notnull(row['Received Date']):
            return "✅ Received"
        elif pd.notnull(row['Purchase order']):
            return "🚚 PO Issued"
        else:
            return "⏳ PR Pending"
            
    df['Current Status'] = df.apply(check_status, axis=1)
    return df

try:
    df = load_and_clean_data()
except:
    st.error("ไม่พบไฟล์ข้อมูล กรุณาตรวจสอบชื่อไฟล์ในระบบ")
    st.stop()

# --- Sidebar Menu ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2271/2271068.png", width=100)
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "เลือกหน้าการทำงาน",
    ["📊 Dashboard Overview", "🔍 PR Status Details", "📅 Daily Movement"],
    index=0
)

# ---------------------------------------------------------
# หน้า 1: Dashboard ข้อมูลทั้งหมด
# ---------------------------------------------------------
if menu == "📊 Dashboard Overview":
    st.header("📊 PR Material Dashboard")
    
    # แถวที่ 1: Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total PRs", len(df))
    m2.metric("Pending PO", len(df[df['Current Status'] == "⏳ PR Pending"]))
    m3.metric("Received", len(df[df['Current Status'] == "✅ Received"]))
    m4.metric("Total Value", f"฿{df['Total Value'].sum():,.2f}")

    st.divider()

    # แถวที่ 2: Charts
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📦 Status Distribution")
        fig_pie = px.pie(df, names='Current Status', color='Current Status',
                         color_discrete_map={'✅ Received':'#28a745', '🚚 PO Issued':'#ffc107', '⏳ PR Pending':'#dc3545'})
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with c2:
        st.subheader("👤 Top Requisitioners")
        top_req = df['Requisitioner'].value_counts().head(5).reset_index()
        fig_bar = px.bar(top_req, x='count', y='Requisitioner', orientation='h', 
                         labels={'count':'PR Count'}, color='Requisitioner')
        st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------
# หน้า 2: Status รายละเอียดของ PR
# ---------------------------------------------------------
elif menu == "🔍 PR Status Details":
    st.header("🔍 Track Individual PR Status")
    
    # ตัวกรองข้อมูล
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("ค้นหาเลขที่ PR, PO หรือ ชื่อวัสดุ", placeholder="Ex. 70185003...")
    with col2:
        status_filter = st.multiselect("กรองตามสถานะ", options=df['Current Status'].unique(), default=df['Current Status'].unique())

    # กรองข้อมูล
    filtered_df = df[df['Current Status'].isin(status_filter)]
    if search:
        filtered_df = filtered_df[
            filtered_df['Purchase Requisition'].astype(str).str.contains(search) | 
            filtered_df['Short Text'].str.contains(search, case=False, na=False) |
            filtered_df['Purchase order'].astype(str).str.contains(search)
        ]

    # แสดงผลในรูปแบบตารางสวยงาม
    st.dataframe(
        filtered_df[['Requisition date', 'Purchase Requisition', 'Purchase order', 'Short Text', 'Quantity requested', 'Unit ', 'Current Status', 'Vendor']],
        use_container_width=True,
        hide_index=True
    )

    # รายละเอียดเชิงลึกเมื่อคลิกเลือก (Optional)
    if not filtered_df.empty:
        with st.expander("📝 ดูรายละเอียดขั้นตอนปัจจุบัน"):
            selected_pr = filtered_df.iloc[0] # ตัวอย่างแสดงรายการแรกที่ค้นเจอ
            st.write(f"**Material:** {selected_pr['Short Text']}")
            step = selected_pr['Current Status']
            if step == "⏳ PR Pending":
                st.info("💡 ขั้นตอน: รอจัดซื้อเปิด PO (Pending at Purchasing)")
            elif step == "🚚 PO Issued":
                st.warning(f"💡 ขั้นตอน: รอส่งมอบจาก Vendor: {selected_pr['Vendor']}")
            else:
                st.success(f"💡 ขั้นตอน: วัสดุเข้าคลังเรียบร้อยเมื่อ {selected_pr['Received Date']}")

# ---------------------------------------------------------
# หน้า 3: รายงานความเคลื่อนไหวประจำวัน
# ---------------------------------------------------------
elif menu == "📅 Daily Movement":
    st.header("📅 Daily PR Movement Report")
    
    target_date = st.date_input("เลือกวันที่ต้องการดูรายงาน", value=df['Requisition date'].max())
    
    # กรองข้อมูลตามวันที่เลือก
    day_df = df[df['Requisition date'].dt.date == target_date]
    
    if day_df.empty:
        st.warning(f"ไม่มีความเคลื่อนไหวในวันที่ {target_date}")
    else:
        st.subheader(f"สรุปรายการเปิด PR ประจำวันที่ {target_date}")
        
        # แสดงตารางสรุป
        st.table(day_df[['Purchase Requisition', 'Short Text', 'Quantity requested', 'Requisitioner']])
        
        # สรุปยอดเงินรายวัน
        daily_sum = day_df['Total Value'].sum()
        st.info(f"💰 ยอดงบประมาณรวมประจำวัน: **{daily_sum:,.2f} บาท**")