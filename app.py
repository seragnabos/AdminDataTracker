import streamlit as st
import pandas as pd
import numpy as np
import base64
import os
from datetime import datetime
from auth import init_auth, show_login, show_admin_panel, login_required, admin_required, is_admin
from utils import load_excel_file, save_excel_file, apply_filters
from components import display_data_table, create_search_filters, create_export_section
from database import init_db, get_all_employees
from db_admin import show_db_admin
from dashboard import create_interactive_dashboard
from advanced_analytics import display_advanced_analytics

# Initialize authentication
init_auth()

# Set page configuration
st.set_page_config(
    page_title="نظام إدارة بيانات الموظفين",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Improved Arabic RTL support with custom HTML/CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');

    * {
        font-family: 'Tajawal', sans-serif;
    }

    .rtl {
        direction: rtl;
        text-align: right;
    }

    .centered {
        text-align: center;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Tajawal', sans-serif;
        font-weight: 700;
    }

    .stButton>button {
        font-family: 'Tajawal', sans-serif;
        font-weight: 500;
    }

    div[data-testid="stVerticalBlock"] {
        direction: rtl;
    }

    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
    }

    .header-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Logo and App title in a header section
def get_image_as_base64(file_path):
    with open(file_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_image_as_base64("attached_assets/logo.png")

st.markdown(f"""
<div class="header-container">
    <div class="logo-container">
        <img src="data:image/png;base64,{logo_base64}" width="200">
    </div>
    <h1 class="centered">نظام إدارة بيانات الموظفين</h1>
</div>
""", unsafe_allow_html=True)

# Initialize session state for storing dataframe
if 'df' not in st.session_state:
    st.session_state.df = None
if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = None
if 'columns_mapping' not in st.session_state:
    # Define mapping between English column names and Arabic display names
    st.session_state.columns_mapping = {
        'name': 'الاسم',
        'employee_id': 'الرقم الوظيفي',
        'national_id': 'الرقم الوطني',
        'birth_date': 'تاريخ الميلاد',
        'birthplace': 'مكان الميلاد',
        'education': 'المؤهل العلمي',
        'position': 'الوظيفة',
        'job_category': 'فئة الوظيفة',
        'department': 'الادارة',
        'affiliation': 'التابعية',
        'workplace': 'موقع العمل'
    }
    # Reverse mapping for internal operations
    st.session_state.reverse_mapping = {v: k for k, v in st.session_state.columns_mapping.items()}

# تحميل البيانات بشكل تلقائي من ملف الإكسل
def load_default_data():
    """تحميل البيانات من ملف الإكسل الافتراضي"""
    sample_file = "attached_assets/01.xlsx"
    try:
        if os.path.exists(sample_file):
            df = load_excel_file(sample_file)
            if df is not None:
                st.session_state.df = df
                st.session_state.filtered_df = df.copy()
                return True
    except Exception as e:
        st.error(f'حدث خطأ أثناء تحميل ملف البيانات: {str(e)}')
    return False

# Load data automatically on startup if not already loaded
if 'df' not in st.session_state or st.session_state.df is None:
    load_default_data()

# Sidebar with improved styling
with st.sidebar:
    if not st.session_state.get('logged_in', False):
        show_login()
        st.stop()
    else:
        st.write(f"مرحباً بك، {st.session_state.current_user}")
        if is_admin():
            if st.button("لوحة التحكم"):
                st.session_state.show_admin = True
                st.rerun()
        if st.button("تسجيل خروج"):
            st.session_state.clear()
            st.rerun()

    if st.session_state.get('show_admin', False) and is_admin():
        show_admin_panel()
        st.stop()
    # Improved sidebar styling
    st.markdown("""
    <style>
    .sidebar-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .sidebar-title {
        color: #0e4c92;
        font-weight: bold;
        margin-bottom: 15px;
        font-size: 1.2rem;
        text-align: center;
        border-bottom: 2px solid #0e4c92;
        padding-bottom: 5px;
    }
    .stats-container {
        background-color: #e9ecef;
        padding: 10px;
        border-radius: 5px;
        margin-top: 15px;
    }
    .stats-item {
        margin-bottom: 5px;
        font-weight: 500;
        font-size: 0.9rem;
        text-align: right;
    }
    .stats-value {
        font-weight: bold;
        color: #0e4c92;
    }
    </style>
    """, unsafe_allow_html=True)

    # File info section
    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown('<h3 class="sidebar-title">معلومات الملف</h3>', unsafe_allow_html=True)

    if st.session_state.df is not None:
        st.success("تم تحميل البيانات بنجاح")
        st.markdown(f'<p class="stats-item">اسم الملف: <span class="stats-value">attached_assets/01.xlsx</span></p>', unsafe_allow_html=True)

        # Get file modification time
        file_time = os.path.getmtime("attached_assets/01.xlsx")
        file_time_str = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
        st.markdown(f'<p class="stats-item">تاريخ آخر تعديل: <span class="stats-value">{file_time_str}</span></p>', unsafe_allow_html=True)
    else:
        st.error("فشل في تحميل البيانات")

        # Add a retry button
        if st.button("إعادة تحميل البيانات"):
            load_default_data()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Statistics section
    if st.session_state.df is not None:
        st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sidebar-title">إحصائيات عامة</h3>', unsafe_allow_html=True)

        st.markdown('<div class="stats-container">', unsafe_allow_html=True)

        # Employee count
        st.markdown(f'<p class="stats-item">عدد الموظفين: <span class="stats-value">{len(st.session_state.df)}</span></p>', unsafe_allow_html=True)

        # Departments count
        if 'department' in st.session_state.df.columns:
            dept_counts = st.session_state.df['department'].value_counts()
            st.markdown(f'<p class="stats-item">عدد الإدارات: <span class="stats-value">{len(dept_counts)}</span></p>', unsafe_allow_html=True)

        # Job categories count
        if 'job_category' in st.session_state.df.columns:
            job_cat_counts = st.session_state.df['job_category'].value_counts()
            st.markdown(f'<p class="stats-item">عدد الفئات الوظيفية: <span class="stats-value">{len(job_cat_counts)}</span></p>', unsafe_allow_html=True)

        # Workplaces count
        if 'workplace' in st.session_state.df.columns:
            workplace_counts = st.session_state.df['workplace'].value_counts()
            st.markdown(f'<p class="stats-item">عدد مواقع العمل: <span class="stats-value">{len(workplace_counts)}</span></p>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Initialize the database
if 'db_initialized' not in st.session_state:
    if os.environ.get("DATABASE_URL"):
        success = init_db()
        if success:
            st.session_state.db_initialized = True
        else:
            st.session_state.db_initialized = False
    else:
        st.session_state.db_initialized = False

# Main navigation
if 'current_view' not in st.session_state:
    st.session_state.current_view = "main"

# Main area navigation
main_tabs = ["البحث بالرقم الوظيفي", "عرض البيانات", "البحث والتصفية", "لوحة التحليلات التفاعلية", "الهيكل التنظيمي", "التصدير والتقارير"]
if st.session_state.db_initialized:
    main_tabs.append("إدارة قاعدة البيانات")

# Add database admin button to sidebar if database is initialized
if st.session_state.db_initialized:
    with st.sidebar:
        st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sidebar-title">مصدر البيانات</h3>', unsafe_allow_html=True)

        data_source = st.radio(
            "اختر مصدر البيانات للعرض",
            ["الملف المحمل", "قاعدة البيانات"],
            index=0,
            key="data_source"
        )

        if data_source == "قاعدة البيانات":
            # Use data from database
            try:
                db_df = get_all_employees()
                if not db_df.empty:
                    st.session_state.df = db_df
                    st.session_state.filtered_df = db_df.copy()
                    st.success("تم تحميل البيانات من قاعدة البيانات")
                else:
                    st.warning("لا توجد بيانات في قاعدة البيانات")
                    # Switch back to file mode if no data
                    st.session_state.data_source = "الملف المحمل"
            except Exception as e:
                st.error(f"حدث خطأ أثناء قراءة قاعدة البيانات: {str(e)}")
                st.session_state.data_source = "الملف المحمل"

        st.markdown('</div>', unsafe_allow_html=True)

# Main area
if st.session_state.df is not None:
    # Create tabs for different functionalities
    tabs = st.tabs(main_tabs)

    with tabs[0]:
        st.markdown("""
        <style>
        .employee-search {
            background-color: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            border: 2px solid #0e4c92;
            margin-bottom: 20px;
        }
        .search-title {
            color: #0e4c92;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }
        .search-instruction {
            color: #6c757d;
            text-align: center;
            margin-bottom: 15px;
            font-size: 16px;
        }
        .employee-card {
            background-color: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin: 25px 0;
            border-right: 5px solid #0e4c92;
        }
        .info-section {
            margin: 15px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        .info-title {
            color: #0e4c92;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #e9ecef;
        }
        .info-item {
            margin: 8px 0;
            padding: 5px 0;
            border-bottom: 1px solid #e9ecef;
        }
        .print-button {
            background-color: #0e4c92;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-align: center;
            cursor: pointer;
            margin: 10px 0;
        }
        @media print {
            .employee-card {
                break-inside: avoid;
                border: 1px solid #ccc;
                padding: 20px;
                margin: 0;
                width: 100%;
                box-shadow: none;
            }
            .info-section {
                background-color: white;
                border: 1px solid #e9ecef;
            }
            * {
                font-family: 'Tajawal', sans-serif !important;
            }
            .no-print {
                display: none !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<h3 class="search-title">البحث بالرقم الوظيفي</h3>', unsafe_allow_html=True)
        st.markdown('<p class="search-instruction">قم بإدخال الرقم الوظيفي للموظف للبحث عن بياناته</p>', unsafe_allow_html=True)

        emp_id = st.text_input(
            "الرقم الوظيفي",
            placeholder="أدخل الرقم الوظيفي هنا...",
            key="employee_search_id_1",
            label_visibility="collapsed"
        )

        if emp_id:
            employee_data = st.session_state.df[st.session_state.df['الرقم الوظيفي'] == emp_id]
            if not employee_data.empty:
                employee = employee_data.iloc[0]

                if pd.notna(employee['تاريخ الميلاد']):
                    birth_date = pd.to_datetime(employee['تاريخ الميلاد'])
                    current_age = (pd.Timestamp.now() - birth_date).days / 365.25
                    remaining_years = 65 - current_age

                    # Create two columns for layout
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        # Display data in a styled table
                        st.markdown("""
                        <style>
                        .employee-table {
                            width: 100%;
                            border-collapse: collapse;
                            margin: 20px 0;
                            font-size: 16px;
                            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
                            border-radius: 10px;
                            overflow: hidden;
                        }
                        .employee-table th {
                            background-color: #0e4c92;
                            color: white;
                            padding: 12px;
                            text-align: right;
                        }
                        .employee-table td {
                            padding: 12px;
                            border-bottom: 1px solid #ddd;
                        }
                        .employee-table tr:nth-child(even) {
                            background-color: #f8f9fa;
                        }
                        .employee-table tr:hover {
                            background-color: #f5f5f5;
                        }
                        </style>
                        """, unsafe_allow_html=True)

                        # Create table HTML
                        table_html = f"""
                        <table class="employee-table">
                            <tr><th colspan="2">البيانات الأساسية</th></tr>
                            <tr><td>الاسم</td><td>{employee['الاســــــــــــــــــــــــم']}</td></tr>
                            <tr><td>الرقم الوظيفي</td><td>{employee['الرقم الوظيفي']}</td></tr>
                            <tr><td>الرقم الوطني</td><td>{employee[' الرقم الوطني']}</td></tr>
                            <tr><th colspan="2">معلومات العمل</th></tr>
                            <tr><td>الإدارة</td><td>{employee['الادارة']}</td></tr>
                            <tr><td>الوظيفة</td><td>{employee['الوظيفة']}</td></tr>
                            <tr><td>الفئة الوظيفية</td><td>{employee['فئة الوظيفة']}</td></tr>
                            <tr><td>موقع العمل</td><td>{employee['موقع العمل']}</td></tr>
                            <tr><td>التابعية</td><td>{employee['التابعية']}</td></tr>
                            <tr><th colspan="2">المعلومات الشخصية</th></tr>
                            <tr><td>المؤهل العلمي</td><td>{employee['المؤهل العلمي']}</td></tr>
                            <tr><td>تاريخ الميلاد</td><td>{birth_date.strftime('%Y-%m-%d')}</td></tr>
                            <tr><td>مكان الميلاد</td><td>{employee['مكان الميلاد']}</td></tr>
                            <tr><td>العمر الحالي</td><td>{current_age:.1f} سنة</td></tr>
                        </table>
                        """
                        st.markdown(table_html, unsafe_allow_html=True)

                        # Print button
                        if st.button("🖨️ طباعة البيانات"):
                            st.markdown("""
                            <style>
                            @media print {
                                .stApp { display: block !important; }
                                .stButton, [class*="css-"] { display: none !important; }
                                .employee-table { box-shadow: none; }
                            }
                            </style>
                            """, unsafe_allow_html=True)

                    with col2:
                        # Create a pie chart for employment status
                        import plotly.graph_objects as go
                        
                        fig = go.Figure(data=[go.Pie(
                            labels=['سنوات الخدمة', 'السنوات المتبقية للتقاعد'],
                            values=[current_age, remaining_years],
                            hole=.3
                        )])
                        
                        fig.update_layout(
                            title="توزيع الخدمة الوظيفية",
                            height=300,
                            showlegend=True,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)

                        # Add a progress bar for retirement
                        st.markdown("### نسبة اكتمال سنوات الخدمة")
                        progress = current_age / 65  # This will give a value between 0 and 1
                        st.progress(min(progress, 1.0))
                        st.write(f"نسبة اكتمال سنوات الخدمة: {progress * 100:.1f}%")
                else:
                    st.error("لا يوجد تاريخ ميلاد مسجل للموظف")
            else:
                st.error("لم يتم العثور على موظف بهذا الرقم الوظيفي")

        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<h3 class="rtl">بيانات الموظفين</h3>', unsafe_allow_html=True)
        # Display the data table with pagination
        display_data_table(st.session_state.filtered_df, st.session_state.columns_mapping)

    with tabs[2]:
        st.markdown('<h3 class="rtl">البحث والتصفية</h3>', unsafe_allow_html=True)
        # Create search and filter interface
        filters = create_search_filters(st.session_state.df, st.session_state.columns_mapping)

        # Apply filters button
        if st.button("تطبيق التصفية"):
            st.session_state.filtered_df = apply_filters(st.session_state.df, filters)
            st.success(f'تم تصفية البيانات. تم العثور على {len(st.session_state.filtered_df)} موظف.')

        # Reset filters button
        if st.button("إعادة تعيين التصفية"):
            st.session_state.filtered_df = st.session_state.df.copy()
            st.success('تم إعادة تعيين التصفية.')
            st.rerun()

    with tabs[3]:
        st.markdown('<h3 class="rtl">لوحة التحليلات التفاعلية</h3>', unsafe_allow_html=True)
        # Create interactive dashboard
        create_interactive_dashboard(st.session_state.filtered_df)

    with tabs[4]:
        st.markdown('<h3 class="rtl">الهيكل التنظيمي</h3>', unsafe_allow_html=True)
        # عرض الهيكل التنظيمي
        display_advanced_analytics()

    with tabs[5]:
        st.markdown('<h3 class="rtl">التصدير والتقارير</h3>', unsafe_allow_html=True)
        if st.session_state.filtered_df is not None and not st.session_state.filtered_df.empty:
            create_export_section(st.session_state.filtered_df)
        else:
            st.warning("لا توجد بيانات متاحة للتصدير")

    # Database admin tab if database is initialized
    if st.session_state.db_initialized and len(main_tabs) > 5:
        with tabs[6]:
            show_db_admin()
else:
    # Display welcome screen with nicer styling and instructions
    st.markdown("""
    <style>
    .welcome-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 20px 0;
        text-align: center;
    }
    .welcome-title {
        color: #0e4c92;
        font-size: 2rem;
        margin-bottom: 20px;
        font-weight: 700;
    }
    .welcome-subtitle {
        color: #495057;
        font-size: 1.2rem;
        margin-bottom: 20px;
    }
    .developer-info {
        background: linear-gradient(135deg, #0e4c92, #1976d2);
        color: white;
        padding: 20px 25px;
        border-radius: 8px;
        margin: 15px auto;
        max-width: 300px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }
    .developer-info:before {
        content: "{ }";
        position: absolute;
        top: 50%;
        left: 10px;
        transform: translateY(-50%);
        font-size: 24px;
        opacity: 0.3;
        font-family: monospace;
    }
    .developer-info:after {
        content: "</>"; 
        position: absolute;
        top: 50%;
        right: 10px;
        transform: translateY(-50%);
        font-size: 24px;
        opacity: 0.3;
        font-family: monospace;
    }
    .developer-title {
        font-size: 1.1rem;
        margin-bottom: 5px;
        opacity: 0.9;
    }
    .developer-name {
        font-size: 1.4rem;
        font-weight: bold;
        margin-bottom: 3px;
    }
    .developer-id {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    .welcome-instructions {
        background-color: white;
        padding: 15px;
        border-radius: 5px;
        margin-top: 20px;
        text-align: right;
        border-right: 4px solid #0e4c92;
    }
    .requirements-list {
        text-align: right;
        padding-right: 20px;
        column-count: 2;
        column-gap: 20px;
    }
    .requirements-list li {
        margin-bottom: 8px;
        position: relative;
    }
    .requirements-list li:before {
        content: "✓";
        position: absolute;
        right: -20px;
        color: #0e4c92;
        font-weight: bold;
    }
    </style>

    <div class="welcome-container">
        <div class="welcome-title">نظام إدارة بيانات الموظفين</div>
        <div class="developer-info">
            <div class="developer-title">تطوير وبرمجة</div>
            <div class="developer-name">م. سراج نبوس</div>
            <div class="developer-id"># 31445</div>
        </div>
        <div class="welcome-subtitle">منظومة متكاملة لإدارة وتحليل بيانات الموظفين</div>

        <div class="welcome-instructions">
            <h3>كيفية استخدام النظام</h3>
            <p>1. قم بتحميل ملف الإكسل الخاص ببيانات الموظفين من القائمة الجانبية.</p>
            <p>2. استخدم علامات التبويب للتنقل بين الوظائف المختلفة للنظام.</p>
            <p>3. يمكنك البحث وتصفية البيانات وتصديرها بصيغ مختلفة.</p>
            <p>4. استفد من الرسوم البيانية والتحليلات لفهم أفضل لبيانات الموظفين.</p>

            <h4>الحقول المطلوبة في ملف البيانات:</h4>
            <ul class="requirements-list">
                <li>الاسم</li>
                <li>الرقم الوظيفي</li>
                <li>الرقم الوطني</li>
                <li>تاريخ الميلاد</li>
                <li>المؤهل العلمي</li>
                <li>الوظيفة</li>
                <li>الفئة الوظيفية</li>
                <li>الادارة</li>
                <li>التابعية</li>
                <li>موقع العمل</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)