from confluent_kafka import Producer, Consumer, KafkaError
from flask import Flask, jsonify, request
import random
import string
import json
from threading import Thread
from flask_cors import CORS
app = Flask(__name__)
KAFKA_BROKER_URL = 'localhost:9092'
KAFKA_TOPIC = 'sms-messages'
KAFKA_STATUS_TOPIC = 'sender-status-updates'
MESSAGES_TOTAL = 10
MESSAGE_LENGTH = 100
producer = Producer({'bootstrap.servers': KAFKA_BROKER_URL})
senders_data_log = {}


def update_senders_data(status):
    senders_data_log[status['sender_id']] = status

def status_update_receiver():
    receiving_message_update = Consumer({
        'bootstrap.servers': KAFKA_BROKER_URL,
        'group.id': 'status_update_consumer_group',
        'auto.offset.reset': 'earliest'
    })

    receiving_message_update.subscribe([KAFKA_STATUS_TOPIC])

    try:
        while True:
            msg = receiving_message_update.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break

            status_update = json.loads(msg.value().decode('utf-8'))
            update_senders_data(status_update)
            print(f"Received status update: {status_update}")

    except KeyboardInterrupt:
        pass
    finally:
        receiving_message_update.close()


def produce_message(message):
    producer.produce(KAFKA_TOPIC, key=None, value=json.dumps(message))

@app.route('/monitor', methods=['GET'])
def monitor():
    stats = {"messages_sent": '', "messages_failed": '', "average_time_per_message": ''}
    success = 0
    failed = 0
    total_time = 0
    for eachData in senders_data_log.keys():
        success += senders_data_log[eachData]['success_count']
        failed += senders_data_log[eachData]['failed_count']
        total_time += senders_data_log[eachData]['total_processing_time']
    stats["messages_sent"] = success
    stats["messages_failed"] = failed
    if(success == 0 and failed == 0):
        stats["average_time_per_message"] = -1
    else:
        stats["average_time_per_message"] = total_time / (success + failed)
    response = jsonify(stats)
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    return response

@app.route('/produce-messages', methods=['POST'])
def produce():
    num_messages = request.json.get('num_messages', MESSAGES_TOTAL)

    for each_message in range(num_messages):
        message_content = ''.join(random.choices(string.ascii_letters, k=MESSAGE_LENGTH))
        phone_number = ''.join(random.choices(string.digits, k=10))
        message = {'content': message_content, 'number': phone_number}
        produce_message(message)

    return jsonify({'message': f'Successfully produced {num_messages} messages'}), 200


# This is executed when the Flask app starts, starting the Kafka consumer in a new thread.
def start_kafka_consumer():
    status_thread = Thread(target=status_update_receiver)
    status_thread.daemon = True  # setting as a daemon thread to terminate when the main thread ends
    status_thread.start()


start_kafka_consumer()
if __name__ == "__main__":
    CORS(app)
    app.run(debug=True)

