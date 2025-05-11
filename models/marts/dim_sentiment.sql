{{ config(
    materialized='table',
    post_hook=[
        "{{ set_primary_key(this, 'sentiment_id') }}"
    ]
) }}

with sentiment_data as (
    select distinct
        sentiment as sentiment_label
    from public.cleaned_reviews
)

select
    row_number() over () as sentiment_id,  -- Unique ID for each sentiment
    sentiment_label
from sentiment_data
