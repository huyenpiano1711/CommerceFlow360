{{ config(materialized='table') }}

-- mart_sales | Grain: 1 dòng / dòng hàng trong đơn (order_id, order_item_id) | Task E01 (Quỳnh Kha)
-- Doanh thu (item_price), phí vận chuyển, danh mục sản phẩm, bang khách hàng, người bán,
-- thời gian (tháng/quý/cờ ngày lễ) ở cùng một dòng để BI/Phân tích tự chọn chiều tổng hợp
-- (theo tháng, danh mục, bang, người bán...) mà không phải nối lại fact/dim.
-- is_valid_sale: loại trừ đơn hủy/không còn hàng khi tính doanh thu, theo quy ước Olist.
with items as (
    select
        order_id,
        order_item_id,
        customer_geography_key,
        seller_key,
        seller_geography_key,
        product_key,
        purchase_date_key,
        item_price,
        freight_value,
        item_price + freight_value as item_total_value,
        item_count
    from {{ ref('fact_order_items') }}
),

orders as (
    select order_id, order_status
    from {{ ref('fact_orders') }}
)

select
    items.order_id,
    items.order_item_id,
    order_date.full_date                           as order_purchase_date,
    order_date.year,
    order_date.quarter,
    order_date.month,
    order_date.month_name,
    order_date.is_brazil_holiday                    as is_holiday,
    order_date.holiday_name,
    product.product_category_name_english           as product_category,
    customer_geo.state                               as customer_state,
    seller.seller_id,
    seller_geo.state                                 as seller_state,
    orders.order_status,
    (orders.order_status not in ('canceled', 'unavailable'))
                                                      as is_valid_sale,
    items.item_price                                 as revenue,
    items.freight_value,
    items.item_total_value,
    items.item_count

from items
join orders
    on items.order_id = orders.order_id
left join {{ ref('dim_date') }} as order_date
    on items.purchase_date_key = order_date.date_key
left join {{ ref('dim_product') }} as product
    on items.product_key = product.product_key
left join {{ ref('dim_seller') }} as seller
    on items.seller_key = seller.seller_key
left join {{ ref('dim_geography') }} as customer_geo
    on items.customer_geography_key = customer_geo.geography_key
left join {{ ref('dim_geography') }} as seller_geo
    on items.seller_geography_key = seller_geo.geography_key
