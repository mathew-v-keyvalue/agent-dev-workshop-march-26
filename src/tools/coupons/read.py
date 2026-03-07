"""Read-only coupon tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def validate_coupon(
    coupon_code: str,
    user_id: int | None = None,
    order_amount: float | None = None,
) -> dict:
    """Validate a coupon: active, not expired, within usage limits (total and per-user).

    Optionally check min_order_amount and user-specific usage limit.
    Returns coupon details if valid, or error message.

    Args:
        coupon_code: The coupon code (e.g. 'SAVE10').
        user_id: Optional user ID to check per-user usage limit.
        order_amount: Optional order subtotal to check min_order_amount.
    """
    code = (coupon_code or "").strip()
    if not code:
        return {"error": "Coupon code is required."}
    rows = execute_query(
        """SELECT coupon_id, code, description, discount_type, discount_value,
                  min_order_amount, max_discount_amount, usage_limit_total, usage_limit_per_user,
                  times_used, valid_from, valid_until, is_active
           FROM coupons WHERE code = %s""",
        (code,),
    )
    if not rows:
        return {"error": f"Coupon '{code}' not found."}
    c = rows[0]
    if not c.get("is_active"):
        return {"error": "Coupon is not active."}
    # Use raw comparison; caller can pass datetime if needed - we use NOW() in SQL for consistency
    check = execute_query(
        """SELECT 1 FROM coupons WHERE coupon_id = %s AND is_active = 1
           AND valid_from <= NOW() AND valid_until >= NOW()""",
        (c["coupon_id"],),
    )
    if not check:
        return {"error": "Coupon is expired or not yet valid."}
    if c.get("usage_limit_total") is not None and (c.get("times_used") or 0) >= c["usage_limit_total"]:
        return {"error": "Coupon has reached its total usage limit."}
    if user_id is not None and c.get("usage_limit_per_user"):
        used_by_user = execute_query(
            "SELECT COUNT(*) AS cnt FROM coupon_usage WHERE coupon_id = %s AND user_id = %s",
            (c["coupon_id"], user_id),
        )
        if used_by_user and (used_by_user[0].get("cnt") or 0) >= c["usage_limit_per_user"]:
            return {"error": "You have already used this coupon the maximum times allowed."}
    if order_amount is not None and c.get("min_order_amount") is not None:
        if float(order_amount) < float(c["min_order_amount"]):
            return {"error": f"Minimum order amount for this coupon is {c['min_order_amount']}."}
    return {
        "valid": True,
        "coupon_id": c["coupon_id"],
        "code": c["code"],
        "description": c["description"],
        "discount_type": c["discount_type"],
        "discount_value": c["discount_value"],
        "min_order_amount": c.get("min_order_amount"),
        "max_discount_amount": c.get("max_discount_amount"),
    }


@tool
def get_available_coupons(user_id: int | None = None) -> list:
    """List coupons that are currently available (active, within validity, within total usage limit).

    Does not check per-user usage; use validate_coupon for that.

    Args:
        user_id: Optional; if provided, only returns coupons the user can still use (per-user limit).
    """
    rows = execute_query(
        """SELECT coupon_id, code, description, discount_type, discount_value,
                  min_order_amount, max_discount_amount, valid_from, valid_until,
                  usage_limit_total, usage_limit_per_user, times_used
           FROM coupons
           WHERE is_active = 1
             AND valid_from <= NOW() AND valid_until >= NOW()
             AND (usage_limit_total IS NULL OR times_used < usage_limit_total)
           ORDER BY valid_until ASC"""
    )
    if not user_id:
        return rows
    result = []
    for c in rows:
        if c.get("usage_limit_per_user"):
            used = execute_query(
                "SELECT COUNT(*) AS cnt FROM coupon_usage WHERE coupon_id = %s AND user_id = %s",
                (c["coupon_id"], user_id),
            )
            if used and (used[0].get("cnt") or 0) >= c["usage_limit_per_user"]:
                continue
        result.append(c)
    return result
