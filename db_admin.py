import streamlit as st
import pandas as pd
from database import (
    import_excel_to_db, get_all_employees, delete_employee,
    update_employee, add_employee, get_departments,
    get_job_categories, get_workplaces
)
from utils import load_excel_file
from components import display_data_table
from datetime import datetime

def show_db_admin():
    """Display the database administration interface."""
    
    st.markdown("""
    <style>
    .admin-header {
        background-color: #0e4c92;
        padding: 10px;
        border-radius: 5px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .admin-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .admin-title {
        color: #0e4c92;
        font-weight: bold;
        margin-bottom: 15px;
        font-size: 1.2rem;
        text-align: right;
        border-bottom: 2px solid #0e4c92;
        padding-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="admin-header"><h2>إدارة قاعدة البيانات</h2></div>', unsafe_allow_html=True)
    
    # Create tabs for admin functions
    tab1, tab2, tab3 = st.tabs(["استيراد البيانات", "إدارة الموظفين", "إضافة موظف جديد"])
    
    with tab1:
        show_import_section()
    
    with tab2:
        show_employee_management()
    
    with tab3:
        show_add_employee_form()


def show_import_section():
    """Display the data import section."""
    st.markdown('<div class="admin-section">', unsafe_allow_html=True)
    st.markdown('<h3 class="admin-title">استيراد البيانات من ملف إكسل</h3>', unsafe_allow_html=True)
    
    # Upload file
    uploaded_file = st.file_uploader("اختر ملف إكسل للاستيراد", type=['xlsx', 'xls'], key="admin_upload")
    
    # Replace existing data option
    replace_existing = st.checkbox("استبدال البيانات الموجودة", value=False)
    
    if uploaded_file is not None:
        try:
            df = load_excel_file(uploaded_file)
            
            if df is not None:
                st.write("معاينة البيانات:")
                st.dataframe(df.head())
                
                if st.button("استيراد البيانات إلى قاعدة البيانات"):
                    success, message = import_excel_to_db(df, replace_existing)
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            else:
                st.error("فشل في قراءة البيانات. تأكد من أن الملف يحتوي على البيانات المطلوبة.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء تحميل الملف: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display current database stats
    st.markdown('<div class="admin-section">', unsafe_allow_html=True)
    st.markdown('<h3 class="admin-title">إحصائيات قاعدة البيانات</h3>', unsafe_allow_html=True)
    
    df = get_all_employees()
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("عدد الموظفين", len(df))
        
        with col2:
            departments = df['department'].dropna().unique()
            st.metric("عدد الإدارات", len(departments))
        
        with col3:
            workplaces = df['workplace'].dropna().unique()
            st.metric("عدد مواقع العمل", len(workplaces))
    else:
        st.info("لا توجد بيانات في قاعدة البيانات حالياً. قم باستيراد البيانات أولاً.")
    
    st.markdown("</div>", unsafe_allow_html=True)


def show_employee_management():
    """Display the employee management section."""
    st.markdown('<div class="admin-section">', unsafe_allow_html=True)
    st.markdown('<h3 class="admin-title">إدارة بيانات الموظفين</h3>', unsafe_allow_html=True)
    
    # Get all employees
    df = get_all_employees()
    
    if df.empty:
        st.info("لا توجد بيانات موظفين في قاعدة البيانات.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Convert timestamps to string format for display
    if 'birth_date' in df.columns:
        df['birth_date'] = pd.to_datetime(df['birth_date']).dt.strftime('%Y-%m-%d')
    
    # Search for specific employee
    search_col1, search_col2 = st.columns([1, 2])
    
    with search_col1:
        search_type = st.selectbox(
            "البحث حسب", 
            ["الرقم الوظيفي", "الاسم", "الادارة"],
            index=0
        )
    
    with search_col2:
        if search_type == "الرقم الوظيفي":
            search_term = st.text_input("أدخل الرقم الوظيفي")
            if search_term:
                df = df[df['employee_id'].astype(str).str.contains(search_term)]
        elif search_type == "الاسم":
            search_term = st.text_input("أدخل اسم الموظف")
            if search_term:
                df = df[df['name'].str.contains(search_term, na=False)]
        elif search_type == "الادارة":
            departments = ["الكل"] + sorted(get_departments())
            selected_dept = st.selectbox("اختر الإدارة", departments)
            if selected_dept != "الكل":
                df = df[df['department'] == selected_dept]
    
    # Display employees
    if not df.empty:
        # Create a mapping for the columns to display
        columns_mapping = {
            'name': 'الاسم',
            'employee_id': 'الرقم الوظيفي',
            'national_id': 'الرقم الوطني',
            'birth_date': 'تاريخ الميلاد',
            'education': 'المؤهل العلمي',
            'position': 'الوظيفة',
            'job_category': 'الفئة الوظيفية',
            'department': 'الادارة',
            'affiliation': 'التابعية',
            'workplace': 'موقع العمل'
        }
        
        # Display the data table
        display_data_table(df, columns_mapping)
        
        # Employee selection for editing or deletion
        st.markdown('<h4 class="admin-title">تعديل أو حذف موظف</h4>', unsafe_allow_html=True)
        
        selected_employee_id = st.selectbox(
            "اختر موظف للتعديل أو الحذف",
            options=df['employee_id'].tolist(),
            format_func=lambda x: f"{x} - {df[df['employee_id'] == x]['name'].values[0]}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("تعديل بيانات الموظف", key="edit_button"):
                # Store the selected employee ID in session state
                st.session_state.edit_employee_id = selected_employee_id
                st.session_state.show_edit_form = True
        
        with col2:
            if st.button("حذف الموظف", key="delete_button"):
                # Display confirmation
                st.session_state.confirm_delete = True
                st.session_state.delete_employee_id = selected_employee_id
        
        # Handle delete confirmation
        if st.session_state.get('confirm_delete', False):
            st.warning(f"هل أنت متأكد من حذف الموظف {df[df['employee_id'] == st.session_state.delete_employee_id]['name'].values[0]}؟")
            
            conf_col1, conf_col2 = st.columns(2)
            
            with conf_col1:
                if st.button("تأكيد الحذف"):
                    success, message = delete_employee(st.session_state.delete_employee_id)
                    
                    if success:
                        st.success(message)
                        st.session_state.confirm_delete = False
                        st.session_state.delete_employee_id = None
                        st.rerun()
                    else:
                        st.error(message)
            
            with conf_col2:
                if st.button("إلغاء"):
                    st.session_state.confirm_delete = False
                    st.session_state.delete_employee_id = None
                    st.rerun()
        
        # Display edit form
        if st.session_state.get('show_edit_form', False):
            show_edit_employee_form(st.session_state.edit_employee_id, df)
    
    st.markdown("</div>", unsafe_allow_html=True)


def show_edit_employee_form(employee_id, df):
    """Display the edit employee form."""
    st.markdown('<div class="admin-section">', unsafe_allow_html=True)
    st.markdown('<h3 class="admin-title">تعديل بيانات الموظف</h3>', unsafe_allow_html=True)
    
    # Get the employee data
    employee = df[df['employee_id'] == employee_id].iloc[0].to_dict()
    
    # Create form
    with st.form(key="edit_employee_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("الاسم", value=employee['name'])
            employee_id_value = st.text_input("الرقم الوظيفي", value=employee['employee_id'], disabled=True)
            national_id = st.text_input("الرقم الوطني", value=employee['national_id'])
            education = st.text_input("المؤهل العلمي", value=employee.get('education', ''))
            position = st.text_input("الوظيفة", value=employee.get('position', ''))
        
        with col2:
            # Get lists for dropdowns
            departments = get_departments()
            job_categories = get_job_categories()
            workplaces = get_workplaces()
            
            # Convert birth_date to datetime for date input
            if 'birth_date' in employee and employee['birth_date']:
                try:
                    birth_date_value = datetime.strptime(
                        employee['birth_date'], '%Y-%m-%d'
                    ).date()
                except:
                    birth_date_value = None
            else:
                birth_date_value = None
            
            birth_date = st.date_input("تاريخ الميلاد", value=birth_date_value)
            
            job_category = st.selectbox(
                "الفئة الوظيفية", 
                options=job_categories,
                index=job_categories.index(employee['job_category']) if employee.get('job_category') in job_categories else 0
            )
            
            department = st.selectbox(
                "الإدارة", 
                options=departments,
                index=departments.index(employee['department']) if employee.get('department') in departments else 0
            )
            
            affiliation = st.text_input("التابعية", value=employee.get('affiliation', ''))
            
            workplace = st.selectbox(
                "موقع العمل", 
                options=workplaces,
                index=workplaces.index(employee['workplace']) if employee.get('workplace') in workplaces else 0
            )
        
        # Submit button
        submit = st.form_submit_button("حفظ التغييرات")
        
        if submit:
            # Prepare data for update
            data = {
                'name': name,
                'national_id': national_id,
                'birth_date': birth_date,
                'education': education,
                'position': position,
                'job_category': job_category,
                'department': department,
                'affiliation': affiliation,
                'workplace': workplace
            }
            
            # Update employee
            success, message = update_employee(employee_id, data)
            
            if success:
                st.success(message)
                st.session_state.show_edit_form = False
                st.rerun()
            else:
                st.error(message)
    
    # Cancel button
    if st.button("إلغاء التعديل"):
        st.session_state.show_edit_form = False
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)


def show_add_employee_form():
    """Display the add employee form."""
    st.markdown('<div class="admin-section">', unsafe_allow_html=True)
    st.markdown('<h3 class="admin-title">إضافة موظف جديد</h3>', unsafe_allow_html=True)
    
    # Create form
    with st.form(key="add_employee_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("الاسم")
            employee_id = st.text_input("الرقم الوظيفي")
            national_id = st.text_input("الرقم الوطني")
            education = st.text_input("المؤهل العلمي")
            position = st.text_input("الوظيفة")
        
        with col2:
            # Get lists for dropdowns
            departments = get_departments()
            job_categories = get_job_categories()
            workplaces = get_workplaces()
            
            birth_date = st.date_input("تاريخ الميلاد")
            
            job_category = st.selectbox(
                "الفئة الوظيفية", 
                options=job_categories if job_categories else [""]
            )
            
            department = st.selectbox(
                "الإدارة", 
                options=departments if departments else [""]
            )
            
            affiliation = st.text_input("التابعية")
            
            workplace = st.selectbox(
                "موقع العمل", 
                options=workplaces if workplaces else [""]
            )
        
        # Submit button
        submit = st.form_submit_button("إضافة الموظف")
        
        if submit:
            # Validate required fields
            if not name or not employee_id or not national_id:
                st.error("الرجاء تعبئة الحقول المطلوبة: الاسم، الرقم الوظيفي، الرقم الوطني")
            else:
                # Prepare data for adding
                data = {
                    'name': name,
                    'employee_id': employee_id,
                    'national_id': national_id,
                    'birth_date': birth_date,
                    'education': education,
                    'position': position,
                    'job_category': job_category if job_category != "" else None,
                    'department': department if department != "" else None,
                    'affiliation': affiliation,
                    'workplace': workplace if workplace != "" else None
                }
                
                # Add employee
                success, message = add_employee(data)
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("</div>", unsafe_allow_html=True)


# Initialize session state variables
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False
    
if 'delete_employee_id' not in st.session_state:
    st.session_state.delete_employee_id = None
    
if 'show_edit_form' not in st.session_state:
    st.session_state.show_edit_form = False
    
if 'edit_employee_id' not in st.session_state:
    st.session_state.edit_employee_id = None