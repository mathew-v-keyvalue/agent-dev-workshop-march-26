"""Write tools for cart and wishlist. Use execute_query, execute_insert, execute_update from src.db."""

from langchain_core.tools import tool

from src.db import execute_insert, execute_query, execute_update


@tool
def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> dict:
    """Add a product to the user's cart. If already in cart, increases quantity.

    Args:
        user_id: The user's ID.
        product_id: The product ID to add.
        quantity: Quantity to add (default 1).
    """
    existing = execute_query(
        "SELECT cart_item_id, quantity FROM cart_items WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
    )
    if existing:
        execute_update(
            "UPDATE cart_items SET quantity = quantity + %s WHERE cart_item_id = %s",
            (quantity, existing[0]["cart_item_id"]),
        )
        return {"ok": True, "message": "Cart quantity updated."}
    execute_insert(
        "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)",
        (user_id, product_id, quantity),
    )
    return {"ok": True, "message": "Item added to cart."}


@tool
def update_cart_quantity(user_id: int, cart_item_id: int, quantity: int) -> dict:
    """Update quantity of a cart line item. Use 0 to remove the item.

    Args:
        user_id: The user's ID.
        cart_item_id: The cart item ID to update.
        quantity: New quantity (0 to remove).
    """
    if quantity < 0:
        return {"error": "Quantity must be non-negative."}
    rows = execute_query(
        "SELECT cart_item_id FROM cart_items WHERE cart_item_id = %s AND user_id = %s",
        (cart_item_id, user_id),
    )
    if not rows:
        return {"error": f"No cart item {cart_item_id} found for this user."}
    if quantity == 0:
        execute_update(
            "DELETE FROM cart_items WHERE cart_item_id = %s AND user_id = %s",
            (cart_item_id, user_id),
        )
        return {"ok": True, "message": "Item removed from cart."}
    execute_update(
        "UPDATE cart_items SET quantity = %s WHERE cart_item_id = %s AND user_id = %s",
        (quantity, cart_item_id, user_id),
    )
    return {"ok": True, "message": f"Cart quantity updated to {quantity}."}


@tool
def remove_from_cart(user_id: int, cart_item_id: int) -> dict:
    """Remove an item from the user's cart.

    Args:
        user_id: The user's ID.
        cart_item_id: The cart item ID to remove.
    """
    affected = execute_update(
        "DELETE FROM cart_items WHERE cart_item_id = %s AND user_id = %s",
        (cart_item_id, user_id),
    )
    if affected == 0:
        return {"error": f"No cart item {cart_item_id} found for this user."}
    return {"ok": True, "message": "Item removed from cart."}


@tool
def add_to_wishlist(user_id: int, product_id: int) -> dict:
    """Add a product to the user's wishlist. Idempotent if already present.

    Args:
        user_id: The user's ID.
        product_id: The product ID to add.
    """
    existing = execute_query(
        "SELECT wishlist_id FROM wishlists WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
    )
    if existing:
        return {"ok": True, "message": "Product already in wishlist."}
    execute_insert(
        "INSERT INTO wishlists (user_id, product_id) VALUES (%s, %s)",
        (user_id, product_id),
    )
    return {"ok": True, "message": "Added to wishlist."}


@tool
def remove_from_wishlist(user_id: int, product_id: int) -> dict:
    """Remove a product from the user's wishlist.

    Args:
        user_id: The user's ID.
        product_id: The product ID to remove.
    """
    affected = execute_update(
        "DELETE FROM wishlists WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
    )
    if affected == 0:
        return {"error": "Product was not in wishlist."}
    return {"ok": True, "message": "Removed from wishlist."}
