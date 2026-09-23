-- Standard SQL. All events, bounded tables; retain history for cohorts.
-- Run a dry run first. No LIMIT: it does not bound bytes scanned.
SELECT event_date, event_timestamp, event_name, user_pseudo_id,
  (SELECT MAX(COALESCE(value.int_value, SAFE_CAST(value.string_value AS INT64)))
   FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS ga_session_id,
  (SELECT COUNT(*) FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_param_count,
  device.category AS device,
  traffic_source.source AS acquisition_source,
  traffic_source.medium AS acquisition_medium,
  ecommerce.transaction_id AS transaction_id,
  ecommerce.purchase_revenue_in_usd AS revenue_usd,
  ecommerce.purchase_revenue AS revenue_local,
  (SELECT MAX(value.string_value) FROM UNNEST(event_params) WHERE key = 'currency') AS currency,
  (SELECT MAX(COALESCE(value.double_value, value.float_value, CAST(value.int_value AS FLOAT64)))
   FROM UNNEST(event_params) WHERE key = 'value') AS event_value
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
