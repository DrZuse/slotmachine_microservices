import tornado.ioloop, tornado.web
import asyncio, json
import pika

def send_to_rabbit(queue, message):
    # Create a connection to the RabbitMQ server
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq-container', port=5672))
    # Establish the RabbitMQ connection
    channel_send = connection.channel()

    # Declare a queue (create it if it doesn't exist)
    channel_send.queue_declare(queue=queue)

    # Publish the message to the queue
    channel_send.basic_publish(exchange='',
        routing_key=queue, body=message)

    # Close the connection
    connection.close()

def get_one_message(queue):
    # Establish the RabbitMQ connection
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq-container', port=5672))

    # Create a channel
    channel_get = connection.channel()

    # Declare the queue
    channel_get.queue_declare(queue)

    res = []
    def callback(ch, _method, _properties, message):
        # Stop consuming and close the connection
        ch.stop_consuming()
        connection.close()
        res.append(message)

    # Start consuming and wait for a message
    channel_get.basic_consume(queue, on_message_callback=callback, auto_ack=True)

    try:
        channel_get.start_consuming()
    except KeyboardInterrupt:
        channel_get.stop_consuming()
        connection.close()

    return res

# Respond with an empty 204 No Content status code to disable favicon requests
class FaviconHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_status(204)
        self.finish()

class MainHandler(tornado.web.RequestHandler):
    async def get(self):
        self.render("index.html")

class NewuserHandler(tornado.web.RequestHandler):
    async def get(self):
        # send message to rabbit to create new user
        send_to_rabbit('new_user', 'create')
        # get new user id
        resp = get_one_message('new_user_data')[0]
        self.set_header("Content-Type", "application/json")
        self.write(resp)

class SpinHandler(tornado.web.RequestHandler):
    async def get(self, user_id):
        # send message to rabbit queue 'spin' with 'user_id
        send_to_rabbit('spin', json.dumps({'user_id': user_id}))
        # get spin result
        resp = get_one_message(f'user_data_{user_id}')[0]
        self.set_header("Content-Type", "application/json")
        self.write(resp)

# This is just an example of async I/O
class LongHandler(tornado.web.RequestHandler):
    async def get(self):
        await asyncio.sleep(10)
        self.set_header("Content-Type", "application/json")
        self.write({"long request": "10 sec"})

def make_app():
    return tornado.web.Application([
        (r"/favicon.ico", FaviconHandler),
        (r"/", MainHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"}),
        (r"/new_user.json", NewuserHandler),
        (r"/spin/([0-9]+).json", SpinHandler),
        (r"/long.json", LongHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()