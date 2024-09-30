import pymysql
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt
import time
import concurrent.futures
import random
import numpy as np

# @Author: Ludmila Yung

# mongo connection
client = MongoClient('localhost', 27017)
db = client['prescriptions']
collection = db['healthCare']


def mongo_search(column, value, sleep_time=0):
    time.sleep(sleep_time)
    # Simple query
    results_mongo = collection.find({column: value})
    # The results
    for document in results_mongo:
        print(document)
    # Closing MongoDB connection


# mongo_search('subject_id', 40124, 0)

# mysql connection
mysql_conn = pymysql.connect(
    host='localhost',
    port=3309,
    user='root',
    password='ohmy5_',
    database='teste'
)


def mysql_search(tabela, chave, sleep_time=0):
    time.sleep(sleep_time)
    try:
        # Create a cursor object
        with mysql_conn.cursor() as cursor:
            # SQL query
            sql_query = f"SELECT * from patients WHERE {tabela} = %s;"

            # Execute the query
            cursor.execute(sql_query, (chave,))  # cursor.execute(sql_query, ("42292",)) EXAMPLE

            # Fetch all the results
            results = cursor.fetchall()

            # Process the results
            for row in results:
                print(row)

    except pymysql.connect.Error as e:
        print("Error:", e)
    # finally:
        # Close the connection
    #     mysql_conn.close()


# mysql_search('subject_id', 40124, 0)

# Read CSV into DataFrame
csv_data = pd.read_csv(
    'C:/Users/lud_y/Downloads/Dissertação/Dados/mimic-iii-clinical-database-demo-1.4/mimic-iii-clinical-database-demo-1.4/CHARTEVENTS.csv')


# print(csv_data.head())
def csv_search(campo, chave, sleep_time=0):
    time.sleep(sleep_time)
    print(csv_data.loc[csv_data.index[csv_data[campo] == chave]])


# csv_search('subject_id', 40124, 0)


# Example query to use all data sources
def polystore_search(data_info, key, sleep_time=0):
    sleep_time = 5 # Affects the execution time

    with concurrent.futures.ThreadPoolExecutor() as executor:
        result1 = executor.submit(mysql_search, data_info, key, sleep_time)
        result2 = executor.submit(mongo_search, data_info, key, sleep_time)
        result3 = executor.submit(csv_search, data_info, key, sleep_time)

    # Wait for all tasks to complete
    concurrent.futures.wait([result1, result2, result3])

    # Get the results
    return {
        'MySQL': result1.result(),
        'MongoDB': result2.result(),
        'Database': result3.result()
    }


start_time = time.time()  # Record the start time
polystore_search('subject_id', 40124, 3)
end_time = time.time()  # Record the end time
execution_time = end_time - start_time  # Calculate the execution time
print(f"Execution time: {execution_time:.4f} seconds")


