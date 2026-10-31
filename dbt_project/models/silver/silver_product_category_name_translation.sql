-- silver_product_category_name_translation | Grain: 1 dòng / product_category_name | Task C02 (Duy Lê)
-- Bảng dịch gốc có 71 danh mục nhưng bảng products còn 2 danh mục chưa có bản dịch
-- và 610 sản phẩm không có danh mục. Bổ sung thủ công để mọi sản phẩm đều có tên tiếng Anh.
with olist as (
    select
        {{ clean_code('product_category_name') }}          as product_category_name,
        {{ clean_code('product_category_name_english') }}  as product_category_name_english,
        'olist'                                            as translation_source,
        row_number() over (
            partition by {{ clean_code('product_category_name') }}
            order by {{ bronze_latest_first(source('bronze', 'product_category_name_translation')) }}
        ) as _rn
    from {{ source('bronze', 'product_category_name_translation') }}
    where {{ clean_code('product_category_name') }} is not null
),

supplement (product_category_name, product_category_name_english, translation_source) as (
    values
        ('pc_gamer',                                       'pc_gamer',                            'manual_supplement'),
        ('portateis_cozinha_e_preparadores_de_alimentos',  'portable_kitchen_food_preparers',     'manual_supplement'),
        ('sem_categoria',                                  'uncategorized',                       'placeholder')
)

select product_category_name, product_category_name_english, translation_source
from olist
where _rn = 1

union all

select s.product_category_name, s.product_category_name_english, s.translation_source
from supplement s
where not exists (
    select 1 from olist o where o._rn = 1 and o.product_category_name = s.product_category_name
)
