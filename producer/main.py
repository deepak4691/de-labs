import json
import logging
import os
import random
import time
import uuid
from datetime import datetime, timezone

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "postgrespassword")
INITIAL_RETRY_DELAY = 1
MAX_RETRY_DELAY = 30


def get_db_connection():
    retry_delay = INITIAL_RETRY_DELAY

    while True:
        try:
            connection = psycopg2.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
            )
            logging.info("Connected to PostgreSQL successfully.")
            return connection
        except psycopg2.OperationalError as error:
            logging.warning(
                "Database unavailable: %s. Retrying in %s seconds...",
                error,
                retry_delay,
            )
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)


def generate_event(force_id=None, malformed=False):
    if malformed:
        return {"event_type": "purchase", "amount": "INVALID_NUMERIC"}

    return {
        "event_id": force_id or str(uuid.uuid4()),
        "event_type": random.choice(["purchase", "page_view", "add_to_cart"]),
        "user_id": random.randint(1000, 1050),
        "product_id": random.randint(500, 520),
        "amount": round(random.uniform(10.0, 500.0), 2),
        "event_time": datetime.now(timezone.utc).isoformat(),
    }


def insert_event(connection, event):
    query = """
        INSERT INTO raw_events (event_id, event_type, user_id, product_id, amount, event_time)
        VALUES (%(event_id)s, %(event_type)s, %(user_id)s, %(product_id)s, %(amount)s, %(event_time)s)
        ON CONFLICT (event_id) DO NOTHING;
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, event)
        connection.commit()
        logging.info("Inserted event: %s", event.get("event_id"))
    except Exception:
        connection.rollback()
        logging.exception("Failed to insert event %s", event.get("event_id"))
        raise


def run():
    connection = get_db_connection()

    while True:
        try:
            event = generate_event()
            insert_event(connection, event)
            time.sleep(1)
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            logging.warning("Database connection dropped. Re-establishing...")
            connection.close()
            connection = get_db_connection()
        except Exception as error:
            logging.error("Execution error: %s", error)
            time.sleep(2)


if __name__ == "__main__":
    run()
