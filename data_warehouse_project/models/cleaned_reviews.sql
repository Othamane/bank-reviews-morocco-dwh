{{ config(
    materialized='table'
) }}
with remove_duplicates as (
    -- Removing duplicates from the raw data
    select distinct
        bank_name,
        branch_name,
        location,
        review_text,
        rating,
        review_date,
        scraping_date
    from {{ source('raw_data', 'staging') }}
),

normalize_text as (
    -- Normalizing text (e.g., converting to lowercase)
    select
        bank_name,
        branch_name,
        location,
        lower(review_text) as review_text,  -- Normalize to lowercase
        rating,
        review_date,
        scraping_date
    from remove_duplicates
),

handle_missing_values as (
    -- Removing rows with missing or empty review_text after cleaning emojis
    select
        bank_name,
        branch_name,
        location,
        -- Removing emojis and non-alphanumeric characters, leaving spaces and alphanumeric only
        nullif(
            trim(
                regexp_replace(
                    review_text, 
                    '[^\w\s]',  -- This removes everything except word characters (letters, numbers, and spaces)
                    '', 
                    'g'
                )
            ), 
            ''
        ) as review_text,
        rating,
        review_date,
        scraping_date
    from normalize_text
    where review_text is not null 
      and trim(
          regexp_replace(
              review_text, 
              '[^\w\s]',  -- This removes everything except word characters (letters, numbers, and spaces)
              '', 
              'g'
          )
      ) <> ''
),


detect_language as (
    -- Detect the language of the review_text
    select
        bank_name,
        branch_name,
        location,
        review_text,
        rating,
        review_date,
        scraping_date,
        case
            when review_text similar to '%\bservice\b%' then 'fr' -- Simple keyword-based language detection for French
            when review_text similar to '%\bthe\b%' then 'en'     -- Simple keyword-based language detection for English
            else null
        end as language
    from handle_missing_values
),

filter_by_language as (
    -- Keep only French and English reviews
    select
        bank_name,
        branch_name,
        location,
        review_text,
        rating,
        review_date,
        scraping_date
    from detect_language
    where language in ('fr', 'en')
),

convert_rating as (
    -- Convert the rating column (example: converting textual ratings to numerical ones)
    select
        bank_name,
        branch_name,
        location,
        review_text,
        case
            when lower(rating) like '%1%' then 1
            when lower(rating) like '%2%' then 2
            when lower(rating) like '%3%' then 3
            when lower(rating) like '%4%' then 4
            when lower(rating) like '%5%' then 5
            else null
        end as rating,  -- Convert ratings to integers (1-5)
        review_date,
        scraping_date
    from handle_missing_values
),

adjust_review_date as (
    -- Adjust review_date based on the scraping_date and relative review_date
    select
        bank_name,
        branch_name,
        regexp_replace(location, '^Adresse:\s*', '') as location,
        review_text,
        rating,
        -- Use the macro to convert the relative review_date
          {{ convert_relative_date(
            "trim(lower(replace(review_date, '\u00A0', ' ')))",
            'review_date',
            'scraping_date'
        ) }} as review_date,
        scraping_date
    from convert_rating
)

-- Final model to create cleaned_reviews table
select
    bank_name,
    concat(branch_name, ' ', regexp_replace(location, '^.*?\b(Avenue|Av\.)', '\1', 'i')) as branch_name,
    location,
    review_text,
    rating,
    review_date
from adjust_review_date
