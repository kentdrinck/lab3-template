import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "flights"),
        user=os.getenv("DB_USER", "program"),
        password=os.getenv("DB_PASSWORD", "test"),
        port=os.getenv("DB_PORT", "5432"),
    )

def fetch_flights(page: int, size: int):
    offset = (page - 1) * size
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Raw SQL запрос с JOIN для получения названий аэропортов
    query = """
        SELECT 
            f.flight_number as "flightNumber",
            f.datetime as "date",
            f.price,
            concat(a1.city, ' ', a1.name) as "fromAirport",
            concat(a2.city, ' ', a2.name) as "toAirport"
        FROM flight f
        JOIN airport a1 ON f.from_airport_id = a1.id
        JOIN airport a2 ON f.to_airport_id = a2.id
        LIMIT %s OFFSET %s
    """
    cur.execute(query, (size, offset))
    items = cur.fetchall()
    
    cur.execute("SELECT COUNT(*) FROM flight")
    total_elements = cur.fetchone()['count']
    
    cur.close()
    conn.close()
    return items, total_elements

def fetch_flight_by_number(flight_number: str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT 
            f.flight_number as "flightNumber",
            f.datetime as "date",
            f.price,
            concat(a1.city, ' ', a1.name) as "fromAirport",
            concat(a2.city, ' ', a2.name) as "toAirport"
        FROM flight f
        JOIN airport a1 ON f.from_airport_id = a1.id
        JOIN airport a2 ON f.to_airport_id = a2.id
        WHERE f.flight_number = %s
    """
    cur.execute(query, (flight_number,))
    flight = cur.fetchone()
    cur.close()
    conn.close()
    return flight