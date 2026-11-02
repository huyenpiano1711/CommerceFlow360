{{ config(materialized='table') }}

with payments as (

    select
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    from {{ ref('silver_order_payments') }}

),

payment_context as (

    select
        payments.*,
        orders.customer_id,
        orders.order_purchase_timestamp,
        customers.customer_unique_id,
        customers.customer_zip_code_prefix
    from payments
    left join {{ ref('silver_orders') }} as orders
        on payments.order_id = orders.order_id
    left join {{ ref('silver_customers') }} as customers
        on orders.customer_id = customers.customer_id

)

select
    payment_context.order_id,
    payment_context.payment_sequential,
    dim_customer.customer_key,
    dim_customer_geo.geography_key as customer_geography_key,
    purchase_date.date_key as purchase_date_key,
    payment_context.payment_type,
    payment_context.payment_installments,
    cast(payment_context.payment_value as decimal(12, 2)) as payment_value

from payment_context
left join {{ ref('dim_customer') }} as dim_customer
    on payment_context.customer_unique_id = dim_customer.customer_unique_id
left join {{ ref('dim_geography') }} as dim_customer_geo
    on payment_context.customer_zip_code_prefix = dim_customer_geo.zip_code_prefix
left join {{ ref('dim_date') }} as purchase_date
    on cast(payment_context.order_purchase_timestamp as date) = purchase_date.full_date
