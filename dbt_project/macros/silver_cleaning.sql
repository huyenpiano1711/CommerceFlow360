{#
  Macro dùng chung cho tầng Silver - CommerceFlow 360 (Task C02, Duy Lê).
  Bronze lưu mọi cột dạng VARCHAR (all_varchar); macro vẫn cast về varchar trước khi xử lý
  nên dùng được cho cả cột đã có kiểu khác.
#}

{# Chuỗi: bỏ khoảng trắng thừa ở hai đầu, gộp nhiều khoảng trắng/xuống dòng thành 1, chuỗi rỗng -> NULL #}
{% macro clean_text(col) -%}
    nullif(trim(regexp_replace(cast({{ col }} as varchar), '\s+', ' ', 'g')), '')
{%- endmacro %}

{# Mã định danh (md5 32 ký tự): làm sạch như chuỗi và đưa về chữ thường #}
{% macro clean_id(col) -%}
    lower({{ clean_text(col) }})
{%- endmacro %}

{# Mã trạng thái / loại (order_status, payment_type...): chữ thường, snake_case #}
{% macro clean_code(col) -%}
    lower(replace({{ clean_text(col) }}, ' ', '_'))
{%- endmacro %}

{# Mã bang Brazil (UF): 2 ký tự in hoa #}
{% macro clean_state(col) -%}
    upper({{ clean_text(col) }})
{%- endmacro %}

{# Tiền tố mã ZIP: luôn là chuỗi 5 chữ số, khôi phục số 0 đầu nếu nguồn bị mất #}
{% macro clean_zip(col) -%}
    lpad(cast(try_cast({{ clean_text(col) }} as integer) as varchar), 5, '0')
{%- endmacro %}

{# Thời gian: chỉ lấy phần đúng mẫu YYYY-MM-DD[ HH:MM:SS] rồi ép kiểu, giá trị lỗi -> NULL
   (ví dụ nguồn có giá trị '2018-01-18 19:12:30q' trong review_answer_timestamp) #}
{% macro clean_timestamp(col) -%}
    try_cast(nullif(regexp_extract(cast({{ col }} as varchar), '\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?'), '') as timestamp)
{%- endmacro %}

{# Số tiền: DECIMAL(12,2) để cộng dồn chính xác khi đối soát doanh thu #}
{% macro clean_money(col) -%}
    try_cast({{ col }} as decimal(12, 2))
{%- endmacro %}

{# Số nguyên #}
{% macro clean_int(col) -%}
    try_cast(try_cast({{ col }} as double) as integer)
{%- endmacro %}

{# Tên thành phố: chữ thường, bỏ dấu, thống nhất dấu nháy, bỏ phần ghi chú bang/quốc gia
   phía sau ("sao paulo - sp", "maua/sao paulo", "andira-pr", "x (porto seguro)"),
   giá trị không phải tên (toàn số, email) -> NULL #}
{% macro clean_city(col, state_col=none) -%}
    {%- set base -%}
        trim(regexp_replace(
            regexp_replace(
                regexp_replace(
                    replace(replace(lower(strip_accents(cast({{ col }} as varchar))), '´', ''''), '`', ''''),
                '\s*\(.*\)\s*$', ''),
            '\s*(/|\\|,|\s-\s).*$', ''),
        '\s+', ' ', 'g'))
    {%- endset -%}
    {%- if state_col is not none -%}
        {%- set base -%}
            regexp_replace({{ base }}, '-' || lower(trim(cast({{ state_col }} as varchar))) || '$', '')
        {%- endset -%}
    {%- endif -%}
    case
        when {{ base }} is null or {{ base }} = '' then null
        when regexp_full_match({{ base }}, '[0-9 ]+') or {{ base }} like '%@%' then null
        when {{ base }} = 'sp' then 'sao paulo'
        when {{ base }} = 'sbc' then 'sao bernardo do campo'
        else {{ base }}
    end
{%- endmacro %}

{#
  Biểu thức ORDER BY dùng khi khử trùng theo grain: ưu tiên bản ghi nạp gần nhất theo cột
  thời điểm nạp (var bronze_load_ts_columns); bảng không có cột này thì thứ tự không quan trọng.
#}
{% macro bronze_latest_first(relation) -%}
    {%- if execute -%}
        {%- set cols = adapter.get_columns_in_relation(relation) | map(attribute='name') | map('lower') | list -%}
        {%- set found = [] -%}
        {%- for c in var('bronze_load_ts_columns') -%}
            {%- if c | lower in cols and found | length == 0 -%}{%- do found.append(c) -%}{%- endif -%}
        {%- endfor -%}
        {%- if found | length > 0 -%}{{ adapter.quote(found[0]) }} desc nulls last{%- else -%}null{%- endif -%}
    {%- else -%}null{%- endif -%}
{%- endmacro %}
