{{ config(materialized='table') }}

with orders as (

    select
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date
    from {{ ref('silver_orders') }}

),

order_context as (

    select
        orders.*,
        customers.customer_unique_id,
        customers.customer_zip_code_prefix
    from orders
    left join {{ ref('silver_customers') }} as customers
        on orders.customer_id = customers.customer_id

)

select
    order_context.order_id,
    order_context.customer_id as source_customer_id,
    dim_customer.customer_key,
    dim_customer_geo.geography_key as customer_geography_key,

    purchase_date.date_key as purchase_date_key,
    approved_date.date_key as approved_date_key,
    carrier_date.date_key as carrier_date_key,
    delivered_date.date_key as delivered_date_key,
    estimated_delivery_date.date_key as estimated_delivery_date_key,

    order_context.order_status,
    1::integer as order_count,

    -- [Sửa logic] Định nghĩa "đơn hợp lệ" dùng chung cho mọi Data Mart (doanh thu, chi tiêu,
    -- khách mua lại): loại đơn bị hủy hoặc không còn hàng. Đặt ở fact để không mart nào tự định nghĩa lại.
    (order_context.order_status not in ('canceled', 'unavailable')) as is_valid_order,

    -- [Sửa logic] Chỉ số giao hàng chỉ tính cho đơn có trạng thái 'delivered'.
    -- Nguồn có 6 đơn canceled vẫn mang ngày giao khách; trước đây các đơn này bị tính vào tỷ lệ giao trễ.
    case
        when order_context.order_status = 'delivered'
         and order_context.order_delivered_customer_date is not null
            then date_diff(
                'day',
                cast(order_context.order_purchase_timestamp as date),
                cast(order_context.order_delivered_customer_date as date)
            )
    end as delivery_days,

    case
        when order_context.order_status = 'delivered'
         and order_context.order_delivered_customer_date is not null
         and order_context.order_estimated_delivery_date is not null
            then greatest(
                date_diff(
                    'day',
                    cast(order_context.order_estimated_delivery_date as date),
                    cast(order_context.order_delivered_customer_date as date)
                ),
                0
            )
    end as days_late,

    case
        when order_context.order_status <> 'delivered'
          or order_context.order_delivered_customer_date is null
          or order_context.order_estimated_delivery_date is null
            then null
        else cast(order_context.order_delivered_customer_date as date)
             > cast(order_context.order_estimated_delivery_date as date)
    end as is_delivered_late

from order_context
left join {{ ref('dim_customer') }} as dim_customer
    on order_context.customer_unique_id = dim_customer.customer_unique_id
left join {{ ref('dim_geography') }} as dim_customer_geo
    on order_context.customer_zip_code_prefix = dim_customer_geo.zip_code_prefix
left join {{ ref('dim_date') }} as purchase_date
    on cast(order_context.order_purchase_timestamp as date) = purchase_date.full_date
left join {{ ref('dim_date') }} as approved_date
    on cast(order_context.order_approved_at as date) = approved_date.full_date
left join {{ ref('dim_date') }} as carrier_date
    on cast(order_context.order_delivered_carrier_date as date) = carrier_date.full_date
left join {{ ref('dim_date') }} as delivered_date
    on cast(order_context.order_delivered_customer_date as date) = delivered_date.full_date
left join {{ ref('dim_date') }} as estimated_delivery_date
    on cast(order_context.order_estimated_delivery_date as date) = estimated_delivery_date.full_date
