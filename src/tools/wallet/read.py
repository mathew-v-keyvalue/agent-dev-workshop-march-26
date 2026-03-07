"""Read-only wallet tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_wallet_balance(user_id: int) -> dict:
    """Get wallet balance for a user. Creates no wallet if missing; returns 0 balance.

    Args:
        user_id: The user's ID.
    """
    rows = execute_query(
        "SELECT wallet_id, user_id, balance, last_updated_at FROM wallet WHERE user_id = %s",
        (user_id,),
    )
    if not rows:
        return {"user_id": user_id, "balance": 0, "wallet_id": None}
    r = rows[0]
    return {"user_id": r["user_id"], "balance": r.get("balance") or 0, "wallet_id": r["wallet_id"], "last_updated_at": r.get("last_updated_at")}


@tool
def get_wallet_transactions(user_id: int, limit: int = 20) -> list:
    """Get recent wallet transactions for a user (credits and debits).

    Args:
        user_id: The user's ID.
        limit: Maximum number of transactions (default 20).
    """
    rows = execute_query(
        """SELECT wt.txn_id, wt.wallet_id, wt.txn_type, wt.amount, wt.description,
                  wt.reference_type, wt.reference_id, wt.created_at
           FROM wallet_transactions wt
           JOIN wallet w ON wt.wallet_id = w.wallet_id
           WHERE w.user_id = %s
           ORDER BY wt.created_at DESC
           LIMIT %s""",
        (user_id, limit),
    )
    return rows
