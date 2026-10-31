{#
  Generic test: tổ hợp cột phải duy nhất (dùng kiểm tra grain nhiều cột,
  ví dụ order_id + order_item_id). Viết sẵn để không phụ thuộc package dbt_utils.
  Cách dùng trong schema.yml (cấp model):
    data_tests:
      - unique_combination:
          arguments:
            columns: ['order_id', 'order_item_id']
#}
{% test unique_combination(model, columns) %}
select {{ columns | join(', ') }}, count(*) as so_dong
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
