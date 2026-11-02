{{ config(materialized='table') }}

with reviews as (

    select
        review_id,
        order_id,
        review_score,
        review_creation_date,
        review_answer_timestamp,
        has_comment,
        is_latest_review
    from {{ ref('silver_order_reviews') }}

),

review_context as (

    select
        reviews.*,
        orders.customer_id,
        orders.order_purchase_timestamp,
        customers.customer_unique_id,
        customers.customer_zip_code_prefix
    from reviews
    left join {{ ref('silver_orders') }} as orders
        on reviews.order_id = orders.order_id
    left join {{ ref('silver_customers') }} as customers
        on orders.customer_id = customers.customer_id

)

select
    review_context.review_id,
    review_context.order_id,
    dim_customer.customer_key,
    dim_customer_geo.geography_key as customer_geography_key,
    purchase_date.date_key as purchase_date_key,
    review_creation_date.date_key as review_creation_date_key,
    review_answer_date.date_key as review_answer_date_key,
    review_context.review_score,
    review_context.has_comment,
    review_context.is_latest_review

from review_context
left join {{ ref('dim_customer') }} as dim_customer
    on review_context.customer_unique_id = dim_customer.customer_unique_id
left join {{ ref('dim_geography') }} as dim_customer_geo
    on review_context.customer_zip_code_prefix = dim_customer_geo.zip_code_prefix
left join {{ ref('dim_date') }} as purchase_date
    on cast(review_context.order_purchase_timestamp as date) = purchase_date.full_date
left join {{ ref('dim_date') }} as review_creation_date
    on cast(review_context.review_creation_date as date) = review_creation_date.full_date
left join {{ ref('dim_date') }} as review_answer_date
    on cast(review_context.review_answer_timestamp as date) = review_answer_date.full_date
