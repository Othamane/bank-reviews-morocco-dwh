{{ config(
    materialized='table',
    post_hook=[
        "{{ set_primary_key(this, 'bank_id') }}"
    ]
) }}

with bank_data as (
    select distinct
        bank_name
    from public.cleaned_reviews
)

select
    row_number() over () as bank_id,  -- This generates a unique ID for each row
    bank_name
from bank_data
