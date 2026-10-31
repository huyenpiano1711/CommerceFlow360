-- silver_order_reviews | Grain: 1 dòng / (review_id, order_id) | Task C02 (Duy Lê)
-- Nguồn có review_id lặp lại cho nhiều đơn và một đơn có thể có nhiều đánh giá, nên grain là cặp
-- (review_id, order_id). Làm sạch bình luận (xuống dòng, khoảng trắng, chuỗi rỗng -> NULL),
-- sửa mốc thời gian lỗi định dạng, và gắn cờ is_latest_review để Gold chọn 1 đánh giá / đơn.
with src as (
    select
        {{ clean_id('review_id') }}                      as review_id,
        {{ clean_id('order_id') }}                       as order_id,
        {{ clean_int('review_score') }}                  as review_score,
        {{ clean_text('review_comment_title') }}         as review_comment_title,
        {{ clean_text('review_comment_message') }}       as review_comment_message,
        {{ clean_timestamp('review_creation_date') }}    as review_creation_date,
        {{ clean_timestamp('review_answer_timestamp') }} as review_answer_timestamp,
        row_number() over (
            partition by {{ clean_id('review_id') }}, {{ clean_id('order_id') }}
            order by {{ bronze_latest_first(source('bronze', 'order_reviews')) }}
        ) as _rn
    from {{ source('bronze', 'order_reviews') }}
    where {{ clean_id('review_id') }} is not null and {{ clean_id('order_id') }} is not null
),

dedup as (
    select * exclude (_rn) from src where _rn = 1
)

select
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date,
    review_answer_timestamp,
    (review_comment_title is not null or review_comment_message is not null) as has_comment,
    row_number() over (
        partition by order_id
        order by review_answer_timestamp desc nulls last, review_creation_date desc nulls last, review_id
    ) = 1                                                                      as is_latest_review
from dedup
