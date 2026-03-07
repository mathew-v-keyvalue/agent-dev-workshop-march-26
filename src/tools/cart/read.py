"""Read-only cart and wishlist tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def get_cart_items(user_id: int) -> list:
    """Get all cart items for a user with product name, price, and image.

    Args:
        user_id: The user's ID.
    """
    rows = execute_query(
        """SELECT ci.cart_item_id, ci.product_id, ci.quantity, ci.added_at,
                  p.name, p.selling_price, p.base_price, p.discount_percent, p.stock_quantity,
                  b.name AS brand_name,
                  (SELECT pi.image_url FROM product_images pi
                   WHERE pi.product_id = p.product_id
                   ORDER BY pi.is_primary DESC, pi.sort_order LIMIT 1) AS image_url
           FROM cart_items ci
           JOIN products p ON ci.product_id = p.product_id
           LEFT JOIN brands b ON p.brand_id = b.brand_id
           WHERE ci.user_id = %s
           ORDER BY ci.added_at DESC""",
        (user_id,),
    )
    return rows


@tool
def get_wishlist(user_id: int) -> list:
    """Get wishlist items for a user with product details.

    Args:
        user_id: The user's ID.
    """
    rows = execute_query(
        """SELECT w.wishlist_id, w.product_id, w.added_at,
                  p.name, p.selling_price, p.discount_percent, p.average_rating,
                  b.name AS brand_name,
                  (SELECT pi.image_url FROM product_images pi
                   WHERE pi.product_id = p.product_id
                   ORDER BY pi.is_primary DESC, pi.sort_order LIMIT 1) AS image_url
           FROM wishlists w
           JOIN products p ON w.product_id = p.product_id
           LEFT JOIN brands b ON p.brand_id = b.brand_id
           WHERE w.user_id = %s
           ORDER BY w.added_at DESC""",
        (user_id,),
    )
    return rows
