import os
import mysql.connector
import streamlit as st
import pandas as pd
import io
import toml

# Load secrets directly
secrets = st.secrets

# Access individual secrets
host = secrets['mysql']['host']
username = secrets['mysql']['user']
password = secrets['mysql']['password']
ssl_enabled = secrets['mysql']['ssl_enabled']

# Function to authenticate user credentials with MySQL database
def authenticate(username, password, host, ssl_enabled=False):
    try:
        # Establish connection to MySQL Server
        mydb = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            ssl_enabled=ssl_enabled
        )
        # Return the connection object along with authentication status
        if mydb.is_connected():
            return True, mydb
        else:
            return False, None
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return False, None

# Function to update the secrets file with new credentials
def update_secrets(secrets_file, host, username, password):
    secrets = toml.load(secrets_file)
    secrets['mysql']['host'] = host
    secrets['mysql']['user'] = username
    secrets['mysql']['password'] = password
    with open(secrets_file, 'w') as f:
        toml.dump(secrets, f)

# Create Streamlit App
def main():
    # Watermark
    st.markdown("<p style='text-align:left;color:gray;font-size:small;'>Developed by: Dopana Rohit Kumar</p>", unsafe_allow_html=True)
    # Watermark
    st.title("🤖MySQL with Streamlit web app")

    # Create a session state to store authentication status and credentials
    session_state = st.session_state

    if 'authenticated' not in session_state:
        session_state.authenticated = False

    if not session_state.authenticated:
        # Login Form
        st.subheader("Login")
        st.write("By default, the host is set to localhost.")
        host = st.text_input("Host", value=secrets['mysql']['host'], placeholder="localhost")
        username = st.text_input("Username", value=secrets['mysql']['user'])
        password = st.text_input("Password", type="password", value=secrets['mysql']['password'])
        
        if st.button("Login"):
            authenticated, db_connection = authenticate(username, password, host, secrets['mysql']['ssl_enabled'])
            if authenticated:
                session_state.authenticated = True
                session_state.db_connection = db_connection
                session_state.username = username
                session_state.password = password
                # Update the secrets file with the new credentials
                update_secrets(secrets, host, username, password)
                st.success("Login Successful!")
            else:
                st.error("Invalid username or password. Please try again.")

    if session_state.authenticated:
        # Add logout button in side panel
        if st.sidebar.button("Logout", help="Click to logout"):
            session_state.authenticated = False
            st.experimental_rerun()

        st.sidebar.subheader("Database Operations")
        perform_operations(session_state.db_connection)


# Function to reset MySQL password for a given username
def reset_password(username, old_password, new_password):
    try:
        # Connect to MySQL Server with the old password
        mydb = mysql.connector.connect(
            host="localhost",
            user=username,
            password=old_password
        )
        mycursor = mydb.cursor()

        # Reset the password for the specified username
        mycursor.execute(f"ALTER USER '{username}'@'localhost' IDENTIFIED BY '{new_password}'")
        mydb.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False


# Panel for resetting password
def reset_password_panel(host):
    username_key = "reset_username_input"
    old_password_key = "reset_old_password_input"
    new_password_key = "reset_new_password_input"
    confirm_new_password_key = "reset_confirm_new_password_input"

    username = st.text_input("Username", key=username_key)
    old_password = st.text_input("Enter Old Password", type="password", key=old_password_key)
    new_password = st.text_input("Enter New Password", type="password", key=new_password_key)
    confirm_new_password = st.text_input("Confirm New Password", type="password", key=confirm_new_password_key)
    if st.button("Reset"):
        if new_password == confirm_new_password:
            if reset_password(username, old_password, new_password, host):
                st.success("Password reset successfully!")
            else:
                st.error("Failed to reset password. Please check your old password.")
        else:
            st.error("New password and confirm password do not match.")

# Function to perform database operations
def perform_operations(db_connection):
    mycursor = db_connection.cursor()
    
    # Checkbox for uploading MySQL script file
    upload_sql_script = st.sidebar.checkbox("Upload MySQL Script File")
    if upload_sql_script:
        upload_sql_script = st.file_uploader("Upload SQL Script", type=['sql'])
        
        if upload_sql_script is not None:
            if st.button("Execute Script"):
                execute_sql_script(upload_sql_script, mycursor, db_connection)

    # Checkbox for managing database
    manage_database = st.sidebar.checkbox("Manage Database")
    if manage_database:
        manage_database_operations(mycursor, db_connection)
    else:
        perform_crud_operations(mycursor, db_connection)

