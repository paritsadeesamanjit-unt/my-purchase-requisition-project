import streamlit as st
import pandas as pd

# ตั้งค่าหน้าจอและ Theme
st.set_page_config(page_title="Material PR Tracking", layout="wide")

st.title("📑 PR Material Control Dashboard")
st.markdown("ระบบติดตามสถานะการเปิด PR และตรวจสอบวัสดุคงค้าง")

# ฟังก์ชันโหลดข้อมูล (Cache ไว้เพื่อความเร็ว)
@st.cache_data
def load_data(file):
    # อ่านไฟล์ CSV (ข้ามแถวแรกถ้าเป็นหัวกระดาษว่าง)
    df = pd.read_csv(file)
    # ล้างข้อมูลเบื้องต้น: ลบแถวที่ไม่มีเลข PR
    df = df.dropna(subset=['PR NO.'])
    return df

# ส่วนการอัปโหลด (หรือจะทำเป็น Link ถาวรบน GitHub ก็ได้)
uploaded_file = st.sidebar.file_uploader("อัปโหลดไฟล์ PR Control (CSV)", type="csv")

if uploaded_file:
    df = load_data(uploaded_file)
    
    # --- 1. ส่วนสรุปภาพรวม (KPI) ---
    st.subheader("📊 สรุปภาพรวมสถานะ")
    col1, col2, col3, col4 = st.columns(4)
    
    total_items = len(df)
    # สมมติว่าสถานะอยู่ในคอลัมน์ 'REMARK' หรือ 'STATUS'
    # คุณสามารถปรับชื่อคอลัมน์ได้ตามจริง
    pending_items = len(df[df['REMARK'].str.contains('รอ|Pending', na=False, case=False)])
    received_items = len(df[df['REMARK'].str.contains('เข้าแล้ว|Received|ครบ', na=False, case=False)])
    
    col1.metric("รายการ PR ทั้งหมด", f"{total_items} รายการ")
    col2.metric("สถานะรอดำเนินการ", f"{pending_items} รายการ", delta_color="inverse")
    col3.metric("ได้รับของแล้ว", f"{received_items} รายการ")
    col4.metric("งบประมาณรวม", f"{df['AMOUNT'].sum():,.2f} บาท") if 'AMOUNT' in df.columns else None

    st.divider()

    # --- 2. ระบบค้นหาและ Filter ---
    st.subheader("🔍 ค้นหาข้อมูลวัสดุ")
    search_col1, search_col2 = st.columns(2)
    
    with search_col1:
        search_query = st.text_input("ค้นหาจากชื่อวัสดุ หรือ เลขที่ PR")
    with search_col2:
        status_filter = st.multiselect("กรองตามสถานะ (Remark)", options=df['REMARK'].unique())

    # Logic การกรองข้อมูล
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df['ITEM DESCRIPTION'].str.contains(search_query, na=False, case=False) |
            filtered_df['PR NO.'].astype(str).str.contains(search_query, na=False)
        ]
    if status_filter:
        filtered_df = filtered_df[filtered_df['REMARK'].isin(status_filter)]

    # --- 3. ตารางแสดงผล ---
    st.dataframe(
        filtered_df, 
        use_container_width=True,
        column_config={
            "PR NO.": st.column_config.TextColumn("เลขที่ PR"),
            "DATE": st.column_config.DateColumn("วันที่เปิด PR"),
            "QTY": st.column_config.NumberColumn("จำนวน"),
        }
    )

    # ปุ่ม Export เฉพาะที่ Filter แล้ว
    csv_data = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Download filtered data", csv_data, "filtered_pr.csv", "text/csv")

else:
    st.info("👈 กรุณาอัปโหลดไฟล์ 'PR of Material Control' ที่แถบเมนูด้านซ้ายเพื่อเริ่มการวิเคราะห์")