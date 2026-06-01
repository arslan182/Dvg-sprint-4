import os
import pika
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_NAME     = os.getenv("DB_NAME", "invoice_db")
DB_USER     = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secretpassword")

RABBITMQ_HOST     = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER     = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "password")


def update_invoice_status(rechnungs_nummer):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE invoices SET status = 'BEZAHLT' WHERE rechnungs_nummer = %s",
                (rechnungs_nummer,)
            )
            conn.commit()
        conn.close()
        print(f"[DB] Status für {rechnungs_nummer} auf BEZAHLT gesetzt.")
    except Exception as e:
        print(f"[DB] Fehler: {e}")


def callback(ch, method, properties, body):
    data = json.loads(body)
    r_nr = data.get("rechnungsnummer")

    print(f"[Payment] Empfangen: Rechnung {r_nr}")

    update_invoice_status(r_nr)

    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    ))
    channel = connection.channel()
    channel.queue_declare(queue="zahlungs_auftraege", durable=True)
    channel.basic_consume(queue="zahlungs_auftraege", on_message_callback=callback)

    print("[Payment] Wartet auf Nachrichten...")
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()
