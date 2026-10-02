-- Synthetic commerce only. One row/order and one item/order; all costs variable.
-- Revenue is net of discounts, excludes tax; costs include fulfillment.
CREATE TABLE finance_months AS
SELECT strftime(day, '%Y-%m') AS month, count(*) AS orders,
       count(DISTINCT customer) AS buyers,
       sum(revenue_cents)/100.0 AS revenue,
       sum(variable_cost_cents)/100.0 AS cost,
       sum(revenue_cents-variable_cost_cents)/100.0 AS margin
FROM orders GROUP BY 1 ORDER BY 1;

CREATE TABLE finance_products AS
SELECT strftime(day, '%Y-%m') AS month, product, count(*) AS orders,
       sum(revenue_cents)/100.0 AS revenue,
       sum(variable_cost_cents)/100.0 AS cost
FROM orders GROUP BY 1,2 ORDER BY 1,2;
