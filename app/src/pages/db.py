"""
Env vars:
  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_POOL_SIZE
"""
from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Iterator, Optional

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

_pool: Optional[MySQLConnectionPool] = None

def _pool_kwargs() -> dict:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", "root"),
        "database": os.getenv("DB_NAME", "spotlight"),
        "pool_name": "spot_pool",
        "pool_size": int(os.getenv("DB_POOL_SIZE", "6")),
        "charset": "utf8mb4",
        "use_pure": True,
    }

def _ensure_pool():
    global _pool
    if _pool is None:
        _pool = MySQLConnectionPool(**_pool_kwargs())

def get_conn():
    _ensure_pool()
    return _pool.get_connection()

@contextmanager
def db_cursor(dictionary: bool = False) -> Iterator[mysql.connector.cursor_cext.CMySQLCursor]:
    cnx = get_conn()
    cur = cnx.cursor(dictionary=dictionary)
    try:
        yield cur
        cnx.commit()
    finally:
        try: cur.close()
        finally: cnx.close()

def ping() -> bool:
    try:
        cnx = get_conn()
        cnx.ping(reconnect=True, attempts=1, delay=0)
        cnx.close()
        return True
    except Exception:
        return False

