"""Publish one isolated notification for the candidate consumer."""
import os
import pika

payload=os.environ['NOTIFICATION_TEST_PAYLOAD']
credentials=pika.PlainCredentials('migration','local-benchmark-only')
connection=pika.BlockingConnection(pika.ConnectionParameters('migration-rabbitmq',5672,'/',credentials))
channel=connection.channel()
channel.queue_declare(queue='email_candidate',durable=True)
channel.basic_publish(exchange='',routing_key='email_candidate',body=payload.encode(),
                      properties=pika.BasicProperties(delivery_mode=2))
connection.close()
print('Published to email_candidate')
