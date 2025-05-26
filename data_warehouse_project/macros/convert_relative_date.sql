{% macro convert_relative_date(review_date, scraping_date) %}
    {% set current_year = "EXTRACT(YEAR FROM " ~ scraping_date ~ ")" %}
    
    case 
        when lower({{ review_date }}) like '%il y a un an%' then {{ current_year }} - 1
        when lower({{ review_date }}) like '%il y a % ans%' then {{ current_year }} - cast(regexp_substr(lower({{ review_date }}), '\\d+') as int)
        when lower({{ review_date }}) like '%il y a un mois%' then {{ current_year }}
        when lower({{ review_date }}) like '%il y a % mois%' then {{ current_year }} - cast(regexp_substr(lower({{ review_date }}), '\\d+') as int)/12
        when lower({{ review_date }}) like '%il y a % semaines%' then {{ current_year }} - cast(regexp_substr(lower({{ review_date }}), '\\d+') as int)/52
        else {{ current_year }}
    end
{% endmacro %}
