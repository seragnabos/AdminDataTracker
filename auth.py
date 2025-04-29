
import streamlit as st
from database import engine, Base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
import hashlib

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_admin = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<User(employee_id='{self.employee_id}')>"

def init_auth():
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create admin user if not exists
    admin = session.query(User).filter_by(employee_id='Stickyfingaz420').first()
    if not admin:
        password = 'Fuckthafucknworld'
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        admin = User(employee_id='Stickyfingaz420', password_hash=password_hash, is_admin=True)
        session.add(admin)
        session.commit()
    
    session.close()

def verify_user(employee_id, password):
    Session = sessionmaker(bind=engine)
    session = Session()
    user = session.query(User).filter_by(employee_id=employee_id).first()
    session.close()
    
    if user and user.password_hash == hashlib.sha256(password.encode()).hexdigest():
        return user
    return None

def is_admin():
    return st.session_state.get('is_admin', False)

def login_required(func):
    def wrapper(*args, **kwargs):
        if not st.session_state.get('logged_in', False):
            st.warning('يرجى تسجيل الدخول أولاً')
            show_login()
            return
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    def wrapper(*args, **kwargs):
        if not st.session_state.get('is_admin', False):
            st.error('هذه الصفحة متاحة فقط للمشرفين')
            return
        return func(*args, **kwargs)
    return wrapper

def show_login():
    st.markdown('<h2 style="text-align: center;">تسجيل الدخول</h2>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        employee_id = st.text_input("الرقم الوظيفي")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول")
        
        if submitted:
            user = verify_user(employee_id, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.is_admin = user.is_admin
                st.session_state.current_user = user.employee_id
                st.success('تم تسجيل الدخول بنجاح')
                st.rerun()
            else:
                st.error('خطأ في الرقم الوظيفي أو كلمة المرور')

def show_admin_panel():
    st.markdown('<h2 style="text-align: center;">لوحة التحكم</h2>', unsafe_allow_html=True)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    tab1, tab2 = st.tabs(["إضافة مستخدم", "إدارة المستخدمين"])
    
    with tab1:
        with st.form("add_user_form"):
            new_employee_id = st.text_input("الرقم الوظيفي")
            new_password = st.text_input("كلمة المرور", type="password")
            is_admin = st.checkbox("مشرف النظام")
            submitted = st.form_submit_button("إضافة")
            
            if submitted:
                if new_employee_id and new_password:
                    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                    new_user = User(employee_id=new_employee_id, password_hash=password_hash, is_admin=is_admin)
                    session.add(new_user)
                    try:
                        session.commit()
                        st.success('تم إضافة المستخدم بنجاح')
                    except:
                        session.rollback()
                        st.error('خطأ: الرقم الوظيفي مستخدم مسبقاً')
                else:
                    st.error('يرجى تعبئة جميع الحقول')
    
    with tab2:
        users = session.query(User).all()
        for user in users:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"الرقم الوظيفي: {user.employee_id} {'(مشرف)' if user.is_admin else ''}")
            with col2:
                if user.employee_id != 'Stickyfingaz420':  # Don't allow deleting main admin
                    if st.button('حذف', key=f'del_{user.employee_id}'):
                        session.delete(user)
                        session.commit()
                        st.success('تم حذف المستخدم')
                        st.rerun()
    
    session.close()
