import pyodbc
import datetime

# Set connection info
server = '192.168.41.22'
database = 'Db_RPA'
username_DB = 'ndd_viewer'
password_DB = 'ioas!@#ibusad$%$!@asd3'

# Run connection
conn = pyodbc.connect('Driver={SQL Server}; Server='+server+';Database='+database+';uid='+username_DB+';pwd='+ password_DB)

if conn:
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(data) FROM [Db_RPA].[dbo].[vw_NDD]")
    NDD_last_input_date = cursor.fetchone()[0]
else:
    print('Falha ao estabelecer conexão.')

# Close the cursor and the connection
cursor.close()
conn.close()
print(NDD_last_input_date)

# Convert NDD_last_input_date to datetime if it's not None
if NDD_last_input_date:
    NDD_last_input_date = datetime.datetime.strptime(str(NDD_last_input_date), "%Y-%m-%d %H:%M:%S")

# Get current date
current_date = datetime.datetime.now().date()

# Calculate the difference in days
if NDD_last_input_date:
    difference = (current_date - NDD_last_input_date.date()).days
    difference = int(difference)
else:
    pass
print(difference)
