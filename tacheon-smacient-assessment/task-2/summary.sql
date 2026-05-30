-- ============================================================
-- CoinGecko Market Data — Summary Queries
-- All queries filter to MAX(fetched_at) to read the latest
-- pipeline snapshot only. This is the standard pattern for
-- WRITE_APPEND time-series tables.
-- ============================================================


-- Query 1: Top 10 Coins by Liquidity
-- Uses the derived volume_to_market_cap_ratio field.
-- High ratio = coin is actively traded relative to its market size.
-- Stablecoins typically top this list — they trade constantly relative to cap.

SELECT
  coin_name,
  symbol,
  market_cap_rank,
  ROUND(current_price_usd, 4)                    AS price_usd,
  ROUND(volume_to_market_cap_ratio * 100, 2)     AS volume_to_mcap_pct,
  ROUND(price_change_pct_24h, 2)                 AS price_change_24h_pct
FROM `starry-sylph-409904.crypto_market_data.coin_markets`
WHERE
  fetched_at = (
    SELECT MAX(fetched_at)
    FROM `starry-sylph-409904.crypto_market_data.coin_markets`
  )
  AND volume_to_market_cap_ratio IS NOT NULL
ORDER BY volume_to_market_cap_ratio DESC
LIMIT 10;


-- Query 2: Top 10 Coins by Intraday Volatility
-- Uses the derived price_range_pct_24h field.
-- High value = large price swing within a single day.
-- Useful for risk profiling and identifying momentum assets.

SELECT
  coin_name,
  symbol,
  market_cap_rank,
  ROUND(current_price_usd, 4)       AS price_usd,
  ROUND(price_range_pct_24h, 2)     AS intraday_swing_pct,
  ROUND(price_change_pct_24h, 2)    AS net_change_24h_pct,
  ROUND(high_24h_usd, 4)            AS high_24h,
  ROUND(low_24h_usd, 4)             AS low_24h
FROM `starry-sylph-409904.crypto_market_data.coin_markets`
WHERE
  fetched_at = (
    SELECT MAX(fetched_at)
    FROM `starry-sylph-409904.crypto_market_data.coin_markets`
  )
  AND price_range_pct_24h IS NOT NULL
ORDER BY price_range_pct_24h DESC
LIMIT 10;


-- Query 3: Market Structure by Rank Tier
-- Aggregates total market cap, volume, avg price change, and avg liquidity
-- across four rank brackets. Shows how capital is distributed across
-- Mega Cap, Large Cap, Mid Cap, and Small Cap segments.

SELECT
  CASE
    WHEN market_cap_rank BETWEEN 1  AND 10  THEN '01-10 (Mega Cap)'
    WHEN market_cap_rank BETWEEN 11 AND 25  THEN '11-25 (Large Cap)'
    WHEN market_cap_rank BETWEEN 26 AND 50  THEN '26-50 (Mid Cap)'
    WHEN market_cap_rank BETWEEN 51 AND 100 THEN '51-100 (Small Cap)'
    ELSE 'Unranked'
  END                                              AS rank_tier,
  COUNT(*)                                         AS coin_count,
  ROUND(SUM(market_cap_usd) / 1e9, 2)             AS total_market_cap_bn_usd,
  ROUND(SUM(total_volume_usd) / 1e9, 2)           AS total_volume_bn_usd,
  ROUND(AVG(price_change_pct_24h), 2)             AS avg_price_change_24h_pct,
  ROUND(AVG(volume_to_market_cap_ratio) * 100, 2) AS avg_volume_to_mcap_pct
FROM `starry-sylph-409904.crypto_market_data.coin_markets`
WHERE
  fetched_at = (
    SELECT MAX(fetched_at)
    FROM `starry-sylph-409904.crypto_market_data.coin_markets`
  )
  AND market_cap_rank IS NOT NULL
GROUP BY rank_tier
ORDER BY rank_tier;