# Function to execute SQL script
def execute_sql_script(uploaded_file, mycursor, db_connection):
    try:
        # Read the content of the uploaded file
        content_str = io.StringIO(uploaded_file.getvalue().decode("utf-8")).read()
        # Split the content into individual queries
        queries = content_str.split(';')
        # Execute each query
        for query in queries:
            if query.strip():
                mycursor.execute(query)
        db_connection.commit()
        st.success("SQL script executed successfully and queries added to the database.")
    except (mysql.connector.Error, ValueError) as err:
        st.error(f"An error occurred while executing the SQL script: {err}")

# Function to perform CRUD operations
def perform_crud_operations(mycursor, db_connection):
    # Checkbox for creating new database or table
    create_new_db_table = st.sidebar.checkbox("Create New Database or Table")
    if create_new_db_table:
        create_new_database_or_table(mycursor)

    # Display Options for CRUD Operations
    operation = st.sidebar.selectbox("Select an Operation", ("Create", "Read", "Update", "Delete"),
                                     placeholder='CRUD Operation', index=None)
    if operation != "Read":
        selected_database, selected_table = select_database_and_table(mycursor)

    # Perform Selected CRUD Operations
    if operation == "Create" and not create_new_db_table:
        create_record(selected_database, selected_table, mycursor, db_connection)

    elif operation == "Read":
        read_records(mycursor)

    elif operation == "Update":
        update_record(selected_database, selected_table, mycursor, db_connection)

    elif operation == "Delete":
        delete_record(selected_database, selected_table, mycursor, db_connection)

# Function to manage database operations
def manage_database_operations(mycursor, db_connection):
    selected_database = st.sidebar.selectbox("Select Database", get_all_databases(mycursor), key="manage_database_selectbox",
                                             placeholder='Select Database', index=None)
    if selected_database:
        operation = st.sidebar.selectbox("Select Operation", ("Alter Table","Truncate Table","Drop Table","Drop Database" ),
                                         index=None)
        if operation == "Alter Table":
            alter_table(selected_database, mycursor, db_connection)
        elif operation == "Truncate Table":
            truncate_table(selected_database, mycursor, db_connection)
        elif operation == "Drop Table":
            drop_table(selected_database, mycursor, db_connection)
        elif operation == "Drop Database":
            drop_database(selected_database, mycursor, db_connection)


# Function to alter table
def alter_table(selected_database, mycursor, db_connection):
    st.subheader("Alter Table")
    mycursor.execute(f"USE {selected_database}")
    selected_table = st.selectbox("Select Table to Alter", get_all_tables(selected_database, mycursor))
    if selected_table:
        try:
            # Fetching table columns
            mycursor.execute(f"DESCRIBE {selected_table}")
            table_columns = [col[0] for col in mycursor.fetchall()]
            selected_column = st.selectbox("Select Column to Alter", table_columns)
            if selected_column:
                # Fetching data type of selected column
                mycursor.execute(f"SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{selected_table}' AND COLUMN_NAME = '{selected_column}'")
                selected_column_data_type = mycursor.fetchone()[0]

                alter_option = st.radio("Select Option", ("Rename Column", "Change Column Type", "Add New Column", "Delete Column", "Rename Table"))
                if alter_option == "Rename Column":
                    new_column_name = st.text_input("Enter New Column Name (e.g., new_column int(100))")
                    if st.button("Rename") and new_column_name:
                        try:
                            mycursor.execute(f"ALTER TABLE {selected_table} CHANGE {selected_column} {new_column_name}")
                            db_connection.commit()
                            st.success("Column Renamed Successfully!!!")
                        except mysql.connector.Error as err:
                            st.error(f"Error: {err}")
                elif alter_option == "Change Column Type":
                    new_column_type = st.text_input("Enter New Column Type (e.g., int(100) or varchar(255))", placeholder=f"Current: {selected_column_data_type}")
                    if st.button("Change Type") and new_column_type:
                        try:
                            mycursor.execute(f"ALTER TABLE {selected_table} MODIFY {selected_column} {new_column_type}")
                            db_connection.commit()
                            st.success("Column Type Changed Successfully!!!")
                        except mysql.connector.Error as err:
                            st.error(f"Error: {err}")
                elif alter_option == "Add New Column":
                    new_column_input = st.text_input("Enter New Column Name and Type (e.g., new_column VARCHAR(255))")
                    if st.button("Add Column") and new_column_input:
                        try:
                            new_column_data = new_column_input.split()
                            new_column_name = new_column_data[0]
                            new_column_type = " ".join(new_column_data[1:])
                            mycursor.execute(f"ALTER TABLE {selected_table} ADD {new_column_name} {new_column_type}")
                            db_connection.commit()
                            st.success("New Column Added Successfully!!!")
                        except mysql.connector.Error as err:
                            st.error(f"Error: {err}")
                elif alter_option == "Delete Column":
                    column_to_delete = st.selectbox("Select Column to Delete", table_columns)
                    if st.button("Delete Column"):
                        try:
                            mycursor.execute(f"ALTER TABLE {selected_table} DROP COLUMN {column_to_delete}")
                            db_connection.commit()
                            st.success("Column Deleted Successfully!!!")
                        except mysql.connector.Error as err:
                            st.error(f"Error: {err}")
                elif alter_option == "Rename Table":
                    new_table_name = st.text_input("Enter New Table Name")
                    if st.button("Rename Table") and new_table_name:
                        try:
                            mycursor.execute(f"ALTER TABLE {selected_table} RENAME TO {new_table_name}")
                            db_connection.commit()
                            st.success("Table Renamed Successfully!!!")
                        except mysql.connector.Error as err:
                            st.error(f"Error: {err}")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

