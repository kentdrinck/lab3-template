import os, psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT"),
    )


def get_privilege_with_history(username: str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT id, balance, status FROM privilege WHERE username = %s", (username,)
    )
    privilege = cur.fetchone()

    if not privilege:
        cur.close()
        conn.close()
        return {"balance": 0, "status": "BRONZE", "history": []}

    cur.execute(
        """
        SELECT datetime as "date", ticket_uid as "ticketUid", 
               balance_diff as "balanceDiff", operation_type as "operationType"
        FROM privilege_history WHERE privilege_id = %s
    """,
        (privilege["id"],),
    )
    history = cur.fetchall()

    cur.close()
    conn.close()
    return {
        "balance": privilege["balance"],
        "status": privilege["status"],
        "history": history,
    }


def process_bonus_operation(
    username: str, ticket_uid: str, price: int, paid_from_balance: bool
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT id, balance, status FROM privilege WHERE username = %s", (username,)
    )
    priv = cur.fetchone()

    if priv is None:
        cur.execute(
            "INSERT INTO privilege (username, status, balance) VALUES (%s, 'BRONZE', 0) RETURNING id, balance, status",
            (username,),
        )
        priv = cur.fetchone()

    paid_by_bonuses = 0
    balance_diff = 0
    op_type = ""

    if paid_from_balance:
        paid_by_bonuses = min(priv["balance"], price)
        balance_diff = -paid_by_bonuses
        op_type = "DEBIT_THE_ACCOUNT"
    else:
        balance_diff = int(price * 0.1)
        paid_by_bonuses = 0
        op_type = "FILL_IN_BALANCE"

    cur.execute(
        "UPDATE privilege SET balance = balance + %s WHERE id = %s RETURNING balance, status",
        (balance_diff, priv["id"]),
    )
    updated_priv = cur.fetchone()

    cur.execute(
        """
        INSERT INTO privilege_history (privilege_id, ticket_uid, datetime, balance_diff, operation_type)
        VALUES (%s, %s, %s, %s, %s)
    """,
        (priv["id"], ticket_uid, datetime.now(), abs(balance_diff), op_type),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "paidByBonuses": paid_by_bonuses,
        "balanceDiff": balance_diff,
        "privilege": {
            "balance": updated_priv["balance"],
            "status": updated_priv["status"],
        },
    }


def process_rollback_operation(
    username: str, ticket_uid: str, price: int
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT operation_type FROM privilege_history WHERE ticket_uid = %s", (ticket_uid,))
    t = cur.fetchone()
    if not t:
        return
    paid_from_balance = t["operation_type"] == "DEBIT_THE_ACCOUNT"

    if paid_from_balance:
        cost = price
    else:
        cur.execute("SELECT balance FROM privilege WHERE username = %s", (username,))
        balance = cur.fetchone()
        if not balance:
            return
        cost = -min(balance["balance"], price // 10)

    cur.execute("UPDATE privilege SET balance = balance + %s WHERE username = %s", (cost, username))

    conn.commit()
    cur.close()
    conn.close()
