-- test_silver_geolocation_customer_coverage | Task C03 (Duy Lê) | severity = warn
-- Liệt kê tiền tố ZIP của khách hàng/người bán không có trong silver_geolocation.
-- Đã xử lý ở Gold: dim_geography lấy city/state từ chính địa chỉ khách hàng/người bán
-- (location_source = 'customer_seller_address'), nên test này chỉ để ghi nhận số lượng trong báo cáo.
{{ config(severity='warn') }}
select 'customer' as doi_tuong, customer_zip_code_prefix as zip_code_prefix
from {{ ref('silver_customers') }}
where customer_zip_code_prefix not in (select geolocation_zip_code_prefix from {{ ref('silver_geolocation') }})
union all
select 'seller', seller_zip_code_prefix
from {{ ref('silver_sellers') }}
where seller_zip_code_prefix not in (select geolocation_zip_code_prefix from {{ ref('silver_geolocation') }})
