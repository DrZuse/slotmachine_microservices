import pika
import oracledb
import json

# Establish the database connection
db_conn = oracledb.connect(user="system", password="psWd123", dsn="oracle-db:1521/XEPDB1")

# Create a cursor object
cursor = db_conn.cursor()

# SQL statement to create a table
table_name = 'users'
create_table_sql = f"""
    CREATE TABLE {table_name.upper()} (
        user_id NUMBER(5) PRIMARY KEY,
        credit NUMBER(10),
        spins NUMBER(10)
    )
"""

# try to create table 'users' 
try:
    # Execute the SQL statement to create a table
    cursor.execute(create_table_sql)
    # Commit the transaction
    db_conn.commit()
except oracledb.DatabaseError as e:
    error, = e.args
    if error.code == 955:
        print('Table already exists')
    else:
        print('Database error occurred:', error)
except Exception as e:
    print('Error occurred:', e)

try:
    # SQL statement to create a sequence
    create_sequence_sql = "CREATE SEQUENCE users_seq START WITH 1 INCREMENT BY 1"

    # SQL statement to create a trigger
    create_trigger_sql = """
    CREATE OR REPLACE TRIGGER users_trigger
    BEFORE INSERT ON users
    FOR EACH ROW
    BEGIN
        SELECT users_seq.NEXTVAL INTO :new.user_id FROM dual;
    END;
    """

    # Execute the SQL statement to create a sequence
    cursor.execute(create_sequence_sql)

    # Execute the SQL statement to create a trigger
    cursor.execute(create_trigger_sql)

except oracledb.DatabaseError as e:
    error, = e.args
    print('Database error occurred:', error)
except Exception as e:
    print('Error occurred:', e)

# Create a connection to the RabbitMQ server
rabbit_conn = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq-container'))

def send_to_rabbit(queue, message):
    chann_send = rabbit_conn.channel()
    # Declare a queue (create it if it doesn't exist)
    chann_send.queue_declare(queue)
    # Publish the message to the queue
    chann_send.basic_publish(exchange='', routing_key=queue, body=message)

def callback(ch, _method, _properties, body):
    if body.decode() == 'create':
        # SQL statement to insert a new row into the table
        insert_sql = "INSERT INTO users (credit, spins) VALUES (:1, :2)"

        # Data to be inserted
        data = (10, 0) # init user with $10 credit and 0 spins
        
        try:
            # Execute the SQL statement to insert a row
            cursor.execute(insert_sql, data)
            # Commit the transaction
            db_conn.commit()
        except oracledb.DatabaseError as e:
            error, = e.args
            print('Database error occurred:', error)
        except Exception as e:
            print('Error occurred:', e)

        # SQL statement to fetch the last row from the table
        select_sql = "SELECT * FROM users ORDER BY user_id DESC FETCH FIRST 1 ROWS ONLY"

        try:
            # Execute the SQL statement to fetch data
            cursor.execute(select_sql)
            # Fetch the row as a tuple
            row = cursor.fetchone()
        except oracledb.DatabaseError as e:
            error, = e.args
            print('Database error occurred:', error)
        except Exception as e:
            print('Error occurred:', e)
        else:
            data = {'user_id': row[0], 'credit': row[1]}
            send_to_rabbit('new_user_data', json.dumps(data))
    return

channel = rabbit_conn.channel()

queue_name = 'new_user'
# Declare the queue to consume messages from
channel.queue_declare(queue_name)
# Set up a consumer and specify the callback function to handle incoming messages
channel.basic_consume(queue_name, on_message_callback=callback, auto_ack=True)

print('Waiting for messages...')
channel.start_consuming()

# Close the cursor and connection
cursor.close()
db_conn.close()