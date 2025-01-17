import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Supabase configuration
SUPABASE_URL = "https://tpkhdaytqdsdxwupgkrp.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwa2hkYXl0cWRzZHh3dXBna3JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY2NTMyOTEsImV4cCI6MjA1MjIyOTI5MX0.Yov57tBy-b9QsjtaO1_BsfVvOPg0uAnivbQwrfpHRsw"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Set page config
st.set_page_config(
    page_title="FinWise Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'auth_response' not in st.session_state:
        st.session_state.auth_response = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'dashboard'


def clear_session_data():
    """Clear all session data"""
    if hasattr(st, 'session_state'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]


def authenticate(email, password):
    """Authenticate user with email and password"""
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.session_state.authenticated = True
        st.session_state.auth_response = auth_response
        fetch_user_data(auth_response)
        return True
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
        return False


def fetch_user_data(auth_response):
    """Fetch user-specific data from all tables"""
    try:
        user_id = auth_response.user.id

        # Fetch expenses
        expenses = supabase.table('expenses').select(
            "*").eq('user_id', user_id).execute()
        st.session_state.user_data['expenses'] = pd.DataFrame(
            expenses.data) if expenses.data else pd.DataFrame()

        # Fetch profile
        profile = supabase.table('profiles').select(
            "*").eq('id', user_id).execute()
        st.session_state.user_data['profile'] = pd.DataFrame(
            profile.data) if profile.data else pd.DataFrame()

    except Exception as e:
        st.error(f"Error fetching user data: {str(e)}")


def display_dashboard():
    """Display the main dashboard"""
    st.title("Financial Dashboard")

    # Get profile data
    profile_df = st.session_state.user_data.get('profile')
    expenses_df = st.session_state.user_data.get('expenses')

    if not profile_df.empty:
        savings_goal = profile_df.iloc[0]['savings_goal']
        username = profile_df.iloc[0].get('username', 'User')
        st.header(f"Welcome, {username}")

        # Display savings goal progress
        if not expenses_df.empty:
            total_expenses = expenses_df['amount'].sum()
            progress = min(1 - (total_expenses / savings_goal), 1)

            st.subheader("Savings Goal Progress")
            progress_container = st.container()
            progress_container.progress(progress)
            progress_container.write(f"₹{total_expenses:,.2f} spent of ₹{
                                     savings_goal:,.2f} goal")

    # Display expense statistics and charts
    if not expenses_df.empty:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Expenses", f"₹{expenses_df['amount'].sum():,.2f}")
        with col2:
            st.metric("Average Expense", f"₹{
                      expenses_df['amount'].mean():,.2f}")
        with col3:
            st.metric("Number of Transactions", len(expenses_df))

        # Category breakdown
        st.subheader("Expenses by Category")
        category_data = expenses_df.groupby(
            'category')['amount'].sum().reset_index()
        fig = px.pie(category_data, values='amount',
                     names='category', hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

        # Monthly trend
        st.subheader("Monthly Expense Trend")
        expenses_df['month'] = pd.to_datetime(
            expenses_df['created_at']).dt.strftime('%Y-%m')
        monthly_data = expenses_df.groupby(
            'month')['amount'].sum().reset_index()
        fig = px.line(monthly_data, x='month', y='amount',
                      labels={'month': 'Month', 'amount': 'Total Expenses (₹)'})
        st.plotly_chart(fig, use_container_width=True)


def display_expenses():
    """Display expenses list and details"""
    st.title("Expenses History")

    # Display expenses table
    expenses_df = st.session_state.user_data.get('expenses')
    if not expenses_df.empty:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            categories = ['All'] + \
                sorted(expenses_df['category'].unique().tolist())
            selected_category = st.selectbox("Filter by Category", categories)

        with col2:
            date_range = st.date_input(
                "Date Range",
                value=(
                    pd.to_datetime(expenses_df['created_at']).min().date(),
                    pd.to_datetime(expenses_df['created_at']).max().date()
                )
            )

        # Filter data
        filtered_df = expenses_df.copy()
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['category']
                                      == selected_category]

        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['created_at']).dt.date >= date_range[0]) &
            (pd.to_datetime(
                filtered_df['created_at']).dt.date <= date_range[1])
        ]

        # Display filtered data
        for _, row in filtered_df.sort_values('created_at', ascending=False).iterrows():
            with st.expander(f"₹{row['amount']} - {row['category']} - {pd.to_datetime(row['created_at']).strftime('%Y-%m-%d')}"):
                st.write(
                    f"**Description:** {row['description'] if row['description'] else 'No description'}")
                if row.get('bill_images'):
                    st.write("**Bill Images:**")
                    for image_path in row['bill_images']:
                        try:
                            # Generate public URL for the image
                            image_url = supabase.storage.from_(
                                'bills').get_public_url(image_path)
                            if image_url:
                                st.image(
                                    image_url, caption=image_path.split('/')[-1])
                            else:
                                st.warning(f"Image not accessible: {
                                           image_path.split('/')[-1]}")
                        except Exception as e:
                            st.warning(f"Unable to load image: {
                                       image_path.split('/')[-1]}")


def display_profile():
    """Display profile information"""
    st.title("Profile Information")

    profile_df = st.session_state.user_data.get('profile')
    if not profile_df.empty:
        profile_data = profile_df.iloc[0]

        col1, col2 = st.columns(2)
        with col1:
            st.write("### Personal Details")
            st.write(
                f"**Username:** {profile_data.get('username', 'Not set')}")
            st.write(
                f"**Monthly Savings Goal:** ₹{float(profile_data.get('savings_goal', 0)):,.2f}")
            st.write(
                f"**Account Created:** {pd.to_datetime(profile_data.get('created_at')).strftime('%Y-%m-%d')}")


def main():
    # Initialize session state
    init_session_state()

    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        if st.session_state.authenticated:
            st.session_state.current_view = st.radio(
                "Select View",
                ["Dashboard", "Expenses", "Profile"]
            ).lower()

            if st.button("Logout"):
                clear_session_data()
                st.rerun()

    # Main content
    if not st.session_state.authenticated:
        st.title("FinWise Dashboard")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")

            if submit_button:
                if authenticate(email, password):
                    st.success("Login successful!")
                    st.rerun()
    else:
        # Display current view
        if st.session_state.current_view == 'dashboard':
            display_dashboard()
        elif st.session_state.current_view == 'expenses':
            display_expenses()
        elif st.session_state.current_view == 'profile':
            display_profile()


if __name__ == "__main__":
    main()
