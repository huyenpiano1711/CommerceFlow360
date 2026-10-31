-- test_silver_geolocation_customer_coverage | Task C03 (Duy Lê) | severity = warn
-- Liệt kê tiền tố ZIP của khách hàng/người bán không có trong silver_geolocation.
-- Gold (dim_geography) cần xử lý các ZIP này như "không xác định" thay vì làm rơi đơn hàng.
{{ config(severity='warn') }}
select 'customer' as doi_tuong, customer_zip_code_prefix as zip_code_prefix
from {{ ref('silver_customers') }}
where customer_zip_code_prefix not in (select geolocation_zip_code_prefix from {{ ref('silver_geolocation') }})
union all
select 'seller', seller_zip_code_prefix
from {{ ref('silver_sellers') }}
where seller_zip_code_prefix not in (select geolocation_zip_code_prefix from {{ ref('silver_geolocation') }})
