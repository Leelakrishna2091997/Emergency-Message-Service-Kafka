from confluent_kafka import Consumer, KafkaException, Producer, KafkaError
import json
import threading
import time

KAFKA_BROKER_URL = 'localhost:9092'
KAFKA_TOPIC = 'sms-messages'
STATUS_TOPIC = 'sender-status-updates'
GROUP_ID = 'sms-sender-group'

class Sender(threading.Thread):

    def __init__(self, sender_id, error_rate, processing_time):
        super().__init__()
        self.sender_id = sender_id
        self.consumer = Consumer({
            'bootstrap.servers': KAFKA_BROKER_URL,
            'group.id': GROUP_ID,
            'auto.offset.reset': 'earliest',
        })
        self.producer = Producer({'bootstrap.servers': KAFKA_BROKER_URL})
        self.success_count = 0
        self.total_msgs = 0
        self.failed_count = 0
        self.error_rate = error_rate
        self.fail_after_msgs = 100/error_rate
        self.processing_time = processing_time

    def run(self):
        self.poll_messages()

    def poll_messages(self):
        self.consumer.subscribe([KAFKA_TOPIC])
        print("processing messages")
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(msg.error())
                        break
                self.total_msgs += 1
                start_time = time.time()
                time.sleep(self.processing_time)
                end_time = time.time()
                if(self.total_msgs % self.fail_after_msgs == 0):
                    self.failed_count +=1
                else:
                    self.success_count += 1
                processing_time = end_time - start_time
                status_update = {
                    'sender_id': self.sender_id,
                    'success_count': self.success_count,
                    'failed_count': self.failed_count,
                    'total_processing_time': processing_time*(self.success_count+self.failed_count)
                }
                print("Sending messages to the status producer")
                self.producer.produce(STATUS_TOPIC, key=str(self.sender_id), value=json.dumps(status_update))
        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()

def main():
    num_senders = 2
    senders = []
    settings = [[10, 2], [20, 1]] # Setting of the error rate and processing times for each sender.
    index = 0
    for i in range(num_senders):
        sender = Sender(sender_id=f'sender_{i}', error_rate=settings[index][0], processing_time=settings[index][1])
        sender.start()
        senders.append(sender)
        index += 1

    for sender in senders:
        sender.join()

if __name__ == '__main__':
    main()
