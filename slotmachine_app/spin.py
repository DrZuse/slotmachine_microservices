import pika
import oracledb
import json
import random

# Establish the database connection
db_conn = oracledb.connect(user="system", password="psWd123", dsn="oracle-db:1521/XEPDB1")
cursor = db_conn.cursor()

# Create a connection to the RabbitMQ server
rabbit_conn = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq-container'))
chann_consum = rabbit_conn.channel()

def generate_statement(win_probability):
    # Generate a random number between 0 and 1
    random_number = random.random()
    
    # Check if the random number is less than the probability of being true
    if random_number < win_probability:
        return True
    else:
        return False

def win(spins):
    winning_spins = [1, 3]
    if spins in winning_spins:
        # Define the probability of the statement being true (e.g., 0.7 for 70% true)
        win_probability = 0.7
    else:
        win_probability = 0.1

    # Generate a statement with the defined probability
    result = generate_statement(win_probability)

    print(f"The statement is {result}")

    return result

def send_to_rabbit(queue, message):
    print(f'send to rabbit queue: {queue} || message: {message}')

    chann_send = rabbit_conn.channel()
    # Declare a queue (create it if it doesn't exist)
    chann_send.queue_declare(queue)
    # Publish the message to the queue
    chann_send.basic_publish(exchange='', routing_key=queue, body=message)

def callback(ch, method, properties, body):
    print(f"Received message from 'spin' queue: {body.decode()}")
    spin_data = json.loads(body.decode())
    user_id = spin_data['user_id']

    # SQL statement to fetch a row from the table
    select_sql = f"SELECT * FROM users WHERE user_id = '{user_id}'"

    # Prepare the UPDATE statement
    update_sql = """
        UPDATE users
        SET credit = :credit, spins = :spins
        WHERE user_id = :user_id
    """

    try:
        cursor.execute(select_sql) # Execute the SQL statement to fetch data       
        row = cursor.fetchone() # Fetch the row as a tuple
        print(row)

        if row is None:
            send_to_rabbit(f'user_data_{user_id}', json.dumps('user not found'))
            return
        
    except oracledb.DatabaseError as e:
        error, = e.args
        print('Database error occurred:', error)
        send_to_rabbit(f'user_data_{user_id}', json.dumps(error))
    except Exception as e:
        print('Error occurred:', e)
        send_to_rabbit(f'user_data_{user_id}', json.dumps(e))
    else:
        if row[1] == 0: # credit check
            print('No money no honey')
            data = {'user_id': row[0], 'credit': row[1], 'spins': row[2], 'win': False}
            send_to_rabbit(f'user_data_{user_id}', json.dumps(data))
            return
        
        spin_res = win(row[2])
        credit = row[1] + 3 if spin_res else row[1] - 1
        spins = row[2]+1

        try:
            # Execute the UPDATE statement
            cursor.execute(update_sql, credit=credit, spins=spins, user_id=user_id)
            db_conn.commit()
        except oracledb.DatabaseError as e:
            error, = e.args
            print('Database error occurred:', error)
            send_to_rabbit(f'user_data_{user_id}', json.dumps(error))
        except Exception as e:
            print('Error occurred:', e)
            send_to_rabbit(f'user_data_{user_id}', json.dumps(e))
        else:
            data = {'user_id': row[0], 'credit': credit, 'spins': spins, 'win': spin_res}
            send_to_rabbit(f'user_data_{user_id}', json.dumps(data))


# Declare the queue to consume messages from
queue_name = 'spin'
chann_consum.queue_declare(queue=queue_name)

# Set up a consumer and specify the callback function to handle incoming messages
chann_consum.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

print('Waiting for messages...')
chann_consum.start_consuming()