-- test_silver_review_score_range | Task C03 (Duy Lê)
-- Quy tắc nghiệp vụ: điểm đánh giá phải nằm trong thang 1-5 và không thiếu.
select review_id, order_id, review_score
from {{ ref('silver_order_reviews') }}
where review_score is null or review_score not between 1 and 5
