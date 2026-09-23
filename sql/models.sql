-- DuckDB 1.4.3. Raw is the flattened extraction, one source row per event.
CREATE OR REPLACE TABLE events AS
SELECT row_number() OVER () AS event_id, *,
  make_timestamp(event_timestamp) AS ts,
  CASE WHEN user_pseudo_id IS NULL OR user_pseudo_id IN ('','<Other>','(not set)') THEN NULL ELSE user_pseudo_id END AS user_key,
  CASE WHEN ga_session_id > 0 AND session_param_count = 1
    AND user_pseudo_id IS NOT NULL AND user_pseudo_id NOT IN ('','<Other>','(not set)')
    THEN user_pseudo_id || ':' || CAST(ga_session_id AS VARCHAR) END AS session_key,
  CASE WHEN device IS NULL OR device IN ('','<Other>','(not set)') THEN 'Unknown' ELSE device END AS device_group,
  CASE WHEN acquisition_medium = 'organic' THEN 'Organic search'
    WHEN acquisition_medium IN ('cpc','ppc','paidsearch') THEN 'Paid search'
    WHEN acquisition_medium = 'email' THEN 'Email'
    WHEN acquisition_medium = 'referral' THEN 'Referral'
    WHEN acquisition_source = '(direct)' AND acquisition_medium IN ('(none)','(not set)') THEN 'Direct'
    WHEN acquisition_medium IS NULL OR acquisition_medium IN ('','<Other>','(not set)') THEN 'Unknown'
    ELSE 'Other' END AS channel,
  CASE WHEN transaction_id IS NULL OR transaction_id IN ('','<Other>','(not set)') THEN NULL ELSE transaction_id END AS transaction_key
FROM raw;

-- Global transaction ID is the store's order key. First receipt wins; ties
-- use source row position. Conflicting revenue/identity is separately audited.
CREATE OR REPLACE TABLE purchases AS
SELECT * FROM events WHERE event_name = 'purchase' AND transaction_key IS NOT NULL
QUALIFY row_number() OVER (PARTITION BY transaction_key ORDER BY ts, event_id) = 1;

CREATE OR REPLACE TABLE sessions AS
SELECT session_key, user_key, min(ts) AS started_at, max(ts) AS ended_at,
  count(*) AS event_count, arg_min(device_group, struct_pack(t := ts, i := event_id)) AS device,
  arg_min(channel, struct_pack(t := ts, i := event_id)) AS channel
FROM (SELECT * FROM events ORDER BY ts, event_id) WHERE session_key IS NOT NULL
GROUP BY session_key, user_key;

CREATE OR REPLACE TABLE users AS
SELECT user_key, min(ts) AS first_observed_at, max(ts) AS last_observed_at,
 count(*) AS event_count, count(DISTINCT session_key) AS sessions
FROM events WHERE user_key IS NOT NULL GROUP BY user_key;

CREATE OR REPLACE TABLE cohorts AS
SELECT *, CAST(date_trunc('week', first_observed_at) AS DATE) AS cohort_week FROM users;
