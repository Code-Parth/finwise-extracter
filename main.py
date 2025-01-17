import os
from supabase import create_client
import pandas as pd
from datetime import datetime
import getpass

# Supabase configuration
SUPABASE_URL = "https://tpkhdaytqdsdxwupgkrp.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwa2hkYXl0cWRzZHh3dXBna3JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY2NTMyOTEsImV4cCI6MjA1MjIyOTI5MX0.Yov57tBy-b9QsjtaO1_BsfVvOPg0uAnivbQwrfpHRsw"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def authenticate():
    """
    Authenticate user with email and password
    """
    print("\nPlease login to access your data:")
    email = input("Email: ")
    password = getpass.getpass("Password: ")

    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        print("Authentication successful!")
        return auth_response
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        return None


def fetch_and_save_table(table_name):
    """
    Fetch data from a Supabase table and save it as a CSV file
    """
    try:
        # Fetch all data from the table
        response = supabase.table(table_name).select("*").execute()

        if response.data:
            # Convert to DataFrame
            df = pd.DataFrame(response.data)

            # Create output directory if it doesn't exist
            os.makedirs('supabase_exports', exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"supabase_exports/{table_name}_{timestamp}.csv"

            # Save to CSV
            df.to_csv(filename, index=False)
            print(f"Successfully exported {table_name} to {filename}")
            print(f"Number of records: {len(df)}")

            # Print column names and first few rows
            print("\nColumns:", df.columns.tolist())
            print("\nFirst few rows:")
            print(df.head())
        else:
            print(f"No data found in table: {table_name}")

    except Exception as e:
        print(f"Error exporting {table_name}: {str(e)}")


def main():
    print("Starting Supabase data export...")

    # Authenticate user first
    auth_response = authenticate()
    if not auth_response:
        print("Export cancelled due to authentication failure.")
        return

    # List of tables to export
    tables = ['expenses', 'profiles']

    for table in tables:
        print(f"\nProcessing table: {table}")
        fetch_and_save_table(table)

    print("\nExport complete!")


if __name__ == "__main__":
    main()
