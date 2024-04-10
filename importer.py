from app import app
from app.models import Power
from app import db
from datetime import datetime
import pika

import csv



def loadString(date, power, powerUnit):
    powerString = Power(
        date=datetime.strptime(date, "%d.%m.%Y"),
        power=power.replace(",", "."),
        powerUnit=powerUnit
    )
    db.session.add(powerString)
    db.session.commit()
    print(powerString)
    pass

def printFile():
    with open(app.config['FILEIMPORT'], "r", encoding="utf8", ) as filedesc:
        reader = csv.reader(filedesc, delimiter="\t")
        then = False
        for i in reader:
            if then:
                loadString(i[0], i[2], i[1])
            else:
                then = True

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='powerImport', durable=True)

def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    with app.app_context():
        printFile()
    print(" [x] Done")
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='powerImport', on_message_callback=callback)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()



