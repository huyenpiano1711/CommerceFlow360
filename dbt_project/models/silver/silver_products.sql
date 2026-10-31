-- silver_products | Grain: 1 dòng / product_id | Task C02 (Duy Lê)
-- Quy tắc: sửa tên cột viết sai ở nguồn (..._lenght -> ..._length), ép kiểu số,
-- danh mục NULL -> 'sem_categoria' (có cờ), kích thước/khối lượng <= 0 là không hợp lệ -> NULL,
-- gắn tên danh mục tiếng Anh từ silver_product_category_name_translation (đã bổ sung bản dịch thiếu).
with src as (
    select
        {{ clean_id('product_id') }}                     as product_id,
        {{ clean_code('product_category_name') }}        as product_category_name_raw,
        {{ clean_int('product_name_lenght') }}           as product_name_length,
        {{ clean_int('product_description_lenght') }}    as product_description_length,
        {{ clean_int('product_photos_qty') }}            as product_photos_qty,
        try_cast(product_weight_g  as double)            as product_weight_g_raw,
        try_cast(product_length_cm as double)            as product_length_cm_raw,
        try_cast(product_height_cm as double)            as product_height_cm_raw,
        try_cast(product_width_cm  as double)            as product_width_cm_raw,
        row_number() over (
            partition by {{ clean_id('product_id') }}
            order by {{ bronze_latest_first(source('bronze', 'products')) }}
        ) as _rn
    from {{ source('bronze', 'products') }}
    where {{ clean_id('product_id') }} is not null
),

translation as (
    select * from {{ ref('silver_product_category_name_translation') }}
)

select
    s.product_id,
    coalesce(s.product_category_name_raw, 'sem_categoria')        as product_category_name,
    t.product_category_name_english,
    s.product_name_length,
    s.product_description_length,
    s.product_photos_qty,
    case when s.product_weight_g_raw  > 0 then s.product_weight_g_raw  end as product_weight_g,
    case when s.product_length_cm_raw > 0 then s.product_length_cm_raw end as product_length_cm,
    case when s.product_height_cm_raw > 0 then s.product_height_cm_raw end as product_height_cm,
    case when s.product_width_cm_raw  > 0 then s.product_width_cm_raw  end as product_width_cm,
    (s.product_category_name_raw is null)                         as flag_category_missing,
    (coalesce(s.product_weight_g_raw, 0) <= 0
        or coalesce(s.product_length_cm_raw, 0) <= 0
        or coalesce(s.product_height_cm_raw, 0) <= 0
        or coalesce(s.product_width_cm_raw, 0) <= 0)              as flag_dimension_invalid
from src s
left join translation t
    on t.product_category_name = coalesce(s.product_category_name_raw, 'sem_categoria')
where s._rn = 1
