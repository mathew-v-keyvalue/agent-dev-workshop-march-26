"""Read-only product tools. All queries use parameterized SQL via src.db.execute_query."""

from langchain_core.tools import tool

from src.db import execute_query


@tool
def search_products(
    query: str,
    limit: int = 20,
) -> list:
    """Search products by name, description, or tags. Returns only active products.

    Args:
        query: Search term to match in name, description, or tags.
        limit: Maximum number of products to return (default 20).
    """
    if not (query or "").strip():
        return []
    pattern = f"%{(query or '').strip()}%"
    rows = execute_query(
        """SELECT p.product_id, p.name, p.description, p.base_price, p.selling_price,
                  p.discount_percent, p.stock_quantity, p.average_rating, p.total_ratings, p.tags,
                  b.name AS brand_name, c.name AS category_name
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.brand_id
           LEFT JOIN categories c ON p.category_id = c.category_id
           WHERE p.is_active = 1
             AND (p.name LIKE %s OR p.description LIKE %s OR p.tags LIKE %s)
           ORDER BY p.average_rating DESC, p.selling_price ASC
           LIMIT %s""",
        (pattern, pattern, pattern, limit),
    )
    return rows


@tool
def get_product_by_id(product_id: int) -> dict:
    """Get a single product by ID with brand and category names. Returns error if not found or inactive.

    Args:
        product_id: The product ID.
    """
    rows = execute_query(
        """SELECT p.*, b.name AS brand_name, c.name AS category_name
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.brand_id
           LEFT JOIN categories c ON p.category_id = c.category_id
           WHERE p.product_id = %s""",
        (product_id,),
    )
    if not rows:
        return {"error": f"No product found with product_id {product_id}."}
    return rows[0]


@tool
def get_products_by_category(category_id: int, limit: int = 50) -> list:
    """List active products in a category. Sorted by rating then price.

    Args:
        category_id: The category ID.
        limit: Maximum number of products (default 50).
    """
    rows = execute_query(
        """SELECT p.product_id, p.name, p.selling_price, p.discount_percent, p.stock_quantity,
                  p.average_rating, b.name AS brand_name
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.brand_id
           WHERE p.category_id = %s AND p.is_active = 1
           ORDER BY p.average_rating DESC, p.selling_price ASC
           LIMIT %s""",
        (category_id, limit),
    )
    return rows


@tool
def get_products_by_brand(brand_id: int, limit: int = 50) -> list:
    """List active products for a brand. Sorted by rating then price.

    Args:
        brand_id: The brand ID.
        limit: Maximum number of products (default 50).
    """
    rows = execute_query(
        """SELECT p.product_id, p.name, p.selling_price, p.discount_percent, p.stock_quantity,
                  p.average_rating, c.name AS category_name
           FROM products p
           LEFT JOIN categories c ON p.category_id = c.category_id
           WHERE p.brand_id = %s AND p.is_active = 1
           ORDER BY p.average_rating DESC, p.selling_price ASC
           LIMIT %s""",
        (brand_id, limit),
    )
    return rows


@tool
def get_product_reviews(product_id: int, limit: int = 20) -> list:
    """Get reviews for a product, most recent first.

    Args:
        product_id: The product ID.
        limit: Maximum number of reviews (default 20).
    """
    rows = execute_query(
        """SELECT r.review_id, r.rating, r.title, r.body, r.is_verified_purchase, r.helpful_count, r.created_at,
                  u.first_name, u.last_name
           FROM product_reviews r
           LEFT JOIN users u ON r.user_id = u.user_id
           WHERE r.product_id = %s
           ORDER BY r.created_at DESC
           LIMIT %s""",
        (product_id, limit),
    )
    return rows


@tool
def get_all_categories() -> list:
    """List all active categories."""
    rows = execute_query(
        "SELECT category_id, name, description, parent_category_id FROM categories WHERE is_active = 1 ORDER BY name"
    )
    return rows


@tool
def get_all_brands() -> list:
    """List all active brands."""
    rows = execute_query(
        "SELECT brand_id, name, logo_url FROM brands WHERE is_active = 1 ORDER BY name"
    )
    return rows


@tool
def get_bulk_products_by_ids(product_ids: list[int]) -> list:
    """Get multiple products by ID list. Returns only active products in same order as input.

    Args:
        product_ids: List of product IDs.
    """
    if not product_ids:
        return []
    placeholders = ",".join(["%s"] * len(product_ids))
    rows = execute_query(
        f"""SELECT p.*, b.name AS brand_name, c.name AS category_name
            FROM products p
            LEFT JOIN brands b ON p.brand_id = b.brand_id
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.product_id IN ({placeholders}) AND p.is_active = 1""",
        tuple(product_ids),
    )
    by_id = {r["product_id"]: r for r in rows}
    return [by_id[pid] for pid in product_ids if pid in by_id]


@tool
def check_product_availability(product_id: int) -> dict:
    """Check if a product is active and in stock. Returns availability and stock_quantity.

    Args:
        product_id: The product ID.
    """
    rows = execute_query(
        "SELECT product_id, name, is_active, stock_quantity FROM products WHERE product_id = %s",
        (product_id,),
    )
    if not rows:
        return {"error": f"No product found with product_id {product_id}."}
    r = rows[0]
    available = r.get("is_active") and (r.get("stock_quantity") or 0) > 0
    return {
        "product_id": r["product_id"],
        "name": r.get("name"),
        "available": bool(available),
        "stock_quantity": r.get("stock_quantity") or 0,
        "is_active": bool(r.get("is_active")),
    }
