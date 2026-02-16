import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- การตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Material Control Dashboard", layout="wide", page_icon="📦")

# --- ฟังก์ชันโหลดข้อมูลแบบปลอดภัย ---
@st.cache_data
def load_data():
    # พยายามหาไฟล์ในชื่อที่กำหนด
    file_name = "PR_data.csv" 
    try:
        # อ่านไฟล์พร้อมรองรับภาษาไทย
        df = pd.read_csv(file_name, encoding='utf-8-sig')
        
        # ล้างช่องว่างในชื่อคอลัมน์
        df.columns = df.columns.str.strip()
        
        # แปลงวันที่ (รองรับรูปแบบจากไฟล์ของคุณ)
        df['Requisition date'] = pd.to_datetime(df['Requisition date'], errors='coerce')
        df['Received Date'] = pd.to_datetime(df['Received Date'], errors='coerce')
        
        # สร้างสถานะจำลอง (Logic: ถ้ามี Received Date = สำเร็จ, ถ้ามี PO = เปิด PO แล้ว, อื่นๆ = รอ)
        def determine_status(row):
            if pd.notnull(row.get('Received Date')): return "✅ Received"
            if pd.notnull(row.get('Purchase order')): return "🚚 PO Issued"
            return "⏳ Pending PR"
        
        df['Current Status'] = df.apply(determine_status, axis=1)
        return df
    except Exception as e:
        return str(e)

# --- เริ่มการทำงาน ---
data = load_data()

# ตรวจสอบ Error เบื้องต้น
if isinstance(data, str):
    st.error(f"❌ ระบบหาไฟล์ 'PR_data.csv' ไม่เจอ หรือไฟล์มีปัญหา")
    st.info(f"รายละเอียด Error: {data}")
    st.stop()

df = data

# --- Sidebar Menu (ใส่ไอคอนสวยๆ) ---
st.sidebar.markdown("## ⚙️ Main Menu")
menu = st.sidebar.radio(
    "เลือกดูข้อมูล:",
    ["📊 Dashboard Overview", "🔍 PR/PO Status", "📅 Daily Movement"],
    index=0
)

# ---------------------------------------------------------
# หน้า 1: Dashboard ข้อมูลทั้งหมด
# ---------------------------------------------------------
if menu == "📊 Dashboard Overview":
    st.title("📊 PR Material Control Overview")
    
    # ส่วนของ KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total PR", len(df))
    with c2:
        pending = len(df[df['Current Status'] == "⏳ Pending PR"])
        st.metric("Pending PR", pending, delta="-รอดำเนินการ", delta_color="inverse")
    with c3:
        received = len(df[df['Current Status'] == "✅ Received"])
        st.metric("Received", received)
    with c4:
        total_val = df['Total Value'].sum() if 'Total Value' in df.columns else 0
        st.metric("Total Value", f"฿{total_val:,.0f}")

    st.divider()

    # กราฟแสดงสัดส่วน
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        fig_pie = px.pie(df, names='Current Status', title="Status Distribution", 
                         color='Current Status', color_discrete_map={
                             "✅ Received": "#2ecc71", "🚚 PO Issued": "#f1c40f", "⏳ Pending PR": "#e74c3c"
                         })
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_chart2:
        # สรุปตามกลุ่มผู้ขอซื้อ (Requisitioner)
        top_req = df['Requisitioner'].value_counts().head(5).reset_index()
        fig_bar = px.bar(top_req, x='count', y='Requisitioner', orientation='h', title="Top 5 Requisitioners")
        st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------
# หน้า 2: Status รายละเอียดของ PR
# ---------------------------------------------------------
elif menu == "🔍 PR/PO Status":
    st.title("🔍 รายละเอียดสถานะการจัดซื้อ")
    
    # ส่วนค้นหา
    search_term = st.text_input("ค้นหาวัสดุ หรือ เลขที่ PR/PO...", placeholder="พิมพ์ชื่อวัสดุที่นี่")
    
    # ฟิลเตอร์ตามสถานะ
    status_choice = st.multiselect("กรองตามสถานะ:", options=df['Current Status'].unique(), default=df['Current Status'].unique())
    
    # กรองข้อมูล
    mask = df['Current Status'].isin(status_choice)
    if search_term:
        mask = mask & (df['Short Text'].str.contains(search_term, case=False, na=False) | 
                       df['Purchase Requisition'].astype(str).str.contains(search_term))
    
    display_df = df[mask]
    
    # ปรับแต่งตารางให้สวยงาม
    st.dataframe(
        display_df[['Requisition date', 'Purchase Requisition', 'Purchase order', 'Short Text', 'Quantity requested', 'Unit ', 'Current Status', 'Vendor']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Current Status": st.column_config.TextColumn("Status", width="medium"),
            "Purchase Requisition": st.column_config.TextColumn("PR No."),
            "Purchase order": st.column_config.TextColumn("PO No.")
        }
    )

# ---------------------------------------------------------
# หน้า 3: รายงานความเคลื่อนไหวประจำวัน
# ---------------------------------------------------------
elif menu == "📅 Daily Movement":
    st.title("📅 รายงานความเคลื่อนไหว")
    
    # เลือกวันที่
    today = datetime.now().date()
    select_date = st.date_input("เลือกวันที่เปิด PR:", value=df['Requisition date'].max())
    
    report_df = df[df['Requisition date'].dt.date == select_date]
    
    if not report_df.empty:
        st.success(f"พบรายการในวันที่ {select_date} ทั้งหมด {len(report_df)} รายการ")
        
        # แสดงรายการแบบ Card สั้นๆ
        for idx, row in report_df.iterrows():
            with st.expander(f"📌 PR: {row['Purchase Requisition']} - {row['Short Text']}"):
                col_a, col_b = st.columns(2)
                col_a.write(f"**จำนวน:** {row['Quantity requested']} {row['Unit ']}")
                col_a.write(f"**ผู้ขอซื้อ:** {row['Requisitioner']}")
                col_b.write(f"**สถานะปัจจุบัน:** {row['Current Status']}")
                col_b.write(f"**Vendor:** {row['Vendor']}")
    else:
        st.warning("ไม่มีรายการเปิด PR ในวันที่เลือก")