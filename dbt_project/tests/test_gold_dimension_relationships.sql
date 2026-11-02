with violations as (

    select 'fact_orders.customer_key' as relationship, cast(f.order_id as varchar) as record_key
    from {{ ref('fact_orders') }} f
    left join {{ ref('dim_customer') }} d on f.customer_key = d.customer_key
    where f.customer_key is null or d.customer_key is null

    union all

    select 'fact_orders.customer_geography_key', cast(f.order_id as varchar)
    from {{ ref('fact_orders') }} f
    left join {{ ref('dim_geography') }} d on f.customer_geography_key = d.geography_key
    where f.customer_geography_key is not null and d.geography_key is null

    union all

    select 'fact_orders.purchase_date_key', cast(f.order_id as varchar)
    from {{ ref('fact_orders') }} f
    left join {{ ref('dim_date') }} d on f.purchase_date_key = d.date_key
    where f.purchase_date_key is null or d.date_key is null

    union all

    select 'fact_orders.approved_date_key', cast(f.order_id as varchar)
    from {{ ref('fact_orders') }} f
    left join {{ ref('dim_date') }} d on f.approved_date_key = d.date_key
    where f.approved_date_key is not null and d.date_key is null

    union all

    select 'fact_orders.carrier_date_key', cast(f.order_id as varchar)
    from {{ ref('fact_orders') }} f
    left join {{ ref('dim_date') }} d on f.carrier_date_key = d.date_key
    where f.carrier_date_key is not null and d.date_key is null

    union all

    select 'fact_orders.delivered_date_key', cast(f.order_id as varchar)
    from {{ ref('fact_orders') }} f
    left join {{ ref('dim_date') }} d on f.delivered_date_key = d.date_key
    where f.delivered_date_key is not null and d.date_key is null

    union all

    select 'fact_orders.estimated_delivery_date_key', cast(f.order_id as varchar)
    from {{ ref('fact_orders') }} f
    left join {{ ref('dim_date') }} d on f.estimated_delivery_date_key = d.date_key
    where f.estimated_delivery_date_key is not null and d.date_key is null

    union all

    select 'fact_order_items.customer_key',
           f.order_id || '|' || cast(f.order_item_id as varchar)
    from {{ ref('fact_order_items') }} f
    left join {{ ref('dim_customer') }} d on f.customer_key = d.customer_key
    where f.customer_key is null or d.customer_key is null

    union all

    select 'fact_order_items.product_key',
           f.order_id || '|' || cast(f.order_item_id as varchar)
    from {{ ref('fact_order_items') }} f
    left join {{ ref('dim_product') }} d on f.product_key = d.product_key
    where f.product_key is null or d.product_key is null

    union all

    select 'fact_order_items.seller_key',
           f.order_id || '|' || cast(f.order_item_id as varchar)
    from {{ ref('fact_order_items') }} f
    left join {{ ref('dim_seller') }} d on f.seller_key = d.seller_key
    where f.seller_key is null or d.seller_key is null

    union all

    select 'fact_order_items.customer_geography_key',
           f.order_id || '|' || cast(f.order_item_id as varchar)
    from {{ ref('fact_order_items') }} f
    left join {{ ref('dim_geography') }} d on f.customer_geography_key = d.geography_key
    where f.customer_geography_key is not null and d.geography_key is null

    union all

    select 'fact_order_items.seller_geography_key',
           f.order_id || '|' || cast(f.order_item_id as varchar)
    from {{ ref('fact_order_items') }} f
    left join {{ ref('dim_geography') }} d on f.seller_geography_key = d.geography_key
    where f.seller_geography_key is not null and d.geography_key is null

    union all

    select 'fact_order_items.purchase_date_key',
           f.order_id || '|' || cast(f.order_item_id as varchar)
    from {{ ref('fact_order_items') }} f
    left join {{ ref('dim_date') }} d on f.purchase_date_key = d.date_key
    where f.purchase_date_key is null or d.date_key is null

    union all

    select 'fact_order_items.shipping_limit_date_key',
           f.order_id || '|' || cast(f.order_item_id as varchar)
    from {{ ref('fact_order_items') }} f
    left join {{ ref('dim_date') }} d on f.shipping_limit_date_key = d.date_key
    where f.shipping_limit_date_key is not null and d.date_key is null

    union all

    select 'fact_payments.customer_key',
           f.order_id || '|' || cast(f.payment_sequential as varchar)
    from {{ ref('fact_payments') }} f
    left join {{ ref('dim_customer') }} d on f.customer_key = d.customer_key
    where f.customer_key is null or d.customer_key is null

    union all

    select 'fact_payments.customer_geography_key',
           f.order_id || '|' || cast(f.payment_sequential as varchar)
    from {{ ref('fact_payments') }} f
    left join {{ ref('dim_geography') }} d on f.customer_geography_key = d.geography_key
    where f.customer_geography_key is not null and d.geography_key is null

    union all

    select 'fact_payments.purchase_date_key',
           f.order_id || '|' || cast(f.payment_sequential as varchar)
    from {{ ref('fact_payments') }} f
    left join {{ ref('dim_date') }} d on f.purchase_date_key = d.date_key
    where f.purchase_date_key is null or d.date_key is null

    union all

    select 'fact_reviews.customer_key', f.review_id || '|' || f.order_id
    from {{ ref('fact_reviews') }} f
    left join {{ ref('dim_customer') }} d on f.customer_key = d.customer_key
    where f.customer_key is null or d.customer_key is null

    union all

    select 'fact_reviews.customer_geography_key', f.review_id || '|' || f.order_id
    from {{ ref('fact_reviews') }} f
    left join {{ ref('dim_geography') }} d on f.customer_geography_key = d.geography_key
    where f.customer_geography_key is not null and d.geography_key is null

    union all

    select 'fact_reviews.purchase_date_key', f.review_id || '|' || f.order_id
    from {{ ref('fact_reviews') }} f
    left join {{ ref('dim_date') }} d on f.purchase_date_key = d.date_key
    where f.purchase_date_key is not null and d.date_key is null

    union all

    select 'fact_reviews.review_creation_date_key', f.review_id || '|' || f.order_id
    from {{ ref('fact_reviews') }} f
    left join {{ ref('dim_date') }} d on f.review_creation_date_key = d.date_key
    where f.review_creation_date_key is null or d.date_key is null

    union all

    select 'fact_reviews.review_answer_date_key', f.review_id || '|' || f.order_id
    from {{ ref('fact_reviews') }} f
    left join {{ ref('dim_date') }} d on f.review_answer_date_key = d.date_key
    where f.review_answer_date_key is not null and d.date_key is null

)

select *
from violations