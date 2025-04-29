import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import base64
import io
import pandas as pd
from utils import save_excel_file, convert_df_to_csv
from io import BytesIO
from openpyxl.styles import Font, Alignment, PatternFill

def display_data_table(df, columns_mapping):
    """
    Display employee data in a paginated table

    Args:
        df: DataFrame containing employee data
        columns_mapping: Dictionary mapping internal column names to display names
    """
    if df is None or df.empty:
        st.warning("لا توجد بيانات للعرض")
        return

    # Create a copy of the dataframe for display
    display_df = df.copy()

    # Format date columns for better display
    for col in display_df.columns:
        if pd.api.types.is_datetime64_any_dtype(display_df[col]):
            display_df[col] = display_df[col].dt.strftime('%Y-%m-%d')

    # إزالة أي عمود تسلسلي قد يكون موجوداً بالفعل (ربما عمود مؤشر)
    if display_df.index.name is None and isinstance(display_df.index, pd.RangeIndex):
        # إعادة تعيين المؤشر
        display_df = display_df.reset_index(drop=True)

    # تأكد من حذف أي أعمدة بلا اسم
    for col in display_df.columns:
        if col == '' or col is None:
            display_df = display_df.drop(col, axis=1)

    # إضافة عمود التسلسل "ت" في أقصى اليمين
    display_df.insert(0, 'ت', range(1, len(display_df) + 1))

    # تأكد من أنه لا يوجد صف بمؤشر يبدأ من 0
    display_df = display_df.copy()

    # Pagination controls in a nice card
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <h4 style="margin-bottom: 10px; text-align: right;">تحكم بالصفحات</h4>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])

    with col1:
        rows_per_page = st.number_input("عدد الصفوف في الصفحة", min_value=10, max_value=100, value=25, step=5)

    total_pages = (len(display_df) - 1) // rows_per_page + 1

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    # Page navigation
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])

    with col1:
        if st.button("الصفحة السابقة", use_container_width=True):
            if st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()

    with col2:
        if st.button("الصفحة التالية", use_container_width=True):
            if st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                st.rerun()

    with col3:
        st.markdown(f"""
        <div style="text-align: center; padding: 8px; background-color: #e9ecef; border-radius: 5px;">
            <p style="margin-bottom: 0; font-weight: bold;">الصفحة {st.session_state.current_page} من {total_pages}</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        page_number = st.number_input("انتقال إلى صفحة", min_value=1, max_value=total_pages, value=st.session_state.current_page)
        if page_number != st.session_state.current_page:
            st.session_state.current_page = page_number
            st.rerun()

    # Display current page of data
    start_idx = (st.session_state.current_page - 1) * rows_per_page
    end_idx = min(start_idx + rows_per_page, len(display_df))

    # Apply styling to the dataframe
    st.markdown("""
    <style>
    .dataframe-container {
        border-radius: 5px;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        padding: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
    # Display table with current page data with improved styling
    st.dataframe(
        display_df.iloc[start_idx:end_idx], 
        use_container_width=True,
        height=min(35 * rows_per_page, 500),  # Dynamic height based on rows
    )
    # أزرار التصدير السريع
    col1, col2, col3 = st.columns(3)
    with col1:
        csv_data = convert_df_to_csv(display_df.iloc[start_idx:end_idx])
        st.download_button(
            "تصدير الصفحة الحالية (CSV)",
            csv_data,
            f"employee_data_page_{st.session_state.current_page}.csv",
            "text/csv"
        )

    with col2:
        excel_data = save_excel_file(display_df.iloc[start_idx:end_idx])
        st.download_button(
            "تصدير الصفحة الحالية (Excel)",
            excel_data,
            f"employee_data_page_{st.session_state.current_page}.xlsx",
            "application/vnd.ms-excel"
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # Display record count information in a better format
    st.markdown(f"""
    <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px; text-align: center;">
        <p style="margin-bottom: 0;">عرض السجلات <b>{start_idx + 1}</b> إلى <b>{end_idx}</b> من أصل <b>{len(display_df)}</b> سجل</p>
    </div>
    """, unsafe_allow_html=True)

def create_search_filters(df, columns_mapping):
    """
    Create enhanced search and filter interface with advanced options

    Args:
        df: DataFrame containing employee data
        columns_mapping: Dictionary mapping internal column names to display names

    Returns:
        dict: Dictionary of selected filters
    """
    st.markdown("""
    <style>
    .search-options {
        background-color: #f0f7ff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .advanced-search {
        background-color: #fff4e6;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)
    filters = {}

    # Apply card style for search filters
    st.markdown("""
    <style>
    .filter-card {
        background-color: #f8f9fa; 
        padding: 15px; 
        border-radius: 5px; 
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .filter-title {
        color: #0e4c92;
        font-weight: bold;
        margin-bottom: 10px;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

    # Layout with columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h4 class="filter-title">البحث النصي</h4>', unsafe_allow_html=True)

        # Search column selection
        search_options = [('all', 'جميع الحقول')]
        for col in df.columns:
            search_options.append((col, col))

        selected_col = st.selectbox(
            "البحث في",
            options=[col[0] for col in search_options],
            format_func=lambda x: dict(search_options)[x],
            index=0
        )
        filters['search_column'] = selected_col

        # Search text input
        search_text = st.text_input(
            "نص البحث",
            placeholder="أدخل نص البحث هنا...",
            label_visibility="visible"
        )
        filters['search_text'] = search_text
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h4 class="filter-title">تصفية متقدمة</h4>', unsafe_allow_html=True)

        # Department filter
        if 'الادارة' in df.columns:
            dept_options = ['الكل'] + sorted(df['الادارة'].dropna().unique().tolist())
            selected_dept = st.selectbox("الإدارة", options=dept_options)
            filters['department'] = selected_dept

        # Job category filter
        if 'فئة الوظيفة' in df.columns:
            category_options = ['الكل'] + sorted(df['فئة الوظيفة'].dropna().unique().tolist())
            selected_category = st.selectbox("الفئة الوظيفية", options=category_options)
            filters['job_category'] = selected_category

        # Workplace filter
        if 'موقع العمل' in df.columns:
            workplace_options = ['الكل'] + sorted(df['موقع العمل'].dropna().unique().tolist())
            selected_workplace = st.selectbox("موقع العمل", options=workplace_options)
            filters['workplace'] = selected_workplace
        st.markdown('</div>', unsafe_allow_html=True)

    # Date range filter for birth_date
    if 'تاريخ الميلاد' in df.columns and pd.api.types.is_datetime64_any_dtype(df['تاريخ الميلاد']):
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h4 class="filter-title">تصفية حسب تاريخ الميلاد</h4>', unsafe_allow_html=True)

        try:
            min_date = df['تاريخ الميلاد'].min().date()
            max_date = df['تاريخ الميلاد'].max().date()

            date_range = st.date_input(
                "نطاق تاريخ الميلاد",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

            if len(date_range) == 2:
                filters['date_range'] = date_range
        except:
            st.warning("تعذر تحميل بيانات التاريخ، يرجى التأكد من تنسيق تاريخ الميلاد في ملف البيانات")

        st.markdown('</div>', unsafe_allow_html=True)

    return filters

def create_export_section(df):
    """Create enhanced data export interface with multiple format options"""
    if df is None or df.empty:
        st.warning("لا توجد بيانات للتصدير")
        return

    st.markdown("### 📊 التقارير المتقدمة")

    report_tabs = st.tabs([
        "تقارير تحليلية", 
        "تقارير تفصيلية",
        "تقارير مخصصة",
        "تصدير البيانات"
    ])

    with report_tabs[0]:
        analysis_type = st.selectbox(
            "نوع التحليل",
            [
                "تحليل الموارد البشرية",
                "تحليل المؤهلات والكفاءات",
                "تحليل التوزيع الجغرافي",
                "تحليل الهيكل التنظيمي"
            ]
        )

        if analysis_type == "تحليل الموارد البشرية":
            hr_metrics = {
                "إجمالي الموظفين": len(df),
                "عدد الإدارات": df['الادارة'].nunique(),
                "متوسط الموظفين لكل إدارة": len(df) / df['الادارة'].nunique()
            }
            st.write(pd.DataFrame([hr_metrics]).T)

        elif analysis_type == "تحليل المؤهلات والكفاءات":
            edu_analysis = pd.crosstab([df['المؤهل العلمي']], [df['فئة الوظيفة']], margins=True)
            st.write(edu_analysis)

    with report_tabs[1]:
        detailed_options = st.multiselect(
            "اختر التفاصيل المطلوبة",
            ["الادارة", "المؤهل العلمي", "فئة الوظيفة", "موقع العمل"],
            default=["الادارة"]
        )

        if detailed_options:
            detailed_report = df.groupby(detailed_options).size().reset_index(name='العدد')
            st.dataframe(detailed_report)

            if st.button("تصدير التقرير التفصيلي"):
                excel_data = save_excel_file(detailed_report)
                st.download_button(
                    "تحميل التقرير (Excel)",
                    excel_data,
                    f"detailed_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    "application/vnd.ms-excel"
                )

    with report_tabs[2]:
        st.write("### إنشاء تقرير مخصص")

        # اختيار الأعمدة
        available_columns = df.columns.tolist()
        selected_columns = st.multiselect(
            "اختر الأعمدة",
            options=available_columns,
            default=available_columns[:3]
        )

        # اختيار التصفية
        filter_column = st.selectbox("تصفية حسب", ["بدون تصفية"] + df.columns.tolist())
        if filter_column != "بدون تصفية":
            filter_values = st.multiselect(
                "اختر القيم",
                df[filter_column].unique().tolist()
            )

            if filter_values:
                filtered_df = df[df[filter_column].isin(filter_values)]
            else:
                filtered_df = df
        else:
            filtered_df = df

        if selected_columns:
            custom_report = filtered_df[selected_columns]
            st.dataframe(custom_report)

            if st.button("تصدير التقرير المخصص"):
                excel_data = save_excel_file(custom_report)
                st.download_button(
                    "تحميل التقرير (Excel)",
                    excel_data,
                    f"custom_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    "application/vnd.ms-excel"
                )

    with report_tabs[3]:
        st.write("### تصدير البيانات")
        export_format = st.radio(
            "اختر صيغة التصدير",
            ["Excel", "CSV", "JSON"],
            horizontal=True
        )

        if export_format == "Excel":
            excel_data = save_excel_file(df)
            st.download_button(
                "تحميل الملف (Excel)",
                excel_data,
                f"data_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "application/vnd.ms-excel"
            )
        elif export_format == "CSV":
            csv_data = convert_df_to_csv(df)
            st.download_button(
                "تحميل الملف (CSV)",
                csv_data,
                f"data_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv"
            )
        else:
            json_data = df.to_json(orient='records', force_ascii=False)
            st.download_button(
                "تحميل الملف (JSON)",
                json_data,
                f"data_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                "application/json"
            )

    # تأكد من أن DataFrame يحتوي على البيانات المطلوبة
    required_columns = ['الادارة', 'فئة الوظيفة', 'المؤهل العلمي', 'موقع العمل']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.warning(f"بعض الأعمدة المطلوبة غير موجودة: {', '.join(missing_columns)}")
        return

    st.markdown("### 📊 التقارير التفصيلية")

    report_type = st.selectbox(
        "اختر نوع التقرير",
        ["تقرير الموظفين حسب الإدارة", 
         "تقرير المؤهلات العلمية", 
         "تقرير الفئات الوظيفية",
         "تقرير التوزيع الجغرافي",
         "تقرير إحصائي شامل"]
    )

    if report_type == "تقرير الموظفين حسب الإدارة":
        dept_report = pd.pivot_table(
            df,
            index='الادارة',
            values=['الرقم الوظيفي'],
            aggfunc='count'
        ).reset_index()
        dept_report.columns = ['الإدارة', 'عدد الموظفين']
        st.dataframe(dept_report)

        # تصدير التقرير
        if st.button("تصدير تقرير الإدارات"):
            excel_data = save_excel_file(dept_report)
            st.download_button(
                "تحميل التقرير (Excel)",
                excel_data,
                f"dept_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "application/vnd.ms-excel"
            )

    elif report_type == "تقرير المؤهلات العلمية":
        edu_report = df.groupby(['المؤهل العلمي', 'الادارة']).size().unstack(fill_value=0)
        st.dataframe(edu_report)

        if st.button("تصدير تقرير المؤهلات"):
            excel_data = save_excel_file(edu_report)
            st.download_button(
                "تحميل التقرير (Excel)",
                excel_data,
                f"education_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "application/vnd.ms-excel"
            )

    elif report_type == "تقرير الفئات الوظيفية":
        job_report = pd.crosstab([df['فئة الوظيفة']], df['الادارة'])
        st.dataframe(job_report)

        if st.button("تصدير تقرير الفئات الوظيفية"):
            excel_data = save_excel_file(job_report)
            st.download_button(
                "تحميل التقرير (Excel)",
                excel_data,
                f"job_category_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "application/vnd.ms-excel"
            )

    elif report_type == "تقرير التوزيع الجغرافي":
        loc_report = pd.crosstab([df['موقع العمل']], [df['الادارة'], df['فئة الوظيفة']])
        st.dataframe(loc_report)

        if st.button("تصدير تقرير التوزيع الجغرافي"):
            excel_data = save_excel_file(loc_report)
            st.download_button(
                "تحميل التقرير (Excel)",
                excel_data,
                f"location_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "application/vnd.ms-excel"
            )

    elif report_type == "تقرير إحصائي شامل":
        # إنشاء تقرير إحصائي شامل
        stats_dict = {
            'إجمالي عدد الموظفين': len(df),
            'عدد الإدارات': df['الادارة'].nunique(),
            'عدد الفئات الوظيفية': df['فئة الوظيفة'].nunique(),
            'عدد مواقع العمل': df['موقع العمل'].nunique()
        }

        stats_df = pd.DataFrame(list(stats_dict.items()), columns=['المؤشر', 'القيمة'])
        st.dataframe(stats_df)

        if st.button("تصدير التقرير الإحصائي"):
            # إنشاء مصنف إكسل مع عدة أوراق عمل
            with pd.ExcelWriter(BytesIO()) as writer:
                stats_df.to_excel(writer, sheet_name='المؤشرات الرئيسية', index=False)
                df.groupby('الادارة').size().reset_index(name='العدد').to_excel(writer, sheet_name='تفاصيل الإدارات', index=False)
                df.groupby('فئة الوظيفة').size().reset_index(name='العدد').to_excel(writer, sheet_name='تفاصيل الفئات', index=False)

                st.download_button(
                    "تحميل التقرير الشامل (Excel)",
                    writer.getvalue(),
                    f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    "application/vnd.ms-excel"
                )

    st.markdown("### 📊 تصدير البيانات والتقارير")

    # خيارات التصدير
    export_type = st.radio(
        "اختر نوع التصدير:",
        ["تقرير كامل", "بيانات مختارة", "تقرير إحصائي"],
        horizontal=True
    )

    if export_type == "تقرير كامل":
        # تصدير كل البيانات
        excel_data = save_excel_file(df)
        st.download_button(
            label="تحميل التقرير الكامل (Excel)",
            data=excel_data,
            file_name=f"full_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.ms-excel"
        )

    elif export_type == "بيانات مختارة":
        # اختيار الأعمدة للتصدير
        selected_cols = st.multiselect(
            "اختر الأعمدة المطلوبة:",
            df.columns.tolist()
        )
        if selected_cols:
            filtered_df = df[selected_cols]
            csv_data = convert_df_to_csv(filtered_df)
            st.download_button(
                label="تحميل البيانات المختارة (CSV)",
                data=csv_data,
                file_name=f"selected_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

    else:  # تقرير إحصائي
        # إنشاء تقرير إحصائي
        stats_df = df.describe()
        excel_stats = save_excel_file(stats_df)
        st.download_button(
            label="تحميل التقرير الإحصائي (Excel)",
            data=excel_stats,
            file_name=f"statistical_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.ms-excel"
        )
    if df is None or df.empty:
        st.warning("لا توجد بيانات للتصدير")
        return

    # Enhanced export section with better styling
    st.markdown("""
    <style>
    .export-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .viz-card {
        background-color: white;
        padding: 15px;
        border-radius: 5px;
        margin-top: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-top: 4px solid #0e4c92;
    }
    .section-title {
        color: #0e4c92;
        font-weight: bold;
        margin-bottom: 15px;
        font-size: 1.2rem;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

    # Export options with better UI
    st.markdown('<div class="export-card">', unsafe_allow_html=True)
    st.markdown('<h4 class="section-title">تصدير البيانات</h4>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])

    with col1:
        export_format = st.radio(
            "صيغة التصدير",
            options=["Excel", "CSV"],
            horizontal=True
        )

    with col2:
        if export_format == "Excel":
            excel_data = save_excel_file(df)

            st.download_button(
                label="تصدير إلى Excel",
                data=excel_data,
                file_name=f"employee_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
        else:  # CSV
            csv_data = convert_df_to_csv(df)

            st.download_button(
                label="تصدير إلى CSV",
                data=csv_data,
                file_name=f"employee_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # Improved visualizations section
    if len(df) > 0:
        st.markdown('<div class="viz-card">', unsafe_allow_html=True)
        st.markdown('<h4 class="section-title">التحليلات البصرية للبيانات</h4>', unsafe_allow_html=True)

        viz_options = []
        if 'الادارة' in df.columns:
            viz_options.append("توزيع الإدارات")

        if 'فئة الوظيفة' in df.columns:
            viz_options.append("توزيع الفئات الوظيفية")

        if 'موقع العمل' in df.columns:
            viz_options.append("توزيع مواقع العمل")

        if 'تاريخ الميلاد' in df.columns and pd.api.types.is_datetime64_any_dtype(df['تاريخ الميلاد']):
            viz_options.append("تحليل الأعمار")

        if not viz_options:
            st.warning("لا توجد بيانات للتحليل")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        viz_type = st.selectbox(
            "اختر نوع التحليل",
            options=viz_options
        )

        if viz_type == "توزيع الإدارات" and 'الادارة' in df.columns:
            dept_counts = df['الادارة'].value_counts().reset_index()
            dept_counts.columns = ['الإدارة', 'العدد']

            # Improved styling for charts
            fig = px.pie(
                dept_counts, 
                values='العدد', 
                names='الإدارة', 
                title='توزيع الموظفين حسب الإدارة',
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(
                font=dict(family="Tajawal, sans-serif", size=14),
                title_font=dict(family="Tajawal, sans-serif", size=18),
                legend_title_font=dict(family="Tajawal, sans-serif", size=14),
                margin=dict(t=50, b=50, l=50, r=50),
            )
            st.plotly_chart(fig, use_container_width=True)

        elif viz_type == "توزيع الفئات الوظيفية" and 'فئة الوظيفة' in df.columns:
            cat_counts = df['فئة الوظيفة'].value_counts().reset_index()
            cat_counts.columns = ['الفئة الوظيفية', 'العدد']

            # Sort by count for better visualization
            cat_counts = cat_counts.sort_values('العدد', ascending=False)

            fig = px.bar(
                cat_counts, 
                x='الفئة الوظيفية', 
                y='العدد', 
                title='توزيع الموظفين حسب الفئة الوظيفية',
                color='العدد',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                xaxis_title='الفئة الوظيفية', 
                yaxis_title='عدد الموظفين',
                font=dict(family="Tajawal, sans-serif", size=14),
                title_font=dict(family="Tajawal, sans-serif", size=18),
                margin=dict(t=50, b=50, l=50, r=50),
            )
            st.plotly_chart(fig, use_container_width=True)

        elif viz_type == "توزيع مواقع العمل" and 'موقع العمل' in df.columns:
            workplace_counts = df['موقع العمل'].value_counts().reset_index()
            workplace_counts.columns = ['موقع العمل', 'العدد']

            fig = px.pie(
                workplace_counts, 
                values='العدد', 
                names='موقع العمل', 
                title='توزيع الموظفين حسب موقع العمل',
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig.update_layout(
                font=dict(family="Tajawal, sans-serif", size=14),
                title_font=dict(family="Tajawal, sans-serif", size=18),
                legend_title_font=dict(family="Tajawal, sans-serif", size=14),
                margin=dict(t=50, b=50, l=50, r=50),
            )
            st.plotly_chart(fig, use_container_width=True)

        elif viz_type == "تحليل الأعمار" and 'تاريخ الميلاد' in df.columns and pd.api.types.is_datetime64_any_dtype(df['تاريخ الميلاد']):
            # Calculate age from birth_date
            today = pd.Timestamp('today')
            df['age'] = (today - df['تاريخ الميلاد']).dt.days / 365.25

            age_bins = [0, 20, 30, 40, 50, 60, 100]
            age_labels = ['< 20', '20-30', '30-40', '40-50', '50-60', '> 60']

            df['age_group'] = pd.cut(df['age'], bins=age_bins, labels=age_labels, right=False)
            age_counts = df['age_group'].value_counts().reset_index()
            age_counts.columns = ['الفئة العمرية', 'العدد']

            # Sort by age group order
            age_counts['sort_order'] = pd.Categorical(
                age_counts['الفئة العمرية'], 
                categories=age_labels, 
                ordered=True
            )
            age_counts = age_counts.sort_values('sort_order')

            fig = px.bar(
                age_counts, 
                x='الفئة العمرية', 
                y='العدد', 
                title='توزيع الموظفين حسب الفئة العمرية',
                color='العدد',
                color_continuous_scale='Turbo'
            )
            fig.update_layout(
                xaxis_title='الفئة العمرية', 
                yaxis_title='عدد الموظفين',
                font=dict(family="Tajawal, sans-serif", size=14),
                title_font=dict(family="Tajawal, sans-serif", size=18),
                margin=dict(t=50, b=50, l=50, r=50),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

def save_excel_file(df, sheet_name="بيانات الموظفين"):
    """
    Save DataFrame to Excel file with enhanced Arabic support

    Args:
        df: DataFrame to save
        sheet_name: اسم ورقة العمل

    Returns:
        bytes: Excel file as bytes
    """
    output = io.BytesIO()

    # Create Excel writer with Arabic support
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write DataFrame
        df.to_excel(writer, index=False, sheet_name=sheet_name)

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Set RTL direction for the worksheet
        worksheet.sheet_view.rightToLeft = True

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

        # Add header formatting
        header_font = Font(bold=True, name='Calibri', size=12)
        header_fill = PatternFill(start_color='E9ECF0', end_color='E9ECF0', fill_type='solid')

        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='right', vertical='center', wrap_text=True)

    return output.getvalue()

def convert_df_to_csv(df):
    return df.to_csv(encoding='utf-8', index=False).encode('utf-8')