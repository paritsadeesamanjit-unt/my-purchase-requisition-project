import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="PR Tracking Pro", layout="wide")
st.title("📦 PR Material Control Tracking")

uploaded_file = st.file_uploader("อัปโหลดไฟล์ PR ของคุณ (CSV หรือ Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # --- ส่วนการอ่านไฟล์แบบยืดหยุ่น ---
        if uploaded_file.name.endswith('.csv'):
            # ลองอ่านหลายๆ Encoding ที่คนไทยชอบใช้
            for enc in ['utf-8-sig', 'cp874', 'tis-620']:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=enc)
                    break
                except:
                    continue
        else:
            df = pd.read_excel(uploaded_file)

        # --- ส่วนล้างข้อมูล (Data Cleaning) ---
        # 1. ลบแถวที่ว่างทั้งหมด
        df = df.dropna(how='all').reset_index(drop=True)
        
        # 2. ล้างชื่อคอลัมน์ (ลบช่องว่างหัว-ท้าย)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # 3. ตรวจสอบว่ามีข้อมูลไหม
        if not df.empty:
            st.success(f"✅ โหลดข้อมูลสำเร็จ! พบ {len(df)} รายการ")
            
            # สร้างตัวกรองข้อมูล (Sidebar)
            st.sidebar.header("Filter Options")
            all_remarks = df['REMARK'].unique() if 'REMARK' in df.columns else ['N/A']
            selected_status = st.sidebar.multiselect("เลือกสถานะ (Remark)", all_remarks)

            # แสดงตาราง
            st.subheader("📋 รายละเอียดวัสดุ")
            
            # ค้นหาแบบ Real-time
            search = st.text_input("🔍 ค้นหาชื่อวัสดุ หรือ เลขที่ PR")
            
            display_df = df.copy()
            if search:
                # ค้นหาทุกคอลัมน์ที่เกี่ยวข้อง
                mask = display_df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
                display_df = display_df[mask]
            
            if selected_status:
                display_df = display_df[display_df['REMARK'].isin(selected_status)]

            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("⚠️ ไฟล์ว่างเปล่า หรือรูปแบบไม่ถูกต้อง")

    except Exception as e:
        st.error(f"❌ ระบบขัดข้อง: {str(e)}")
        st.info("💡 คำแนะนำ: หากเป็น CSV ลอง Save as จาก Excel เป็น 'CSV UTF-8 (Comma delimited)'")