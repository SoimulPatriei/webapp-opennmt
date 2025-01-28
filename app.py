from flask import Flask, request, jsonify, render_template
import pika, json, re, uuid, nltk

# Ensure NLTK resources are available
nltk.download('punkt')
nltk.download('punkt_tab')

app = Flask(__name__, static_folder='static')

# RabbitMQ connection settings
rabbitmq_host = 'rabbitmq'
connection = None
channel = None

def connect_to_rabbitmq():
    """Establish a connection to RabbitMQ and open a channel with a longer heartbeat."""
    global connection, channel
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=rabbitmq_host,
        heartbeat=600  # Set a 10-minute heartbeat interval (600 seconds)
    ))
    channel = connection.channel()
    channel.queue_declare(queue='nmt_queue')  # Declare the NMT queue

connect_to_rabbitmq()

@app.route('/')
def index():
    return render_template('simplification_interface.html')  # Render the main interface

@app.route('/nmt_simplify', methods=['POST'])
def nmt_simplify():
    """Simplify using the OpenNMT model."""
    global connection, channel

    # Reconnect if the channel is closed
    if connection.is_closed or channel.is_closed:
        connect_to_rabbitmq()

    try:
        if not request.is_json:
            return jsonify({"error": "Unsupported Media Type. Expecting JSON data."}), 415

        data = request.get_json()
        input_text = data.get('text', '')

        if not input_text:
            return jsonify({"error": "Text field is empty."}), 400

        # Extract numbers and replace them with @ARV
        numbers = re.findall(r'\b\d+\b', input_text)
        processed_input = re.sub(r'\b\d+\b', '@ARV', " ".join(nltk.word_tokenize(input_text.lower())))

        # Create a callback queue for receiving the response
        result = channel.queue_declare(queue='', exclusive=True)
        callback_queue = result.method.queue

        corr_id = str(uuid.uuid4())  # Unique identifier for this request
        response = None

        def on_response(ch, method, props, body):
            """Callback to handle the response message."""
            nonlocal response
            if corr_id == props.correlation_id:
                response = body

        # Consume messages from the callback queue
        channel.basic_consume(queue=callback_queue, on_message_callback=on_response, auto_ack=True)

        # Publish the input to the NMT queue
        channel.basic_publish(
            exchange='',
            routing_key='nmt_queue',
            properties=pika.BasicProperties(
                reply_to=callback_queue,
                correlation_id=corr_id,
            ),
            body=json.dumps({"text": processed_input})
        )

        # Wait for the response
        while response is None:
            connection.process_data_events()

        # Decode the response and post-process
        translated_text = json.loads(response.decode('utf-8'))["translation"]
        translated_text = '. '.join([x.strip().capitalize() for x in translated_text.split(' .')])
        translated_text = translated_text.replace(' ,', ',')

        # Replace @ARV with original numbers
        for number in numbers:
            translated_text = re.sub(r'@arv|@ARV', number, translated_text, count=1)

        return jsonify({"translation": translated_text})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Handle errors gracefully

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
