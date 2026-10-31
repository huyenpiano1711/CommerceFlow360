-- test_silver_bronze_row_reconciliation | Task C03 (Duy Lê)
-- Đối soát Bronze -> Silver: số dòng Silver phải bằng số khóa grain phân biệt ở Bronze
-- (Silver chỉ được loại bản trùng theo grain, không được làm mất bản ghi hợp lệ).
-- Riêng geolocation: số dòng Silver = số tiền tố ZIP phân biệt ở Bronze.
with checks as (
    select 'orders' as bang,
           (select count(distinct lower(trim(cast(order_id as varchar)))) from {{ source('bronze', 'orders') }}) as so_khoa_bronze,
           (select count(*) from {{ ref('silver_orders') }}) as so_dong_silver
    union all
    select 'order_items',
           (select count(distinct (lower(trim(cast(order_id as varchar))), try_cast(order_item_id as integer))) from {{ source('bronze', 'order_items') }}),
           (select count(*) from {{ ref('silver_order_items') }})
    union all
    select 'order_payments',
           (select count(distinct (lower(trim(cast(order_id as varchar))), try_cast(payment_sequential as integer))) from {{ source('bronze', 'order_payments') }}),
           (select count(*) from {{ ref('silver_order_payments') }})
    union all
    select 'order_reviews',
           (select count(distinct (lower(trim(cast(review_id as varchar))), lower(trim(cast(order_id as varchar))))) from {{ source('bronze', 'order_reviews') }}),
           (select count(*) from {{ ref('silver_order_reviews') }})
    union all
    select 'customers',
           (select count(distinct lower(trim(cast(customer_id as varchar)))) from {{ source('bronze', 'customers') }}),
           (select count(*) from {{ ref('silver_customers') }})
    union all
    select 'sellers',
           (select count(distinct lower(trim(cast(seller_id as varchar)))) from {{ source('bronze', 'sellers') }}),
           (select count(*) from {{ ref('silver_sellers') }})
    union all
    select 'products',
           (select count(distinct lower(trim(cast(product_id as varchar)))) from {{ source('bronze', 'products') }}),
           (select count(*) from {{ ref('silver_products') }})
    union all
    select 'geolocation',
           (select count(distinct try_cast(geolocation_zip_code_prefix as integer)) from {{ source('bronze', 'geolocation') }}),
           (select count(*) from {{ ref('silver_geolocation') }})
)
select * from checks where so_khoa_bronze <> so_dong_silver
