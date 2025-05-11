{{ config(
    materialized='table',
    post_hook=[
        "alter table {{ this }} add foreign key (bank_id) references {{ ref('dim_bank') }} (bank_id)",
        "alter table {{ this }} add foreign key (branch_id) references {{ ref('dim_branch') }} (branch_id)",
        "alter table {{ this }} add foreign key (location_id) references {{ ref('dim_location') }} (location_id)",
        "alter table {{ this }} add foreign key (sentiment_id) references {{ ref('dim_sentiment') }} (sentiment_id)"
    ]
) }}
with banks as (
    select bank_id, bank_name from {{ ref('dim_bank') }}
),
branches as (
    select branch_id, branch_name from {{ ref('dim_branch') }}
),
locations as (
    select location_id, location from {{ ref('dim_location') }}
),
sentiments as (
    select sentiment_id, sentiment_label from {{ ref('dim_sentiment') }}
),
reviews as (
    select * from public.cleaned_reviews
)

select
    row_number() over () as fact_review_id,  -- Unique ID for each fact record
    b.bank_id,
    br.branch_id,
    l.location_id,
    s.sentiment_id,
    r.review_text,
    r.relative_topic,
    r.topic_meaning,
    r.rating,
    r.review_date,
    r.language
from reviews r
join banks b on r.bank_name = b.bank_name
join branches br on r.branch_name = br.branch_name
join locations l on r.location = l.location
join sentiments s on r.sentiment = s.sentiment_label
