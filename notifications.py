
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

def check_notifications(df):
    """فحص وعرض التنبيهات"""
    notifications = []
    
    # التحقق من المعلومات العامة للموظفين
    for _, employee in df.iterrows():
        # التحقق من اكتمال البيانات الأساسية
        required_fields = ['name', 'employee_id', 'department', 'position']
        column_mapping = {
            'name': 'الاسم',
            'employee_id': 'الرقم الوظيفي',
            'department': 'الادارة',
            'position': 'الوظيفة'
        }
        
        missing_fields = [column_mapping[field] for field in required_fields if pd.isna(employee.get(field, None))]
        
        if missing_fields:
            emp_name = employee.get('name', 'غير معروف')
            emp_id = employee.get('employee_id', 'غير معروف')
            notifications.append({
                'نوع': 'بيانات ناقصة',
                'رسالة': f"الموظف {emp_name} - {emp_id} يحتاج لاستكمال: {', '.join(missing_fields)}",
                'أولوية': 'عالية'
            })
        
        # التحقق من العمر إذا كان تاريخ الميلاد متوفر
        if 'birth_date' in df.columns and pd.notna(employee['birth_date']):
            birth_date = pd.to_datetime(employee['birth_date'])
            age = (datetime.now() - birth_date).days / 365.25
            if age >= 60:
                notifications.append({
                    'نوع': 'تنبيه سن التقاعد',
                    'رسالة': f"الموظف {employee.get('name', 'غير معروف')} سيبلغ/بلغ سن التقاعد",
                    'أولوية': 'متوسطة'
                })

    return notifications

def display_notifications():
    """عرض واجهة التنبيهات"""
    st.markdown("""
    <style>
    .notification-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-right: 4px solid #0e4c92;
    }
    .notification-high {
        border-right-color: #dc3545;
        background-color: #fff5f5;
    }
    .notification-medium {
        border-right-color: #ffc107;
        background-color: #fffbf0;
    }
    .notification-title {
        font-weight: bold;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 التنبيهات والإشعارات")
    
    if 'df' in st.session_state and not st.session_state.df.empty:
        notifications = check_notifications(st.session_state.df)
        
        if notifications:
            for notif in notifications:
                urgency_class = "notification-high" if notif['أولوية'] == 'عالية' else "notification-medium"
                
                st.markdown(f"""
                <div class="notification-card {urgency_class}">
                    <div class="notification-title">{notif['نوع']}</div>
                    <p>{notif['رسالة']}</p>
                    <small>الأولوية: {notif['أولوية']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🎉 لا توجد تنبيهات حالياً - جميع البيانات مكتملة")
    else:
        st.warning("⚠️ لا توجد بيانات متاحة للتحليل")

