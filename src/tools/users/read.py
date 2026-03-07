"""Read-only user and address tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_user_profile(user_id: int) -> dict:
    """Get user profile by ID. Excludes sensitive fields as needed.

    Args:
        user_id: The user's ID.
    """
    rows = execute_query(
        """SELECT user_id, first_name, last_name, email, phone, date_of_birth, gender,
                  account_status, is_premium_member, premium_expiry, created_at, last_login_at
           FROM users WHERE user_id = %s""",
        (user_id,),
    )
    if not rows:
        return {"error": f"No user found with user_id {user_id}."}
    return rows[0]


@tool
def get_user_by_email(email: str) -> dict:
    """Look up a user by email address.

    Args:
        email: The user's email.
    """
    rows = execute_query(
        "SELECT user_id, first_name, last_name, email, phone, account_status FROM users WHERE email = %s",
        (email.strip(),),
    )
    if not rows:
        return {"error": f"No user found with email '{email}'."}
    return rows[0]


@tool
def get_user_addresses(user_id: int) -> list:
    """Get all saved addresses for a user.

    Args:
        user_id: The user's ID.
    """
    rows = execute_query(
        """SELECT address_id, label, full_name, phone, address_line1, address_line2,
                  city, state, pincode, country, is_default, created_at
           FROM addresses WHERE user_id = %s ORDER BY is_default DESC, address_id""",
        (user_id,),
    )
    return rows
