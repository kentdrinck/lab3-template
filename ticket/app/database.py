import os
import psycopg2
import uuid
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def get_user_tickets(username: str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT ticket_uid as "ticketUid", flight_number as "flightNumber", price, status 
        FROM ticket WHERE username = %s
    """, (username,))
    tickets = cur.fetchall()
    cur.close()
    conn.close()
    return tickets

def create_new_ticket(username: str, flight_number: str, price: int, ticket_uid: uuid.UUID | None):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if not ticket_uid:
        ticket_uid = uuid.uuid4()
    
    cur.execute("""
        INSERT INTO ticket (ticket_uid, username, flight_number, price, status)
        VALUES (%s, %s, %s, %s, 'PAID')
        RETURNING ticket_uid as "ticketUid", flight_number as "flightNumber", price, status
    """, (str(ticket_uid), username, flight_number, price))
    
    ticket = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return ticket

def update_ticket_status(ticket_uid: str, username: str, status: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE ticket SET status = %s 
        WHERE ticket_uid = %s AND username = %s
    """, (status, ticket_uid, username))
    
    count = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return count > 0

def get_ticket_by_uid_and_user(ticket_uid: str, username: str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # В запросе обязательно проверяем и UID билета, и имя пользователя
    query = """
        SELECT 
            ticket_uid as "ticketUid", 
            flight_number as "flightNumber", 
            price, 
            status 
        FROM ticket 
        WHERE ticket_uid = %s AND username = %s
    """
    cur.execute(query, (ticket_uid, username))
    ticket = cur.fetchone()
    
    cur.close()
    conn.close()
    return ticket