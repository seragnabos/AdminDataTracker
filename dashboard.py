import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from utils import convert_df_to_csv

def create_interactive_dashboard(df):
    """
    Create an interactive data visualization dashboard with enhanced analytics

    Args:
        df: DataFrame containing employee data
    """
    # إضافة التبديل بين أنواع العرض
    viz_type = st.radio(
        "نوع التحليل",
        ["نظرة عامة", "المقارنات", "الاتجاهات", "التحليل الديموغرافي"],
        horizontal=True
    )

    if viz_type == "نظرة عامة":
        create_kpi_summary(df)
        create_pie_charts(df)
        create_bar_charts(df)

    elif viz_type == "المقارنات":
        # إضافة مقارنات تفاعلية
        st.markdown("### 📊 المقارنات التفاعلية")

        compare_cols = st.multiselect(
            "اختر العناصر للمقارنة",
            ['الادارة', 'فئة الوظيفة', 'موقع العمل', 'المؤهل العلمي']
        )

        if len(compare_cols) == 2:
            comparison_df = pd.crosstab(df[compare_cols[0]], df[compare_cols[1]])
            fig = px.imshow(
                comparison_df,
                title=f'مقارنة {compare_cols[0]} مع {compare_cols[1]}',
                aspect='auto',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig, use_container_width=True, key=f"comparison_chart_{datetime.now().timestamp()}")

            # إضافة تحليل نسبي
            st.markdown("### 📈 التحليل النسبي")
            relative_df = comparison_df.div(comparison_df.sum(axis=1), axis=0) * 100
            fig2 = px.imshow(
                relative_df,
                title='التحليل النسبي (%)',
                aspect='auto',
                color_continuous_scale='RdYlBu'
            )
            st.plotly_chart(fig2, use_container_width=True, key=f"relative_chart_{datetime.now().timestamp()}")

    elif viz_type == "الاتجاهات":
        if 'تاريخ التعيين' in df.columns:
            st.markdown("### 📈 تحليل اتجاهات التوظيف")

            # تحليل شهري وسنوي
            df['شهر_التعيين'] = pd.to_datetime(df['تاريخ التعيين']).dt.to_period('M')
            monthly_hiring = df.groupby('شهر_التعيين').size()

            fig = px.line(
                x=monthly_hiring.index.astype(str),
                y=monthly_hiring.values,
                title='اتجاهات التوظيف الشهرية',
                labels={'x': 'الشهر', 'y': 'عدد التعيينات'}
            )
            st.plotly_chart(fig, use_container_width=True, key=f"monthly_hiring_{datetime.now().timestamp()}")

            # إضافة تحليل موسمي
            df['شهر'] = pd.to_datetime(df['تاريخ التعيين']).dt.month
            seasonal = df.groupby('شهر').size()

            fig2 = px.bar(
                x=['يناير', 'فبراير', 'مارس', 'ابريل', 'مايو', 'يونيو', 'يوليو', 'اغسطس', 'سبتمبر', 'اكتوبر', 'نوفمبر', 'ديسمبر'],
                y=seasonal.values,
                title='التحليل الموسمي للتوظيف',
                labels={'x': 'الشهر', 'y': 'عدد التعيينات'}
            )
            st.plotly_chart(fig2, use_container_width=True, key=f"seasonal_hiring_{datetime.now().timestamp()}")

    elif viz_type == "التحليل الديموغرافي":
        create_demographic_analysis(df)

        # إضافة تحليل الفئات العمرية حسب الإدارة
        if 'تاريخ الميلاد' in df.columns and 'الادارة' in df.columns:
            st.markdown("### 👥 تحليل الفئات العمرية حسب الإدارة")
            df['العمر'] = (pd.Timestamp.now() - pd.to_datetime(df['تاريخ الميلاد'])).dt.total_seconds() / (365.25 * 24 * 60 * 60)
            df['فئة_عمرية'] = pd.cut(df['العمر'], bins=[0, 25, 35, 45, 55, 100], labels=['< 25', '25-35', '35-45', '45-55', '> 55'])

            age_dept = pd.crosstab(df['الادارة'], df['فئة_عمرية'])
            fig = px.bar(
                age_dept,
                title='توزيع الفئات العمرية حسب الإدارة',
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True, key=f"age_dept_{datetime.now().timestamp()}")

    # إضافة زر لتصدير الرسوم البيانية
    if st.button("تصدير الرسوم البيانية"):
        if 'current_figures' in locals():
            for fig in current_figures:
                if fig is not None:
                    img_bytes = fig.to_image(format="png")
                    st.download_button(
                        label=f"تحميل {fig.layout.title.text}",
                        data=img_bytes,
                        file_name=f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png"
                    )
    if df is None or df.empty:
        st.warning("لا توجد بيانات للتحليل")
        return

    # Apply styling
    st.markdown("""
    <style>
    .dashboard-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .dashboard-title {
        color: #0e4c92;
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: right;
        border-right: 4px solid #0e4c92;
        padding-right: 10px;
    }
    .filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .chart-container {
        margin-top: 1.5rem;
        padding: 0.5rem;
        border-radius: 5px;
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

    # Dashboard header
    st.markdown('<h2 class="dashboard-title">لوحة تحكم التحليلات البصرية</h2>', unsafe_allow_html=True)

    # Create KPI summary cards
    create_kpi_summary(df)

    # Filter section
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: right;">تخصيص لوحة التحكم</h3>', unsafe_allow_html=True)

    # Allow user to select which visualizations to display
    chart_options = {
        "pie_charts": "الرسوم البيانية الدائرية",
        "bar_charts": "الرسوم البيانية الشريطية",
        "demographic": "التحليل الديموغرافي",
        "trends": "تحليل الاتجاهات والأنماط"
    }

    selected_charts = []
    col1, col2 = st.columns(2)

    with col1:
        if st.checkbox(chart_options["pie_charts"], value=True):
            selected_charts.append("pie_charts")
        if st.checkbox(chart_options["demographic"], value=True):
            selected_charts.append("demographic")

    with col2:
        if st.checkbox(chart_options["bar_charts"], value=True):
            selected_charts.append("bar_charts")
        if st.checkbox(chart_options["trends"], value=True):
            selected_charts.append("trends")

    st.markdown('</div>', unsafe_allow_html=True)

    # Display selected visualizations
    if "pie_charts" in selected_charts:
        create_pie_charts(df)

    if "bar_charts" in selected_charts:
        create_bar_charts(df)

    if "demographic" in selected_charts:
        create_demographic_analysis(df)

    if "trends" in selected_charts:
        create_trend_analysis(df)

def create_kpi_summary(df):
    """Create a summary of key performance indicators"""
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: right;">المؤشرات الرئيسية</h3>', unsafe_allow_html=True)

    # Create 4 KPI cards
    col1, col2, col3, col4 = st.columns(4)

    # Total employees
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background-color: #e6f3ff; border-radius: 5px; height: 100%;">
            <h1 style="color: #0e4c92; font-size: 2.5rem; margin-bottom: 0.5rem;">{}</h1>
            <p style="font-size: 1rem; color: #777;">إجمالي الموظفين</p>
        </div>
        """.format(len(df)), unsafe_allow_html=True)

    # Department count
    with col2:
        dept_count = df['الادارة'].nunique() if 'الادارة' in df.columns else 0
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background-color: #fff1e6; border-radius: 5px; height: 100%;">
            <h1 style="color: #d56a00; font-size: 2.5rem; margin-bottom: 0.5rem;">{}</h1>
            <p style="font-size: 1rem; color: #777;">عدد الإدارات</p>
        </div>
        """.format(dept_count), unsafe_allow_html=True)

    # Job Category count
    with col3:
        job_cat_count = df['فئة الوظيفة'].nunique() if 'فئة الوظيفة' in df.columns else 0
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background-color: #e6ffe6; border-radius: 5px; height: 100%;">
            <h1 style="color: #0a8a0a; font-size: 2.5rem; margin-bottom: 0.5rem;">{}</h1>
            <p style="font-size: 1rem; color: #777;">فئات وظيفية</p>
        </div>
        """.format(job_cat_count), unsafe_allow_html=True)

    # Workplace count
    with col4:
        workplace_count = df['موقع العمل'].nunique() if 'موقع العمل' in df.columns else 0
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background-color: #f0e6ff; border-radius: 5px; height: 100%;">
            <h1 style="color: #6a0dad; font-size: 2.5rem; margin-bottom: 0.5rem;">{}</h1>
            <p style="font-size: 1rem; color: #777;">مواقع العمل</p>
        </div>
        """.format(workplace_count), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def create_pie_charts(df):
    """Create pie charts for categorical data"""
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: right;">توزيع البيانات الفئوية</h3>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Department distribution
    if 'الادارة' in df.columns:
        with col1:
            dept_counts = df['الادارة'].value_counts().nlargest(10).reset_index()
            dept_counts.columns = ['الإدارة', 'العدد']

            # Check if there are more than 10 departments
            total_depts = df['الادارة'].nunique()
            if total_depts > 10:
                # Add an "Other" category for the remaining departments
                other_count = df['الادارة'].value_counts().nsmallest(total_depts - 10).sum()
                other_df = pd.DataFrame({'الإدارة': ['أخرى'], 'العدد': [other_count]})
                dept_counts = pd.concat([dept_counts, other_df])

            fig = px.pie(
                dept_counts, 
                values='العدد', 
                names='الإدارة', 
                title='توزيع الموظفين حسب الإدارة',
                color_discrete_sequence=px.colors.qualitative.Bold,
                hole=0.4
            )

            fig.update_layout(
                font=dict(family="Tajawal, sans-serif", size=14),
                title_font_size=18,
                title_x=0.5,
                margin=dict(t=50, b=20, l=20, r=20),
            )

            fig.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+percent+value')
            st.plotly_chart(fig, use_container_width=True, key=f"dept_pie_chart_{datetime.now().timestamp()}")

    # Job category distribution
    if 'فئة الوظيفة' in df.columns:
        with col2:
            category_counts = df['فئة الوظيفة'].value_counts().reset_index()
            category_counts.columns = ['الفئة الوظيفية', 'العدد']

            fig = px.pie(
                category_counts, 
                values='العدد', 
                names='الفئة الوظيفية', 
                title='توزيع الموظفين حسب الفئة الوظيفية',
                color_discrete_sequence=px.colors.qualitative.Safe,
                hole=0.4
            )

            fig.update_layout(
                font=dict(family="Tajawal, sans-serif", size=14),
                title_font_size=18,
                title_x=0.5,
                margin=dict(t=50, b=20, l=20, r=20),
            )

            fig.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+percent+value')
            st.plotly_chart(fig, use_container_width=True, key=f"job_cat_pie_chart_{datetime.now().timestamp()}")

    col1, col2 = st.columns(2)

    # Workplace distribution
    if 'موقع العمل' in df.columns:
        with col1:
            workplace_counts = df['موقع العمل'].value_counts().reset_index()
            workplace_counts.columns = ['موقع العمل', 'العدد']

            fig = px.pie(
                workplace_counts, 
                values='العدد', 
                names='موقع العمل', 
                title='توزيع الموظفين حسب موقع العمل',
                color_discrete_sequence=px.colors.qualitative.Pastel,
                hole=0.4
            )

            fig.update_layout(
                font=dict(family="Tajawal, sans-serif", size=14),
                title_font_size=18,
                title_x=0.5,
                margin=dict(t=50, b=20, l=20, r=20),
            )

            fig.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+percent+value')
            st.plotly_chart(fig, use_container_width=True, key=f"workplace_pie_chart_{datetime.now().timestamp()}")

    # Educational qualification distribution
    if 'المؤهل العلمي' in df.columns:
        with col2:
            edu_counts = df['المؤهل العلمي'].value_counts().reset_index()
            edu_counts.columns = ['المؤهل العلمي', 'العدد']

            fig = px.pie(
                edu_counts, 
                values='العدد', 
                names='المؤهل العلمي', 
                title='توزيع الموظفين حسب المؤهل العلمي',
                color_discrete_sequence=px.colors.qualitative.Vivid,
                hole=0.4
            )

            fig.update_layout(
                font=dict(family="Tajawal, sans-serif", size=14),
                title_font_size=18,
                title_x=0.5,
                margin=dict(t=50, b=20, l=20, r=20),
            )

            fig.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+percent+value')
            st.plotly_chart(fig, use_container_width=True, key=f"edu_pie_chart_{datetime.now().timestamp()}")

    st.markdown('</div>', unsafe_allow_html=True)

def create_bar_charts(df):
    """Create bar charts for categorical data analysis"""
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: right;">تحليل البيانات الفئوية</h3>', unsafe_allow_html=True)

    # Top departments by employee count
    if 'الادارة' in df.columns:
        top_depts = df['الادارة'].value_counts().nlargest(10).reset_index()
        top_depts.columns = ['الإدارة', 'عدد الموظفين']

        fig = px.bar(
            top_depts,
            x='عدد الموظفين',
            y='الإدارة',
            orientation='h',
            title='أكبر 10 إدارات من حيث عدد الموظفين',
            color='عدد الموظفين',
            color_continuous_scale='Blues',
        )

        fig.update_layout(
            font=dict(family="Tajawal, sans-serif", size=14),
            title_font_size=18,
            title_x=0.5,
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="عدد الموظفين",
            yaxis_title="الإدارة",
            margin=dict(t=50, b=50, l=50, r=20),
        )

        st.plotly_chart(fig, use_container_width=True, key=f"top_depts_bar_{datetime.now().timestamp()}")

    # Job category by department - Heatmap
    if 'الادارة' in df.columns and 'فئة الوظيفة' in df.columns:
        # Get top 10 departments and top 7 job categories
        top_depts = df['الادارة'].value_counts().nlargest(10).index.tolist()
        top_categories = df['فئة الوظيفة'].value_counts().nlargest(7).index.tolist()

        # Filter the dataframe
        filtered_df = df[df['الادارة'].isin(top_depts) & df['فئة الوظيفة'].isin(top_categories)]

        # Create a crosstab
        heatmap_data = pd.crosstab(filtered_df['الادارة'], filtered_df['فئة الوظيفة'])

        # Convert to format suitable for heatmap
        heatmap_df = heatmap_data.reset_index().melt(id_vars='الادارة', var_name='فئة الوظيفة', value_name='العدد')

        fig = px.density_heatmap(
            heatmap_df,
            x='فئة الوظيفة',
            y='الادارة',
            z='العدد',
            title='توزيع الفئات الوظيفية عبر الإدارات',
            color_continuous_scale='Viridis',
        )

        fig.update_layout(
            font=dict(family="Tajawal, sans-serif", size=14),
            title_font_size=18,
            title_x=0.5,
            margin=dict(t=50, b=50, l=50, r=20),
        )

        st.plotly_chart(fig, use_container_width=True, key=f"job_cat_dept_heatmap_{datetime.now().timestamp()}")

    # Affiliation analysis if available
    if 'التابعية' in df.columns:
        affiliation_counts = df['التابعية'].value_counts().reset_index()
        affiliation_counts.columns = ['التابعية', 'العدد']

        fig = px.bar(
            affiliation_counts,
            x='التابعية',
            y='العدد',
            title='توزيع الموظفين حسب التابعية',
            color='العدد',
            color_continuous_scale='Reds',
        )

        fig.update_layout(
            font=dict(family="Tajawal, sans-serif", size=14),
            title_font_size=18,
            title_x=0.5,
            xaxis_title="التابعية",
            yaxis_title="عدد الموظفين",
            xaxis_tickangle=45,
            margin=dict(t=50, b=100, l=50, r=20),
        )

        st.plotly_chart(fig, use_container_width=True, key=f"affiliation_bar_{datetime.now().timestamp()}")

    st.markdown('</div>', unsafe_allow_html=True)

def create_demographic_analysis(df):
    """Create demographic analysis visualizations"""
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: right;">التحليل الديموغرافي</h3>', unsafe_allow_html=True)

    # متوسط العمر حسب الإدارة
    if 'تاريخ الميلاد' in df.columns and 'الادارة' in df.columns:
        st.markdown('#### متوسط العمر حسب الإدارة')

        df_with_age = df.copy()
        today = datetime.now()
        df_with_age['العمر'] = (today - pd.to_datetime(df_with_age['تاريخ الميلاد'])).dt.total_seconds() / (365.25 * 24 * 60 * 60)

        avg_age_by_dept = df_with_age.groupby('الادارة')['العمر'].mean().round(1).reset_index()

        fig = px.bar(
            avg_age_by_dept,
            x='الادارة',
            y='العمر',
            title='متوسط العمر حسب الإدارة',
            labels={'العمر': 'متوسط العمر (سنوات)', 'الادارة': 'الإدارة'},
            color='العمر',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True, key=f"avg_age_dept_{datetime.now().timestamp()}")

    # توزيع المؤهلات حسب الفئة الوظيفية
    if 'المؤهل العلمي' in df.columns and 'فئة الوظيفة' in df.columns:
        st.markdown('#### توزيع المؤهلات العلمية حسب الفئة الوظيفية')

        qual_by_cat = pd.crosstab(df['فئة الوظيفة'], df['المؤهل العلمي'])
        qual_by_cat_pct = qual_by_cat.div(qual_by_cat.sum(axis=1), axis=0) * 100

        fig = px.imshow(
            qual_by_cat_pct,
            title='نسبة المؤهلات العلمية في كل فئة وظيفية',
            labels=dict(x='المؤهل العلمي', y='الفئة الوظيفية', color='النسبة المئوية'),
            color_continuous_scale='RdYlBu_r',
            aspect='auto'
        )
        st.plotly_chart(fig, use_container_width=True, key=f"qual_by_cat_{datetime.now().timestamp()}")

    # التوزيع الجغرافي
    if 'موقع العمل' in df.columns:
        st.markdown('#### التوزيع الجغرافي للموظفين')

        location_counts = df['موقع العمل'].value_counts()

        fig = px.pie(
            values=location_counts.values,
            names=location_counts.index,
            title='توزيع الموظفين حسب الموقع الجغرافي',
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True, key=f"location_pie_{datetime.now().timestamp()}")

    # تحليل إضافي: عدد الموظفين حسب الفئة والإدارة
    if 'فئة الوظيفة' in df.columns and 'الادارة' in df.columns:
        st.markdown('#### توزيع الفئات الوظيفية في الإدارات')

        dept_cat_counts = pd.crosstab(df['الادارة'], df['فئة الوظيفة'])

        fig = px.bar(
            dept_cat_counts,
            title='عدد الموظفين حسب الفئة والإدارة',
            barmode='stack',
            labels={'value': 'عدد الموظفين', 'الادارة': 'الإدارة'},
        )
        st.plotly_chart(fig, use_container_width=True, key=f"dept_cat_bar_{datetime.now().timestamp()}")

    # Age distribution analysis if birth_date is available
    if 'تاريخ الميلاد' in df.columns and pd.api.types.is_datetime64_any_dtype(df['تاريخ الميلاد']):
        # Calculate age
        today = datetime.now()
        df_with_age = df.copy()
        df_with_age['العمر'] = df_with_age['تاريخ الميلاد'].apply(
            lambda x: today.year - x.year - ((today.month, today.day) < (x.month, x.day)) if pd.notna(x) else np.nan
        )

        # Age distribution histogram
        fig = px.histogram(
            df_with_age.dropna(subset=['العمر']),
            x='العمر',
            nbins=50,
            title='توزيع أعمار الموظفين',
            color_discrete_sequence=['#0e4c92'],
            marginal='box',
        )

        fig.update_layout(
            font=dict(family="Tajawal, sans-serif", size=14),
            title_font_size=18,
            title_x=0.5,
            xaxis_title="العمر (سنوات)",
            yaxis_title="عدد الموظفين",
            margin=dict(t=50, b=50, l=50, r=20),
        )

        st.plotly_chart(fig, use_container_width=True, key=f"age_hist_{datetime.now().timestamp()}")

        # Age groups analysis
        age_bins = [20, 30, 40, 50, 60, 100]
        age_labels = ['20-29', '30-39', '40-49', '50-59', '60+']

        df_with_age['فئة العمر'] = pd.cut(
            df_with_age['العمر'], 
            bins=age_bins, 
            labels=age_labels,
            right=False
        )

        age_group_counts = df_with_age['فئة العمر'].value_counts().sort_index().reset_index()
        age_group_counts.columns = ['فئة العمر', 'العدد']

        fig = px.bar(
            age_group_counts,
            x='فئة العمر',
            y='العدد',
            title='توزيع الموظفين حسب الفئات العمرية',
            color='فئة العمر',
            color_discrete_sequence=px.colors.qualitative.Bold,
        )

        fig.update_layout(
            font=dict(family="Tajawal, sans-serif", size=14),
            title_font_size=18,
            title_x=0.5,
            xaxis_title="فئة العمر",
            yaxis_title="عدد الموظفين",
            margin=dict(t=50, b=50, l=50, r=20),
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True, key=f"age_group_bar_{datetime.now().timestamp()}")

        # Age pyramid by gender if gender is available
        if 'الجنس' in df.columns:
            males = df_with_age[df_with_age['الجنس'] == 'ذكر']
            females = df_with_age[df_with_age['الجنس'] == 'أنثى']

            male_counts = males['فئة العمر'].value_counts().sort_index().reset_index()
            male_counts.columns = ['فئة العمر', 'العدد']

            female_counts = females['فئة العمر'].value_counts().sort_index().reset_index()
            female_counts.columns = ['فئة العمر', 'العدد']
            female_counts['العدد'] = -female_counts['العدد']  # Negative for the pyramid

            # Create age pyramid
            fig = go.Figure()

            fig.add_trace(go.Bar(
                y=male_counts['فئة العمر'],
                x=male_counts['العدد'],
                name='ذكور',
                orientation='h',
                marker=dict(color='#1e88e5'),
                hovertemplate='ذكور: %{x}<extra></extra>'
            ))

            fig.add_trace(go.Bar(
                y=female_counts['فئة العمر'],
                x=female_counts['العدد'],
                name='إناث',
                orientation='h',
                marker=dict(color='#ff5252'),
                hovertemplate='إناث: %{x:,.0f}<extra></extra>'
            ))

            fig.update_layout(
                title='الهرم العمري للموظفين حسب الجنس',
                font=dict(family="Tajawal, sans-serif", size=14),
                title_font_size=18,
                title_x=0.5,
                barmode='relative',
                bargap=0.1,
                xaxis=dict(
                    title='عدد الموظفين',
                    tickvals=[-300, -200, -100, 0, 100, 200, 300],
                    ticktext=['300', '200', '100', '0', '100', '200', '300'],
                ),
                yaxis=dict(title='فئة العمر'),
                margin=dict(t=50, b=50, l=50, r=20),
            )

            st.plotly_chart(fig, use_container_width=True, key=f"age_pyramid_{datetime.now().timestamp()}")

    st.markdown('</div>', unsafe_allow_html=True)

def create_trend_analysis(df):
    """Create trend analysis visualizations"""
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: right;">تحليل الاتجاهات والأنماط</h3>', unsafe_allow_html=True)

    # If hire date is available, analyze employment trends
    if 'تاريخ التعيين' in df.columns and pd.api.types.is_datetime64_any_dtype(df['تاريخ التعيين']):
        # Employment by year
        df_copy = df.copy()
        df_copy['سنة التعيين'] = df_copy['تاريخ التعيين'].dt.year

        yearly_hires = df_copy['سنة التعيين'].value_counts().sort_index().reset_index()
        yearly_hires.columns = ['السنة', 'عدد التعيينات']

        fig = px.line(
            yearly_hires,
            x='السنة',
            y='عدد التعيينات',
            title='اتجاه التعيينات السنوية',
            markers=True,
            line_shape='spline',
        )

        fig.update_layout(
            font=dict(family="Tajawal, sans-serif", size=14),
            title_font_size=18,
            title_x=0.5,
            xaxis_title="السنة",
            yaxis_title="عدد التعيينات",
            margin=dict(t=50, b=50, l=50, r=20),
        )

        st.plotly_chart(fig, use_container_width=True, key=f"yearly_hires_{datetime.now().timestamp()}")

        # Employment by month (aggregated across years)
        df_copy['شهر التعيين'] = df_copy['تاريخ التعيين'].dt.month
        monthly_hires = df_copy['شهر التعيين'].value_counts().sort_index().reset_index()
        monthly_hires.columns = ['الشهر', 'عدد التعيينات']

        # Map month numbers to Arabic month names
        arabic_months = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'مايو', 6: 'يونيو',
            7: 'يوليو', 8: 'أغسطس', 9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }
        monthly_hires['اسم الشهر'] = monthly_hires['الشهر'].map(arabic_months)

        fig = px.bar(
            monthly_hires,
            x='اسم الشهر',
            y='عدد التعيينات',
            title='توزيع التعيينات حسب الشهر',
            color='عدد التعيينات',
            color_continuous_scale='Viridis',
        )

        # Ensure months are in correct order
        fig.update_layout(
            font=dict(family="Tajawal, sans-serif", size=14),
            title_font_size=18,
            title_x=0.5,
            xaxis={'categoryorder':'array', 'categoryarray': [arabic_months[i] for i in range(1, 13)]},
            xaxis_title="الشهر",
            yaxis_title="عدد التعيينات",
            margin=dict(t=50, b=80, l=50, r=20),
        )

        st.plotly_chart(fig, use_container_width=True, key=f"monthly_hires_{datetime.now().timestamp()}")

    # Show related metric trends if possible
    if 'الادارة' in df.columns and 'المؤهل العلمي' in df.columns:
        # Educational qualification by department - Bubble chart
        edu_by_dept = pd.crosstab(df['الادارة'], df['المؤهل العلمي']).reset_index()

        # Melt the dataframe for bubble chart
        edu_by_dept_melted = pd.melt(
            edu_by_dept, 
            id_vars='الادارة', 
            value_vars=edu_by_dept.columns[1:],
            var_name='المؤهل العلمي',
            value_name='العدد'
        )

        # Get department sizes for bubble size
        dept_sizes = df['الادارة'].value_counts().reset_index()
        dept_sizes.columns = ['الادارة', 'إجمالي الموظفين']

        # Merge to add total employees
        edu_by_dept_melted = edu_by_dept_melted.merge(dept_sizes, on='الادارة', how='left')

        # Calculate percentage
        edu_by_dept_melted['النسبة'] = edu_by_dept_melted['العدد'] / edu_by_dept_melted['إجمالي الموظفين'] * 100

        # Get top departments
        top_depts = dept_sizes.nlargest(10, 'إجمالي الموظفين')['الادارة'].tolist()
        filtered_data = edu_by_dept_melted[edu_by_dept_melted['الادارة'].isin(top_depts)]

        fig = px.scatter(
            filtered_data,
            x='الادارة',
            y='المؤهل العلمي',
            size='العدد',
            color='النسبة',
            hover_name='الادارة',
            size_max=50,
            color_continuous_scale='RdBu',
            title='تحليل المؤهلات العلمية حسب الإدارة',
        )

        fig.update_layout(
            font=dict(family="Tajawal, sans-serif", size=14),
            title_font_size=18,
            title_x=0.5,
            xaxis_title="الإدارة",
            yaxis_title="المؤهل العلمي",
            xaxis_tickangle=45,
            margin=dict(t=50, b=100, l=50, r=20),
        )

        st.plotly_chart(fig, use_container_width=True, key=f"edu_dept_bubble_{datetime.now().timestamp()}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Data insights section
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: right;">أفكار وملاحظات مستخلصة من البيانات</h3>', unsafe_allow_html=True)

    # Generate some key insights based on the data
    insights = []

    if 'الادارة' in df.columns:
        top_dept = df['الادارة'].value_counts().idxmax()
        top_dept_count = df['الادارة'].value_counts().max()
        top_dept_percentage = (top_dept_count / len(df)) * 100
        insights.append(f"إدارة '{top_dept}' هي الأكبر من حيث عدد الموظفين بنسبة {top_dept_percentage:.1f}% من إجمالي الموظفين.")

    if 'فئة الوظيفة' in df.columns:
        top_category = df['فئة الوظيفة'].value_counts().idxmax()
        top_category_count = df['فئة الوظيفة'].value_counts().max()
        top_category_percentage = (top_category_count / len(df)) * 100
        insights.append(f"الفئة الوظيفية '{top_category}' هي الأكثر شيوعاً بنسبة {top_category_percentage:.1f}% من إجمالي الموظفين.")

    if 'تاريخ الميلاد' in df.columns and pd.api.types.is_datetime64_any_dtype(df['تاريخ الميلاد']):
        today = datetime.now()
        avg_age = (today - df['تاريخ الميلاد']).mean().days / 365.25
        insights.append(f"متوسط عمر الموظفين هو {avg_age:.1f} سنة.")

    if 'المؤهل العلمي' in df.columns:
        edu_counts = df['المؤهل العلمي'].value_counts()
        top_edu = edu_counts.idxmax()
        top_edu_percentage = (edu_counts.max() / len(df)) * 100
        insights.append(f"المؤهل العلمي '{top_edu}' هو الأكثر شيوعاً بين الموظفين بنسبة {top_edu_percentage:.1f}%.")

    # Advanced Analytics Section
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: right;">التحليل المتقدم</h3>', unsafe_allow_html=True)

    # Education Analysis
    if 'المؤهل العلمي' in df.columns and 'الادارة' in df.columns:
        edu_dept = pd.crosstab(df['المؤهل العلمي'], df['الادارة'])
        fig = px.bar(
            edu_dept,
            title='توزيع المؤهلات العلمية حسب الإدارات',
            labels={'value': 'عدد الموظفين', 'المؤهل العلمي': 'المؤهل'},
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(
            barmode='stack',
            xaxis_title='الإدارة',
            yaxis_title='عدد الموظفين',
            showlegend=True,
            legend_title='المؤهل العلمي'
        )
        st.plotly_chart(fig, use_container_width=True, key=f"edu_dept_bar_{datetime.now().timestamp()}")

    # Age Distribution by Department
    if 'تاريخ الميلاد' in df.columns and 'الادارة' in df.columns:
        df_age = df.copy()
        df_age['العمر'] = (pd.Timestamp('now') - df_age['تاريخ الميلاد']).dt.total_seconds() / (365.25 * 24 * 60 * 60)

        fig = px.box(
            df_age,
            x='الادارة',
            y='العمر',
            title='توزيع الأعمار حسب الإدارات',
            color='الادارة',
            points='all'
        )
        fig.update_layout(
            xaxis_title='الإدارة',
            yaxis_title='العمر',
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, key=f"age_dept_box_{datetime.now().timestamp()}")

    # KPI Cards
    col1, col2, col3 = st.columns(3)

    with col1:
        if 'تاريخ الميلاد' in df.columns:
            avg_age = (pd.Timestamp('now') - df['تاريخ الميلاد']).mean().total_seconds() / (365.25 * 24 * 60 * 60)
            st.metric("متوسط العمر", f"{avg_age:.1f} سنة")

    with col2:
        if 'المؤهل العلمي' in df.columns:
            higher_edu_count = df[df['المؤهل العلمي'].str.contains('بكالوريوس|ماجستير|دكتوراه', na=False)].shape[0]
            higher_edu_percent = (higher_edu_count / len(df)) * 100
            st.metric("نسبة حملة الشهادات العليا", f"{higher_edu_percent:.1f}%")

    with col3:
        if 'الادارة' in df.columns:
            dept_diversity = df['الادارة'].nunique()
            st.metric("التنوع الإداري", f"{dept_diversity} إدارة")

    st.markdown('</div>', unsafe_allow_html=True)

    # Display insights
    for i, insight in enumerate(insights):
        st.markdown(f"""
        <div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; margin-bottom: 10px; border-right: 4px solid #0e4c92; direction: rtl; text-align: right;">
            <span style="font-weight: bold; color: #0e4c92;">ملاحظة {i+1}:</span> {insight}
        </div>
        """, unsafe_allow_html=True)

    # Export data button
    export_data = convert_df_to_csv(df)
    st.download_button(
        label="تصدير البيانات الكاملة",
        data=export_data,
        file_name=f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

    st.markdown('</div>', unsafe_allow_html=True)