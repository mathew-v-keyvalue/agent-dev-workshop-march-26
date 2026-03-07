"""LangChain DB tools: orders, logistics, payments, products, cart, coupons, wallet, returns, support, notifications, users."""

from src.tools.cart import (
    add_to_cart,
    add_to_wishlist,
    get_cart_items,
    get_wishlist,
    remove_from_cart,
    remove_from_wishlist,
    update_cart_quantity,
)
from src.tools.coupons import get_available_coupons, validate_coupon
from src.tools.logistics import (
    get_bulk_shipments_by_orders,
    get_delivery_estimate,
    get_full_tracking_by_order,
    get_logistics_partners,
    get_shipment_by_order,
    get_tracking_events,
    update_shipment_status,
)
from src.tools.notifications import get_user_notifications, mark_notification_read
from src.tools.orders import (
    cancel_order,
    get_bulk_orders_by_ids,
    get_order_by_id,
    get_order_by_order_number,
    get_order_details_full,
    get_order_items,
    get_orders_by_user,
    update_order_status,
)
from src.tools.payments import (
    get_bulk_payments_by_orders,
    get_payment_by_order,
    get_payments_by_user,
)
from src.tools.products import (
    check_product_availability,
    get_all_brands,
    get_all_categories,
    get_bulk_products_by_ids,
    get_product_by_id,
    get_product_reviews,
    get_products_by_brand,
    get_products_by_category,
    search_products,
)
from src.tools.returns import (
    create_return_request,
    get_refund_by_order,
    get_refund_by_user,
    get_refund_status,
    get_return_requests_by_order,
    get_return_requests_by_user,
    update_return_status,
)
from src.tools.support import (
    create_support_ticket,
    get_ticket_details,
    get_tickets_by_user,
    update_ticket_status,
)
from src.tools.users import get_user_addresses, get_user_by_email, get_user_profile
from src.tools.wallet import get_wallet_balance, get_wallet_transactions

ORDER_TOOLS = [
    get_order_by_order_number,
    get_order_by_id,
    get_orders_by_user,
    get_order_items,
    get_order_details_full,
    get_bulk_orders_by_ids,
    cancel_order,
    update_order_status,
]

LOGISTICS_TOOLS = [
    get_shipment_by_order,
    get_tracking_events,
    get_full_tracking_by_order,
    get_delivery_estimate,
    get_logistics_partners,
    get_bulk_shipments_by_orders,
    update_shipment_status,
]

PAYMENT_TOOLS = [
    get_payment_by_order,
    get_payments_by_user,
    get_bulk_payments_by_orders,
]

PRODUCT_TOOLS = [
    search_products,
    get_product_by_id,
    get_products_by_category,
    get_products_by_brand,
    get_product_reviews,
    get_all_categories,
    get_all_brands,
    get_bulk_products_by_ids,
    check_product_availability,
]

CART_TOOLS = [
    get_cart_items,
    get_wishlist,
    add_to_cart,
    update_cart_quantity,
    remove_from_cart,
    add_to_wishlist,
    remove_from_wishlist,
]

COUPON_TOOLS = [
    validate_coupon,
    get_available_coupons,
]

WALLET_TOOLS = [
    get_wallet_balance,
    get_wallet_transactions,
]

RETURNS_TOOLS = [
    get_return_requests_by_order,
    get_return_requests_by_user,
    get_refund_by_order,
    get_refund_by_user,
    get_refund_status,
    create_return_request,
    update_return_status,
]

SUPPORT_TOOLS = [
    get_tickets_by_user,
    get_ticket_details,
    create_support_ticket,
    update_ticket_status,
]

NOTIFICATION_TOOLS = [
    get_user_notifications,
    mark_notification_read,
]

USER_TOOLS = [
    get_user_profile,
    get_user_by_email,
    get_user_addresses,
]

__all__ = [
    "ORDER_TOOLS",
    "LOGISTICS_TOOLS",
    "PAYMENT_TOOLS",
    "PRODUCT_TOOLS",
    "CART_TOOLS",
    "COUPON_TOOLS",
    "WALLET_TOOLS",
    "RETURNS_TOOLS",
    "SUPPORT_TOOLS",
    "NOTIFICATION_TOOLS",
    "USER_TOOLS",
    "get_order_by_order_number",
    "get_order_by_id",
    "get_orders_by_user",
    "get_order_items",
    "get_order_details_full",
    "get_bulk_orders_by_ids",
    "cancel_order",
    "update_order_status",
    "get_shipment_by_order",
    "get_tracking_events",
    "get_full_tracking_by_order",
    "get_delivery_estimate",
    "get_logistics_partners",
    "get_bulk_shipments_by_orders",
    "update_shipment_status",
    "get_payment_by_order",
    "get_payments_by_user",
    "get_bulk_payments_by_orders",
    "search_products",
    "get_product_by_id",
    "get_products_by_category",
    "get_products_by_brand",
    "get_product_reviews",
    "get_all_categories",
    "get_all_brands",
    "get_bulk_products_by_ids",
    "check_product_availability",
    "get_cart_items",
    "get_wishlist",
    "add_to_cart",
    "update_cart_quantity",
    "remove_from_cart",
    "add_to_wishlist",
    "remove_from_wishlist",
    "validate_coupon",
    "get_available_coupons",
    "get_wallet_balance",
    "get_wallet_transactions",
    "get_return_requests_by_order",
    "get_return_requests_by_user",
    "get_refund_by_order",
    "get_refund_by_user",
    "get_refund_status",
    "create_return_request",
    "update_return_status",
    "get_tickets_by_user",
    "get_ticket_details",
    "create_support_ticket",
    "update_ticket_status",
    "get_user_notifications",
    "mark_notification_read",
    "get_user_profile",
    "get_user_by_email",
    "get_user_addresses",
]
