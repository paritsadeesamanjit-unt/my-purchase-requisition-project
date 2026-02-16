import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Setup ---
st.set_page_config(page_title="Material PR Tracking", layout="wide", page_icon="📦")

# ฟังก์ชันช่วยหาชื่อคอลัมน์ที่ใกล้เคียงที่สุด (ป้องกัน KeyError)
def get_col(df, possible_names):
    for name in possible_names:
        if name in df.columns:
            return name
    return None

@st.cache_data
def load_data():
    # พยายามหาไฟล์ CSV ในเครื่อง
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not files:
        return None
    
    # เลือกไฟล์ที่น่าจะเป็นฐานข้อมูลหลัก (เลือกไฟล์ที่มีคำว่า Sheet1 หรือไฟล์ที่ใหญ่ที่สุด)
    target_file = files[0]
    for f in files:
        if "Sheet1" in f:
            target_file = f
            break
            
    df = pd.read_csv(target_file, encoding='utf-8-sig')
    df.columns = df.columns.str.strip() # ลบช่องว่างที่ชื่อคอลัมน์
    return df

# --- เริ่มโหลดข้อมูล ---
df_raw = load_data()

if df_raw is None:
    st.error("❌ ไม่พบไฟล์ข้อมูล CSV ใน Repository! กรุณาอัปโหลดไฟล์เข้าไปใน GitHub ด้วยนะครับ")
    st.stop()

# ทำ Mapping คอลัมน์สำคัญ (เพื่อให้โค้ดไม่พังถ้าชื่อหัวตารางเปลี่ยน)
col_pr = get_col(df_raw, ['Purchase Requisition', 'PR NO.', '請購單號', 'PR Number'])
col_date = get_col(df_raw, ['Requisition date', 'DATE', '日期', 'Date'])
col_item = get_col(df_raw, ['Short Text', 'ITEM DESCRIPTION', '品名規格', 'Material Name'])
col_po = get_col(df_raw, ['Purchase order', 'PO NO.', 'PO Number'])
col_status = get_col(df_raw, ['Current Status', 'Remark', 'Status', 'REMARK'])
col_qty = get_col(df_raw, ['Quantity requested', 'QTY', '數量', 'Quantity'])

# --- Sidebar Menu ---
st.sidebar.title("🏢 Material Control")
menu = st.sidebar.selectbox("เมนูการใช้งาน", ["📊 Dashboard", "🔍 PR Status Details", "📅 Daily Movement"])

# --- 1. หน้า Dashboard ---
if menu == "📊 Dashboard":
    st.header("📊 ภาพรวมสถานะวัสดุ")
    
    # คำนวณสถานะพื้นฐาน
    total_pr = len(df_raw)
    has_po = df_raw[col_po].notnull().sum() if col_po else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("จำนวน PR ทั้งหมด", f"{total_pr} รายการ")
    c2.metric("เปิด PO แล้ว", f"{has_po} รายการ")
    c3.metric("รอดำเนินการ", f"{total_pr - has_po} รายการ", delta_color="inverse")

    st.divider()
    
    # กราฟวงกลมแสดงสัดส่วน
    if col_po:
        df_raw['Status_Group'] = df_raw[col_po].apply(lambda x: 'PO Issued' if pd.notnull(x) else 'Pending PR')
        fig = px.pie(df_raw, names='Status_Group', title="สัดส่วนการดำเนินงาน (PR vs PO)",
                     color_discrete_sequence=['#2ecc71', '#e74c3c'])
        st.plotly_chart(fig, use_container_width=True)

# --- 2. หน้า PR Status Details ---
elif menu == "🔍 PR Status Details":
    st.header("🔍 ตรวจสอบรายละเอียดรายตัว")
    search = st.text_input("พิมพ์ชื่อวัสดุ หรือ เลขที่ PR เพื่อค้นหา...")
    
    if search:
        mask = df_raw.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
        result_df = df_raw[mask]
    else:
        result_df = df_raw

    st.dataframe(result_df, use_container_width=True)

# --- 3. หน้า Daily Movement ---
elif menu == "📅 Daily Movement":
    st.header("📅 รายงานความเคลื่อนไหวประจำวัน")
    if col_date:
        # แปลงเป็น datetime
        df_raw[col_date] = pd.to_datetime(df_raw[col_date], errors='coerce')
        latest_date = df_raw[col_date].max()
        
        selected_date = st.date_input("เลือกวันที่", value=latest_date)
        daily_df = df_raw[df_raw[col_date].dt.date == selected_date]
        
        if not daily_df.empty:
            st.success(f"พบความเคลื่อนไหว {len(daily_df)} รายการ")
            st.table(daily_df[[col_pr, col_item, col_qty]])
        else:
            st.info("ไม่มีรายการในวันที่เลือก")
    else:
        st.warning("ในไฟล์ไม่มีคอลัมน์ 'วันที่' จึงไม่สามารถดูรายงานรายวันได้")