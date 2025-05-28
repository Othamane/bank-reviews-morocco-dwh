{% macro convert_relative_date(normalized_review_date, review_date, scraping_date) %}
    case
        -- Handle years (an/ans)
        when {{ normalized_review_date }} = 'il y a un an' then
            {{ scraping_date }} - interval '1 year'
        when {{ normalized_review_date }} = 'il y a 1 an' then
            {{ scraping_date }} - interval '1 year'
        when {{ normalized_review_date }} like 'il y a % an' and {{ normalized_review_date }} not like '%ans' then
            {{ scraping_date }} - (cast(split_part({{ normalized_review_date }}, ' ', 4) as int) * interval '1 year')
        when {{ normalized_review_date }} like 'il y a % ans' then
            {{ scraping_date }} - (cast(split_part({{ normalized_review_date }}, ' ', 4) as int) * interval '1 year')

        -- Handle months (mois)
        when {{ normalized_review_date }} = 'il y a un mois' then
            {{ scraping_date }} - interval '1 month'
        when {{ normalized_review_date }} = 'il y a 1 mois' then
            {{ scraping_date }} - interval '1 month'
        when {{ normalized_review_date }} like 'il y a % mois' then
            {{ scraping_date }} - (cast(split_part({{ normalized_review_date }}, ' ', 4) as int) * interval '1 month')

        -- Handle weeks (semaine/semaines)
        when {{ normalized_review_date }} = 'il y a une semaine' then
            {{ scraping_date }} - interval '1 week'
        when {{ normalized_review_date }} = 'il y a 1 semaine' then
            {{ scraping_date }} - interval '1 week'
        when {{ normalized_review_date }} like 'il y a % semaine' and {{ normalized_review_date }} not like '%semaines' then
            {{ scraping_date }} - (cast(split_part({{ normalized_review_date }}, ' ', 4) as int) * interval '1 week')
        when {{ normalized_review_date }} like 'il y a % semaines' then
            {{ scraping_date }} - (cast(split_part({{ normalized_review_date }}, ' ', 4) as int) * interval '1 week')

        -- Handle days (jour/jours)
        when {{ normalized_review_date }} = 'il y a un jour' then
            {{ scraping_date }} - interval '1 day'
        when {{ normalized_review_date }} = 'il y a 1 jour' then
            {{ scraping_date }} - interval '1 day'
        when {{ normalized_review_date }} like 'il y a % jour' and {{ normalized_review_date }} not like '%jours' then
            {{ scraping_date }} - (cast(split_part({{ normalized_review_date }}, ' ', 4) as int) * interval '1 day')
        when {{ normalized_review_date }} like 'il y a % jours' then
            {{ scraping_date }} - (cast(split_part({{ normalized_review_date }}, ' ', 4) as int) * interval '1 day')

        -- Handle "aujourd'hui"
        when {{ normalized_review_date }} = 'aujourd''hui' then 
            {{ scraping_date }}

        -- Handle "hier"
        when {{ normalized_review_date }} = 'hier' then 
            {{ scraping_date }} - interval '1 day'

        -- Handle already formatted dates
        when {{ review_date }} ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' then
            cast({{ review_date }} as date)

        -- Handle null or empty values
        when {{ review_date }} is null or trim({{ review_date }}) = '' then
            null

        else
            null
    end
{% endmacro %}