# Make this more visual
def select_table_and_key(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print("Tables in MySQL database:")
        for table in tables:
            print(table)
        selected_table = input("Enter the name of the table you want to select: ")

        cursor.execute(f"SHOW COLUMNS FROM {selected_table}")
        columns = [column[0] for column in cursor.fetchall()]
        print("Columns in the selected table:")
        for column in columns:
            print(column)
        selected_key = input("Enter the name of the key you want to select: ")

        return selected_table, selected_key
    except pymysql.connect.Error as e:
        print("Error:", e)
        return None, None


class FogNode:
    def __init__(self, id, location, processing_power):
        self.id = id
        self.location = location
        self.processing_power = processing_power
        self.current_load = 0

    def process_data(self, processing_demand):
        if self.processing_power - self.current_load >= processing_demand:
            self.current_load += processing_demand
            return True
        else:
            return False


class CloudServer:
    def __init__(self, processing_power):
        self.processing_power = processing_power
        self.current_load = 0
        self.processing_times = []  # List to store processing times

    # def process_data(self, processing_demand):
    #     if self.processing_power - self.current_load >= processing_demand:
    #         self.current_load += processing_demand
    #         return True
    #     else:
    #         return False

    def process_data(self, processing_demand):
        start_time = time.time()  # Record start time
        if self.processing_power - self.current_load >= processing_demand:
            self.current_load += processing_demand
            # Simulate processing time
            time.sleep(processing_demand / 1000)  # Assuming processing time in milliseconds
            end_time = time.time()  # Record end time
            processing_time = end_time - start_time  # Calculate processing time
            self.processing_times.append(processing_time)  # Record processing time
            return True
        else:
            return False

    def average_processing_time(self):
        return sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0

class Environment:
    def __init__(self, fog_nodes, cloud_server, mysql_conn, client, csv_data):
        self.fog_nodes = fog_nodes
        self.cloud_server = cloud_server
        self.processing_times = []
        self.fog_utilization = []
        self.cloud_utilization = []
        self.mysql_connection = mysql_conn
        self.mongo_client = client
        self.csv_file = csv_data

    def allocate_resources(self, data):
        if 'processing_demand' in data and 'subject_id' in data:
            if self.cloud_server.process_data(data['processing_demand']):
                # If cloud server can handle the processing demand, process data there
                polystore_search_result = polystore_search(data['data_info'], data['key'])
                return f"Data processed at Cloud Server using polystore_search: {polystore_search_result}"

            # If cloud server is busy, try fog nodes
            for node in self.fog_nodes:
                if node.process_data(data['processing_demand']):
                    # If fog node can handle the processing demand, process data there
                    polystore_search_result = polystore_search(data['data_info'], data['key'])
                    return f"Data processed at Fog Node {node.id} using polystore_search: {polystore_search_result}"

            # If no fog node or cloud server can handle the processing demand, return "Insufficient processing power"
            return "Insufficient processing power"
        else:
            return "Data is missing required keys"

    def average_processing_time(self):
        return sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0

    def calculate_utilization(self):
        fog_utilization = sum(node.current_load for node in self.fog_nodes) / sum(node.processing_power for node in self.fog_nodes)
        self.fog_utilization.append(fog_utilization)
        cloud_utilization = self.cloud_server.current_load / self.cloud_server.processing_power
        self.cloud_utilization.append(cloud_utilization)

def initialize_fog_nodes(num_nodes):
    fog_nodes = []
    for i in range(num_nodes):
        # Simulate fog node details
        location = np.array([random.uniform(0, 10), random.uniform(0, 10)])  # Random location
        processing_power = random.randint(10, 599)  # Random processing power
        fog_node = FogNode(i + 1, location, processing_power)
        fog_nodes.append(fog_node)
    return fog_nodes

# Function to run simulation for n times
def run_simulation(env, data, n):
    for _ in range(n):
        # Allocate resources
        result = env.allocate_resources(data)

        # Calculate utilization
        env.calculate_utilization()
    # Close the MySQL and MongoDB connections after all queries have been executed
    mysql_conn.close()
    client.close()

# Example results

polystore_search_data = {'info': 'subject_id', 'key': 40124}
# polystore_search_data = {'processing_demand': random.randint(2000, 50000), 'info': 'subject_id', 'key': 40124}

#polystore_search_data = {'processing_demand': 50, 'info': 'subject_id', 'key': 40124}


# Example of using
fog_nodes = initialize_fog_nodes(10)
cloud_server = CloudServer(600)  # Example: Cloud server with a given processing power

# Create environment
# environment = Environment(fog_nodes, cloud_server)

# Create environment with MySQL connection, MongoDB client, and the other database
environment = Environment(fog_nodes, cloud_server, mysql_conn, client, csv_data)

# Simulate data processing requests
#data1 = {'processing_demand': 50}  # Example data processing demand
#data2 = {'processing_demand': 20}  # Example data processing demand
#data3 = {'processing_demand': 15}  # Example data processing demand

#data_list = [data1, data2, data3]

# data = {'processing_demand': random.randint(20, 500)}

#data = {'processing_demand': random.randint(2000, 50000), 'info': 'subject_id', 'key': 40124}

data = {'processing_demand': random.randint(20, 50)}

# for i, data in enumerate(data_list):
#    result = environment.allocate_resources(data)
#    print(f"Data {i+1}: {result}")

n = 10000  # Change the number of iterations as needed
run_simulation(environment, data, n)

#result1 = environment.allocate_resources(data1)
#result2 = environment.allocate_resources(data2)
#result3 = environment.allocate_resources(data3)

# Measure efficiency metrics
# Calculate average processing time, fog node utilization, and cloud server utilization
# average_processing_time = environment.average_processing_time()
average_fog_utilization = sum(environment.fog_utilization) / len(environment.fog_utilization)
average_cloud_utilization = sum(environment.cloud_utilization) / len(environment.cloud_utilization)

# print("Average Processing Time:", average_processing_time)
print("Average Fog Node Utilization:", average_fog_utilization)
print("Average Cloud Server Utilization:", average_cloud_utilization)

# Calculate the gain of using fog instead of cloud

# Measure efficiency metrics
# Calculate average processing time, fog node utilization, and cloud server utilization
average_processing_time = environment.average_processing_time()  # Calculating average processing time
average_fog_utilization = sum(environment.fog_utilization) / len(environment.fog_utilization)
average_cloud_utilization = sum(environment.cloud_utilization) / len(environment.cloud_utilization)

# Calculate the gain of using fog instead of cloud

# Calculate the gain in average utilization
gain_utilization = average_fog_utilization - average_cloud_utilization

# Calculate the gain in average processing time (assuming lower is better)
average_processing_time_fog = environment.average_processing_time()  # Calculating average processing time for fog

cloud_server = CloudServer(600)  # Example: Cloud server with a given processing power
cloud_server.process_data(50)  # Example: Process data with processing demand 50
average_processing_time_cloud = cloud_server.average_processing_time()
print("Average Processing Time for Cloud Server:", average_processing_time_cloud)

gain_processing_time = average_processing_time_cloud - average_processing_time_fog

# Print the gains
print("Gain in Average Utilization (Fog vs Cloud):", gain_utilization)
print("Gain in Average Processing Time (Cloud vs Fog):", gain_processing_time)

# Plot
iterations = range(1, n + 1)
plt.plot(iterations, environment.fog_utilization, label='Fog Node Utilization', color='blue')
plt.axhline(y=average_fog_utilization, color='blue', linestyle='--', label='Average Fog Node Utilization')
plt.plot(iterations, environment.cloud_utilization, label='Cloud Server Utilization', color='orange')
plt.axhline(y=average_cloud_utilization, color='orange', linestyle='--', label='Average Cloud Server Utilization')
plt.xlabel('Iterations')
plt.ylabel('Utilization')
plt.title('Fog Node and Cloud Server Utilization Over Iterations')
plt.legend()
plt.show()
