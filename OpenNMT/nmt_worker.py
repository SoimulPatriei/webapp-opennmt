import pika
import json
import tempfile
import os
import time
import yaml

# Load configuration from nmt_config.yaml
CONFIG_FILE = "nmt_config.yaml"
with open(CONFIG_FILE, 'r') as config_file:
    config = yaml.safe_load(config_file)
model_path = config.get("model_path", "OpenNMT/models/model.pt")

def process_translation(input_text):
    """
    Process translation using OpenNMT with temporary files for concurrency safety.
    """
    try:
        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt") as temp_input, \
             tempfile.NamedTemporaryFile(delete=False, mode="r", suffix=".txt") as temp_output:
            
            # Write the input text to the temporary input file
            temp_input.write(input_text)
            temp_input.close()  # Ensure the file is written to disk

            # Construct the command with temporary file paths
            command = f"onmt_translate -model {model_path} -src {temp_input.name} -output {temp_output.name} --verbose --ban_unk_token"
            print(f"Running command: {command}")
            
            # Run the translation command
            os.system(command)

            # Read the translated text from the output file
            translated_text = temp_output.read()

        print(f"Translation result: {translated_text.strip()}")

        return translated_text.strip()
    except Exception as e:
        print(f"Error in process_translation: {e}")
        return "Error during translation."
    finally:
        # Clean up temporary files
        try:
            os.unlink(temp_input.name)
            os.unlink(temp_output.name)
        except Exception as cleanup_error:
            print(f"Error cleaning up temporary files: {cleanup_error}")

def connect_to_rabbitmq():
    """
    Establish a connection to RabbitMQ with retries on failure.
    """
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            channel = connection.channel()
            print("Connected to RabbitMQ")
            return connection, channel
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def on_message(ch, method, props, body):
    """
    Process incoming messages and send the translated result back to the callback queue.
    """
    try:
        # Parse the incoming message
        data = json.loads(body)
        input_text = data.get('text', '')

        # Perform the translation
        translated_text = process_translation(input_text)

        # Send the response back to the callback queue
        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=json.dumps({"translation": translated_text})
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"Processed message: {input_text}")
    except Exception as e:
        print(f"Error processing message: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":
    # Connect to RabbitMQ
    connection, channel = connect_to_rabbitmq()

    # Declare the queue for incoming translation requests
    channel.queue_declare(queue='nmt_queue')

    # Start consuming messages from the 'nmt_queue'
    print("Worker is waiting for messages...")
    channel.basic_consume(queue='nmt_queue', on_message_callback=on_message)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Stopping worker...")
        channel.stop_consuming()
    finally:
        connection.close()
