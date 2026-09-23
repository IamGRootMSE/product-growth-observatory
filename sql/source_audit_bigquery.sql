-- Match the extraction's suffix range exactly. Independent source reconciliation.
SELECT event_name, COUNT(*) AS event_count,
  COUNTIF(user_pseudo_id IS NULL OR user_pseudo_id IN ('', '<Other>', '(not set)')) AS missing_user_count,
  COUNT(DISTINCT IF(user_pseudo_id IN ('', '<Other>', '(not set)'), NULL, user_pseudo_id)) AS users,
  SUM(IF(event_name = 'purchase', ecommerce.purchase_revenue_in_usd, NULL)) AS raw_purchase_revenue_usd
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY event_name
