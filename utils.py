import pandas as pd
import numpy as np
import io
from datetime import datetime
import re
import streamlit as st
from openpyxl.styles import Font, PatternFill, Alignment

def load_excel_file(file):
    """
    Load and process an Excel file containing employee data.
    
    Args:
        file: The uploaded Excel file
    
    Returns:
        DataFrame: Processed pandas DataFrame with original column names
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file)
        
        # Get the expected column names directly from the Excel file
        # and use them as is without renaming
        
        # Convert date column to datetime if it exists
        if 'تاريخ الميلاد' in df.columns:
            try:
                df['تاريخ الميلاد'] = pd.to_datetime(df['تاريخ الميلاد'], errors='coerce')
            except:
                # If conversion fails, keep as is
                pass
        
        # Convert IDs to string type for consistent handling
        if 'الرقم الوظيفي' in df.columns:
            df['الرقم الوظيفي'] = df['الرقم الوظيفي'].astype(str)
        
        if ' الرقم الوطني' in df.columns:
            df[' الرقم الوطني'] = df[' الرقم الوطني'].astype(str)
        
        # Create a mapping between original column names and simplified versions for display
        columns_mapping = {}
        for col in df.columns:
            # Create a simplified name without extra spaces
            simple_name = col.strip()
            columns_mapping[col] = simple_name
        
        # Save the mapping in the dataframe as an attribute (will be used later)
        df.attrs['columns_mapping'] = columns_mapping
        
        return df
    
    except Exception as e:
        st.error(f"خطأ في تحميل الملف: {str(e)}")
        return None

def save_excel_file(df):
    """
    Save DataFrame to Excel file and create a download link
    
    Args:
        df: DataFrame to save
    
    Returns:
        bytes: Excel file as bytes
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employee Data')
    
    return output.getvalue()

def apply_filters(df, filters):
    """
    Apply enhanced filters to the DataFrame with advanced search capabilities
    
    Args:
        df: DataFrame to filter
        filters: Dictionary of filter conditions
    
    Returns:
        DataFrame: Filtered DataFrame
    """
    filtered_df = df.copy()
    
    # تحسين البحث النصي مع دعم البحث المتعدد
    if filters.get('search_text'):
        search_terms = filters['search_text'].strip().split(',')
        for term in search_terms:
            term = term.strip().lower()
            if term:
                if filters.get('search_column') == 'all':
                    mask = pd.Series(False, index=filtered_df.index)
                    for col in filtered_df.columns:
                        if filtered_df[col].dtype == 'object':
                            column_mask = filtered_df[col].astype(str).str.lower().str.contains(term, na=False, regex=True)
                            mask = mask | column_mask
                    filtered_df = filtered_df[mask]
                else:
                    filtered_df = filtered_df[
                        filtered_df[filters['search_column']].astype(str).str.lower().str.contains(term, na=False, regex=True)
                    ]
    filtered_df = df.copy()
    
    # Apply text search if provided
    if filters.get('search_text') and filters.get('search_column'):
        search_term = filters['search_text'].strip().lower()
        search_column = filters['search_column']
        
        if search_column == 'all':
            # Search across all text columns
            mask = pd.Series(False, index=filtered_df.index)
            for col in filtered_df.columns:
                if filtered_df[col].dtype == 'object':  # Only search in text columns
                    column_mask = filtered_df[col].astype(str).str.lower().str.contains(search_term, na=False)
                    mask = mask | column_mask
            filtered_df = filtered_df[mask]
        else:
            # Search in specific column
            filtered_df = filtered_df[
                filtered_df[search_column].astype(str).str.lower().str.contains(search_term, na=False)
            ]
    
    # Apply department filter if provided
    if filters.get('department') and filters['department'] != 'الكل':
        filtered_df = filtered_df[filtered_df['الادارة'] == filters['department']]
    
    # Apply job category filter if provided
    if filters.get('job_category') and filters['job_category'] != 'الكل':
        filtered_df = filtered_df[filtered_df['فئة الوظيفة'] == filters['job_category']]
    
    # Apply workplace filter if provided
    if filters.get('workplace') and filters['workplace'] != 'الكل':
        filtered_df = filtered_df[filtered_df['موقع العمل'] == filters['workplace']]
    
    # Apply date range filter if provided
    if filters.get('date_range'):
        start_date, end_date = filters['date_range']
        if 'تاريخ الميلاد' in filtered_df.columns and pd.api.types.is_datetime64_any_dtype(filtered_df['تاريخ الميلاد']):
            # Convert date objects to pandas Timestamp
            start_timestamp = pd.Timestamp(start_date)
            end_timestamp = pd.Timestamp(end_date)
            
            filtered_df = filtered_df[
                (filtered_df['تاريخ الميلاد'] >= start_timestamp) & 
                (filtered_df['تاريخ الميلاد'] <= end_timestamp)
            ]
    
    return filtered_df

def convert_df_to_csv(df):
    """
    Convert DataFrame to CSV
    
    Args:
        df: DataFrame to convert
    
    Returns:
        str: CSV string
    """
    return df.to_csv(index=False).encode('utf-8-sig')  # Use UTF-8 with BOM for Arabic support
