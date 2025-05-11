{{ config(
    materialized='table',
    post_hook=[
        "{{ set_primary_key(this, 'location_id') }}"
    ]
) }}

with location_data as (
    select distinct
        location
    from public.cleaned_reviews
)

select
    row_number() over () as location_id,  -- Unique ID for each location
    location
from location_data
