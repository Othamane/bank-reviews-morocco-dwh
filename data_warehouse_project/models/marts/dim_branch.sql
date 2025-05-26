{{ config(
    materialized='table',
    post_hook=[
        "{{ set_primary_key(this, 'branch_id') }}"
    ]
) }}

with branch_data as (
    select distinct
        branch_name
    from public.cleaned_reviews
)

select
    row_number() over () as branch_id,  -- Unique ID for each branch
    branch_name
from branch_data