# Function to truncate a table
def truncate_table(selected_database, mycursor, db_connection):
    st.subheader("Truncate Table")
    mycursor.execute(f"USE {selected_database}")
    selected_table = st.selectbox("Select Table to Truncate", get_all_tables(selected_database, mycursor))
    if selected_table:
        if st.button("Truncate"):
            try:
                mycursor.execute(f"TRUNCATE TABLE {selected_table}")
                db_connection.commit()
                st.success(f"Table '{selected_table}' truncated successfully!")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")

# Function to drop table
def drop_table(selected_database, mycursor, db_connection):
    st.subheader("Drop Table")
    mycursor.execute(f"USE {selected_database}")
    selected_table = st.selectbox("Select Table to Drop", get_all_tables(selected_database, mycursor))
    if selected_table:
        if st.button("Drop"):
            try:
                mycursor.execute(f"DROP TABLE {selected_table}")
                st.success(f"Table '{selected_table}' dropped successfully!")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")

# Function to drop database
def drop_database(selected_database, mycursor, db_connection):
    st.subheader("Drop Database")
    if st.button("Drop"):
        try:
            mycursor.execute(f"DROP DATABASE {selected_database}")
            st.success(f"Database '{selected_database}' dropped successfully!")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

# Select Database and Table
def select_database_and_table(mycursor):
    st.sidebar.subheader("Select Database")
    mycursor.execute("SHOW DATABASES")
    databases = [db[0] for db in mycursor.fetchall()]
    if not databases:
        st.sidebar.warning("No databases found.")
        selected_database = None
    else:
        selected_database = st.sidebar.selectbox("Database", databases, placeholder='Select Database', index=None)

    if selected_database:
        # Select Table
        mycursor.execute(f"USE {selected_database}")
        mycursor.execute("SHOW TABLES")
        tables = [table[0] for table in mycursor.fetchall()]
        if not tables:
            st.sidebar.warning("No tables found in the selected database.")
            selected_table = None
        else:
            selected_table = st.sidebar.selectbox("Table", tables, index=0)
            # Show selected table
            st.sidebar.write(f"Selected Table: {selected_table}")
    else:
        selected_table = None

    return selected_database, selected_table

# Function to create a new database or table
def create_new_database_or_table(mycursor):
    st.subheader("Create New Database or Table")
    create_option = st.radio("Select Option", ("Database", "Table"))
    if create_option == "Database":
        create_new_database(mycursor)
    elif create_option == "Table":
        create_new_table(mycursor)

# Function to create a new database
def create_new_database(mycursor):
    new_db_name = st.text_input("Enter New Database Name:")
    if st.button("Create") and new_db_name:
        try:
            # Create new database
            mycursor.execute(f"CREATE DATABASE {new_db_name}")
            st.success(f"Database '{new_db_name}' created successfully!")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

# Function to create a new table
def create_new_table(mycursor):
    st.subheader("Create New Table")
    new_table_name = st.text_input("Enter New Table Name:")
    if st.button("Create") and new_table_name:
        try:
            # Create new table
            mycursor.execute(f"CREATE TABLE {new_table_name} (id INT AUTO_INCREMENT PRIMARY KEY)")
            st.success(f"Table '{new_table_name}' created successfully!")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

