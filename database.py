import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, Text, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import streamlit as st
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///employees.db")

# Initialize engine and session only if DATABASE_URL is available
engine = None
session = None

if DATABASE_URL:
    # Create SQLAlchemy engine and session
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
else:
    logger.warning("DATABASE_URL environment variable not set. Database functionality will be disabled.")

# Create a base class for declarative models
Base = declarative_base()

# Define Employee model
class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False)
    national_id = Column(String(50), unique=True, nullable=False)
    birth_date = Column(Date, nullable=True)
    education = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    job_category = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    affiliation = Column(String(100), nullable=True)
    workplace = Column(String(100), nullable=True)
    created_at = Column(Date, default=datetime.now)
    updated_at = Column(Date, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Employee(name='{self.name}', employee_id='{self.employee_id}')>"


def init_db():
    """
    Initialize the database by creating all tables if they don't exist.
    """
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully.")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        return False


def import_excel_to_db(df, replace_existing=False):
    """
    Import data from a pandas DataFrame to the database.
    
    Args:
        df: DataFrame containing employee data
        replace_existing: If True, delete all existing records before importing
        
    Returns:
        tuple: (success, message)
    """
    try:
        # If replace_existing is True, delete all existing records
        if replace_existing:
            session.query(Employee).delete()
            session.commit()
            logger.info("Deleted all existing records from employees table.")
        
        # Convert DataFrame to list of dictionaries
        records = df.to_dict('records')
        
        # Counter for tracking imports
        imported_count = 0
        updated_count = 0
        error_count = 0
        
        for record in records:
            # Check if employee already exists
            existing_employee = session.query(Employee).filter_by(
                employee_id=record['employee_id']
            ).first()
            
            try:
                # Convert birth_date to python date if it's not NaN
                if 'birth_date' in record and pd.notna(record['birth_date']):
                    birth_date = record['birth_date']
                    if not isinstance(birth_date, datetime) and not isinstance(birth_date, pd.Timestamp):
                        # Try to parse as string
                        birth_date = pd.to_datetime(birth_date).date()
                    else:
                        birth_date = birth_date.date()
                    record['birth_date'] = birth_date
                else:
                    record['birth_date'] = None
                
                if existing_employee:
                    # Update existing employee
                    for key, value in record.items():
                        if key in record and hasattr(existing_employee, key):
                            setattr(existing_employee, key, value)
                    
                    existing_employee.updated_at = datetime.now()
                    updated_count += 1
                else:
                    # Create new employee
                    new_employee = Employee(**record)
                    session.add(new_employee)
                    imported_count += 1
            
            except Exception as e:
                error_count += 1
                logger.error(f"Error importing record: {str(e)}")
                logger.error(f"Record data: {record}")
                continue
        
        # Commit the session
        session.commit()
        
        message = f"Import completed: {imported_count} records imported, {updated_count} records updated, {error_count} errors."
        logger.info(message)
        
        return True, message
    
    except Exception as e:
        session.rollback()
        error_message = f"Error importing data to database: {str(e)}"
        logger.error(error_message)
        return False, error_message


def get_all_employees():
    """
    Get all employees from the database.
    
    Returns:
        DataFrame: pandas DataFrame containing all employees
    """
    try:
        # Query all employees
        employees = session.query(Employee).all()
        
        # Convert to list of dictionaries
        records = [
            {c.name: getattr(employee, c.name) for c in Employee.__table__.columns}
            for employee in employees
        ]
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        return df
    
    except Exception as e:
        logger.error(f"Error retrieving employees from database: {str(e)}")
        return pd.DataFrame()


def search_employees(search_params):
    """
    Search employees based on provided parameters.
    
    Args:
        search_params: Dictionary of search parameters
        
    Returns:
        DataFrame: pandas DataFrame containing search results
    """
    try:
        # Start with base query
        query = session.query(Employee)
        
        # Apply filters
        if search_params.get('name'):
            query = query.filter(Employee.name.ilike(f"%{search_params['name']}%"))
        
        if search_params.get('employee_id'):
            query = query.filter(Employee.employee_id.ilike(f"%{search_params['employee_id']}%"))
        
        if search_params.get('department'):
            query = query.filter(Employee.department == search_params['department'])
        
        if search_params.get('job_category'):
            query = query.filter(Employee.job_category == search_params['job_category'])
        
        if search_params.get('workplace'):
            query = query.filter(Employee.workplace == search_params['workplace'])
        
        # Execute query
        employees = query.all()
        
        # Convert to list of dictionaries
        records = [
            {c.name: getattr(employee, c.name) for c in Employee.__table__.columns}
            for employee in employees
        ]
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        return df
    
    except Exception as e:
        logger.error(f"Error searching employees: {str(e)}")
        return pd.DataFrame()


def get_departments():
    """
    Get list of all departments.
    
    Returns:
        list: List of department names
    """
    try:
        departments = session.query(Employee.department).distinct().all()
        return [d[0] for d in departments if d[0]]
    except Exception as e:
        logger.error(f"Error retrieving departments: {str(e)}")
        return []


def get_job_categories():
    """
    Get list of all job categories.
    
    Returns:
        list: List of job category names
    """
    try:
        categories = session.query(Employee.job_category).distinct().all()
        return [c[0] for c in categories if c[0]]
    except Exception as e:
        logger.error(f"Error retrieving job categories: {str(e)}")
        return []


def get_workplaces():
    """
    Get list of all workplaces.
    
    Returns:
        list: List of workplace names
    """
    try:
        workplaces = session.query(Employee.workplace).distinct().all()
        return [w[0] for w in workplaces if w[0]]
    except Exception as e:
        logger.error(f"Error retrieving workplaces: {str(e)}")
        return []


def delete_employee(employee_id):
    """
    Delete an employee by employee_id.
    
    Args:
        employee_id: The employee_id to delete
        
    Returns:
        tuple: (success, message)
    """
    try:
        employee = session.query(Employee).filter_by(employee_id=employee_id).first()
        
        if not employee:
            return False, "الموظف غير موجود."
        
        session.delete(employee)
        session.commit()
        
        return True, "تم حذف الموظف بنجاح."
    
    except Exception as e:
        session.rollback()
        error_message = f"خطأ في حذف الموظف: {str(e)}"
        logger.error(error_message)
        return False, error_message


def update_employee(employee_id, data):
    """
    Update an employee by employee_id.
    
    Args:
        employee_id: The employee_id to update
        data: Dictionary of fields to update
        
    Returns:
        tuple: (success, message)
    """
    try:
        employee = session.query(Employee).filter_by(employee_id=employee_id).first()
        
        if not employee:
            return False, "الموظف غير موجود."
        
        # Update fields
        for key, value in data.items():
            if hasattr(employee, key):
                setattr(employee, key, value)
        
        employee.updated_at = datetime.now()
        
        session.commit()
        
        return True, "تم تحديث بيانات الموظف بنجاح."
    
    except Exception as e:
        session.rollback()
        error_message = f"خطأ في تحديث بيانات الموظف: {str(e)}"
        logger.error(error_message)
        return False, error_message


def add_employee(data):
    """
    Add a new employee.
    
    Args:
        data: Dictionary of employee data
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Check if employee already exists
        existing = session.query(Employee).filter_by(employee_id=data['employee_id']).first()
        
        if existing:
            return False, "موظف بنفس الرقم الوظيفي موجود بالفعل."
        
        # Create new employee
        new_employee = Employee(**data)
        session.add(new_employee)
        session.commit()
        
        return True, "تمت إضافة الموظف بنجاح."
    
    except Exception as e:
        session.rollback()
        error_message = f"خطأ في إضافة الموظف: {str(e)}"
        logger.error(error_message)
        return False, error_message


# Initialize the database when the module is imported
if DATABASE_URL:
    init_db()
else:
    logger.error("DATABASE_URL environment variable not set.")