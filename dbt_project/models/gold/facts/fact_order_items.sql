{{ config(materialized='table') }}

with order_items as (

    select
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_limit_date,
        price,
        freight_value
    from {{ ref('silver_order_items') }}

),

item_context as (

    select
        order_items.*,
        orders.customer_id,
        orders.order_purchase_timestamp,
        customers.customer_unique_id,
        customers.customer_zip_code_prefix as customer_zip_code_prefix,
        sellers.seller_zip_code_prefix as seller_zip_code_prefix
    from order_items
    left join {{ ref('silver_orders') }} as orders
        on order_items.order_id = orders.order_id
    left join {{ ref('silver_customers') }} as customers
        on orders.customer_id = customers.customer_id
    left join {{ ref('silver_sellers') }} as sellers
        on order_items.seller_id = sellers.seller_id

)

select
    item_context.order_id,
    item_context.order_item_id,
    dim_customer.customer_key,
    dim_product.product_key,
    dim_seller.seller_key,
    customer_geo.geography_key as customer_geography_key,
    seller_geo.geography_key as seller_geography_key,
    purchase_date.date_key as purchase_date_key,
    shipping_limit_date.date_key as shipping_limit_date_key,

    cast(item_context.price as decimal(12, 2)) as item_price,
    cast(item_context.freight_value as decimal(12, 2)) as freight_value,
    1::integer as item_count

from item_context
left join {{ ref('dim_customer') }} as dim_customer
    on item_context.customer_unique_id = dim_customer.customer_unique_id
left join {{ ref('dim_product') }} as dim_product
    on item_context.product_id = dim_product.product_id
left join {{ ref('dim_seller') }} as dim_seller
    on item_context.seller_id = dim_seller.seller_id
left join {{ ref('dim_geography') }} as customer_geo
    on item_context.customer_zip_code_prefix = customer_geo.zip_code_prefix
left join {{ ref('dim_geography') }} as seller_geo
    on item_context.seller_zip_code_prefix = seller_geo.zip_code_prefix
left join {{ ref('dim_date') }} as purchase_date
    on cast(item_context.order_purchase_timestamp as date) = purchase_date.full_date
left join {{ ref('dim_date') }} as shipping_limit_date
    on cast(item_context.shipping_limit_date as date) = shipping_limit_date.full_date
