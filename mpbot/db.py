import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
  telegram_id INTEGER PRIMARY KEY,
  username TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  balance_cents INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS topups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id INTEGER NOT NULL,
  bill_code TEXT NOT NULL UNIQUE,
  amount_cents INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  ref_no TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  paid_at TEXT,
  raw_payload TEXT,
  FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_topups_user ON topups(telegram_id);

CREATE TABLE IF NOT EXISTS vpn_accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id INTEGER NOT NULL,
  protocol TEXT NOT NULL,
  username TEXT NOT NULL,
  password TEXT,
  expires_at TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  meta TEXT,
  FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_accounts_user ON vpn_accounts(telegram_id);
"""


@dataclass
class User:
  telegram_id: int
  username: str
  balance_cents: int


class DB:
  def __init__(self, path: str):
    self.path = path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    self._init()

  def _conn(self) -> sqlite3.Connection:
    conn = sqlite3.connect(self.path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

  def _init(self) -> None:
    with self._conn() as c:
      c.executescript(SCHEMA)

  def upsert_user(self, telegram_id: int, username: str = "") -> None:
    with self._conn() as c:
      c.execute(
        "INSERT INTO users (telegram_id, username) VALUES (?, ?) "
        "ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username",
        (telegram_id, username or ""),
      )

  def get_user(self, telegram_id: int) -> Optional[User]:
    with self._conn() as c:
      row = c.execute(
        "SELECT telegram_id, username, balance_cents FROM users WHERE telegram_id=?",
        (telegram_id,),
      ).fetchone()
      if not row:
        return None
      return User(int(row["telegram_id"]), str(row["username"]), int(row["balance_cents"]))

  def add_balance(self, telegram_id: int, amount_cents: int) -> None:
    with self._conn() as c:
      c.execute(
        "UPDATE users SET balance_cents = balance_cents + ? WHERE telegram_id=?",
        (amount_cents, telegram_id),
      )

  def set_balance(self, telegram_id: int, amount_cents: int) -> None:
    with self._conn() as c:
      c.execute(
        "UPDATE users SET balance_cents = ? WHERE telegram_id=?",
        (amount_cents, telegram_id),
      )

  def create_topup(self, telegram_id: int, bill_code: str, amount_cents: int) -> None:
    with self._conn() as c:
      c.execute(
        "INSERT INTO topups (telegram_id, bill_code, amount_cents) VALUES (?,?,?)",
        (telegram_id, bill_code, amount_cents),
      )

  def mark_topup_paid(self, bill_code: str, ref_no: str, raw_payload: str) -> Optional[Tuple[int,int]]:
    """Mark PAID. Return (telegram_id, amount_cents) if status updated from PENDING."""
    with self._conn() as c:
      row = c.execute(
        "SELECT telegram_id, amount_cents, status FROM topups WHERE bill_code=?",
        (bill_code,),
      ).fetchone()
      if not row:
        return None
      if row["status"] == "PAID":
        return None
      c.execute(
        "UPDATE topups SET status='PAID', ref_no=?, paid_at=datetime('now'), raw_payload=? WHERE bill_code=?",
        (ref_no, raw_payload, bill_code),
      )
      return int(row["telegram_id"]), int(row["amount_cents"])

  def list_accounts(self, telegram_id: int) -> List[Dict[str, Any]]:
    with self._conn() as c:
      rows = c.execute(
        "SELECT protocol, username, password, expires_at, created_at FROM vpn_accounts WHERE telegram_id=? ORDER BY id DESC",
        (telegram_id,),
      ).fetchall()
      return [dict(r) for r in rows]

  def add_account(self, telegram_id: int, protocol: str, username: str, password: str = "", expires_at: str = "", meta: str = "") -> None:
    with self._conn() as c:
      c.execute(
        "INSERT INTO vpn_accounts (telegram_id, protocol, username, password, expires_at, meta) VALUES (?,?,?,?,?,?)",
        (telegram_id, protocol, username, password or None, expires_at or None, meta or None),
      )