# Function to create a new record
def create_record(database, table, mycursor, db_connection):
    st.subheader("Create Record")
    if database and table:
        # Fetching table columns
        mycursor.execute(f"DESCRIBE {table}")
        table_columns = [col[0] for col in mycursor.fetchall()]
        record = {}
        for column in table_columns:
            record[column] = st.text_input(column)

        if st.button("Create"):
            try:
                # Constructing the query to insert record
                columns = ', '.join(record.keys())
                values = ', '.join([f"'{value}'" for value in record.values()])
                query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
                mycursor.execute(query)
                db_connection.commit()
                st.success("Record created successfully!")
            except mysql.connector.Error as err:
                st.error(f"Error: {err}")
    else:
        st.warning("Please select a database and a table first.")

# Function to read records
def read_records(mycursor):
    st.subheader("Read Records")
    selected_database, selected_table = select_database_and_table(mycursor)
    if selected_database and selected_table:
        try:
            # Fetching all records from the selected table
            mycursor.execute(f"SELECT * FROM {selected_table}")
            records = mycursor.fetchall()
            if records:
                # Displaying records in a DataFrame
                df = pd.DataFrame(records, columns=[col[0] for col in mycursor.description])
                st.write(df)
            else:
                st.info("No records found in the selected table.")
        except mysql.connector.Error as err:
            st.error(f"Error: {err}")

# Function to update a record
def update_record(database, table, mycursor, db_connection):
    st.subheader("Update Record")
    if database and table:
        # Fetching table columns
        mycursor.execute(f"DESCRIBE {table}")
        table_columns = [col[0] for col in mycursor.fetchall()]
        # Dropdown to select the record to update
        record_id = st.selectbox("Select Record ID", get_record_ids(table, mycursor))
        if record_id:
            # Fetching the selected record
            mycursor.execute(f"SELECT * FROM {table} WHERE id = {record_id}")
            record = mycursor.fetchone()
            if record:
                # Displaying the selected record
                st.write(f"Selected Record ID: {record_id}")
                st.write(record)
                # Input fields to update the record
                updated_record = {}
                for column in table_columns:
                    updated_record[column] = st.text_input(column, value=record[table_columns.index(column)])
                if st.button("Update"):
                    try:
                        # Constructing the query to update record
                        set_values = ', '.join([f"{key} = '{value}'" for key, value in updated_record.items()])
                        query = f"UPDATE {table} SET {set_values} WHERE id = {record_id}"
                        mycursor.execute(query)
                        db_connection.commit()
                        st.success("Record updated successfully!")
                    except mysql.connector.Error as err:
                        st.error(f"Error: {err}")
            else:
                st.warning("Record not found.")
    else:
        st.warning("Please select a database and a table first.")

# Function to delete a record
def delete_record(database, table, mycursor, db_connection):
    st.subheader("Delete Record")
    if database and table:
        # Dropdown to select the record to delete
        record_id = st.selectbox("Select Record ID", get_record_ids(table, mycursor))
        if record_id:
            # Fetching the selected record
            mycursor.execute(f"SELECT * FROM {table} WHERE id = {record_id}")
            record = mycursor.fetchone()
            if record:
                # Displaying the selected record
                st.write(f"Selected Record ID: {record_id}")
                st.write(record)
                if st.button("Delete"):
                    try:
                        # Constructing the query to delete record
                        query = f"DELETE FROM {table} WHERE id = {record_id}"
                        mycursor.execute(query)
                        db_connection.commit()
                        st.success("Record deleted successfully!")
                    except mysql.connector.Error as err:
                        st.error(f"Error: {err}")
            else:
                st.warning("Record not found.")
    else:
        st.warning("Please select a database and a table first.")

# Function to get all databases
def get_all_databases(mycursor):
    mycursor.execute("SHOW DATABASES")
    return [db[0] for db in mycursor.fetchall()]

# Function to get all tables in a database
def get_all_tables(database, mycursor):
    mycursor.execute(f"USE {database}")
    mycursor.execute("SHOW TABLES")
    return [table[0] for table in mycursor.fetchall()]

# Function to get record IDs
def get_record_ids(table, mycursor):
    mycursor.execute(f"SELECT id FROM {table}")
    return [record[0] for record in mycursor.fetchall()]

if __name__ == '__main__':
    main()
