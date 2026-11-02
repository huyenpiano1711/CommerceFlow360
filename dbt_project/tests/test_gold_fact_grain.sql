with violations as (

    select
        'fact_orders' as fact_name,
        cast(order_id as varchar) as grain_key,
        count(*) as row_count
    from {{ ref('fact_orders') }}
    group by order_id
    having count(*) > 1

    union all

    select
        'fact_order_items',
        order_id || '|' || cast(order_item_id as varchar),
        count(*)
    from {{ ref('fact_order_items') }}
    group by order_id, order_item_id
    having count(*) > 1

    union all

    select
        'fact_payments',
        order_id || '|' || cast(payment_sequential as varchar),
        count(*)
    from {{ ref('fact_payments') }}
    group by order_id, payment_sequential
    having count(*) > 1

    union all

    select
        'fact_reviews',
        review_id || '|' || order_id,
        count(*)
    from {{ ref('fact_reviews') }}
    group by review_id, order_id
    having count(*) > 1

)

select *
from violations