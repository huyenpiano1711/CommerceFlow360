with reconciliations as (

    select
        'order_count' as metric,
        cast(
            (
                select count(distinct lower(trim(cast(order_id as varchar))))
                from {{ source('bronze', 'orders') }}
            ) as decimal(18, 2)
        ) as source_value,
        cast(
            (select count(*) from {{ ref('silver_orders') }})
            as decimal(18, 2)
        ) as silver_value,
        cast(
            (select sum(order_count) from {{ ref('fact_orders') }})
            as decimal(18, 2)
        ) as gold_value

    union all

    select
        'item_revenue',
        cast(
            (
                select sum(try_cast(price as decimal(18, 2)))
                from {{ source('bronze', 'order_items') }}
            ) as decimal(18, 2)
        ),
        cast(
            (select sum(price) from {{ ref('silver_order_items') }})
            as decimal(18, 2)
        ),
        cast(
            (select sum(item_price) from {{ ref('fact_order_items') }})
            as decimal(18, 2)
        )

    union all

    select
        'freight_value',
        cast(
            (
                select sum(try_cast(freight_value as decimal(18, 2)))
                from {{ source('bronze', 'order_items') }}
            ) as decimal(18, 2)
        ),
        cast(
            (select sum(freight_value) from {{ ref('silver_order_items') }})
            as decimal(18, 2)
        ),
        cast(
            (select sum(freight_value) from {{ ref('fact_order_items') }})
            as decimal(18, 2)
        )

    union all

    select
        'payment_value',
        cast(
            (
                select sum(try_cast(payment_value as decimal(18, 2)))
                from {{ source('bronze', 'order_payments') }}
            ) as decimal(18, 2)
        ),
        cast(
            (select sum(payment_value) from {{ ref('silver_order_payments') }})
            as decimal(18, 2)
        ),
        cast(
            (select sum(payment_value) from {{ ref('fact_payments') }})
            as decimal(18, 2)
        )

)

select *
from reconciliations
where source_value is null
   or silver_value is null
   or gold_value is null
   or abs(source_value - silver_value) >= 0.01
   or abs(silver_value - gold_value) >= 0.01