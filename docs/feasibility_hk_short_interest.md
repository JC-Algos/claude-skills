# Feasibility Study: HK Short Selling Interest Data Integration

**Date:** 2026-01-29  
**Prepared by:** Oracle 🐷

---

## Executive Summary

✅ **Feasible** - HK short selling data is publicly available from two main sources (HKEX and SFC) at no cost. Integration is achievable with moderate development effort.

---

## Data Sources

### 1. HKEX Daily Short Selling Turnover (Real-time/Daily)

**URL:** https://www.hkex.com.hk/Market-Data/Statistics/Securities-Market/Short-Selling-Turnover-Today

**Data Includes:**
- Daily short selling turnover amounts (HK$)
- Short selling turnover as % of total turnover
- Top 10 most-shorted stocks by volume
- Short selling ratios (Main Board & GEM)
- Individual stock short selling data

**Format:** HTML tables (requires scraping) or potential API access

**Frequency:** Real-time during market hours, daily historical

**Cost:** FREE

**Pros:**
- Real-time data available
- Covers all designated securities
- Shows actual trading activity (turnover-based)

**Cons:**
- HTML scraping required (no direct CSV/API for free tier)
- Turnover-based, not position-based

---

### 2. SFC Aggregated Short Positions (Weekly)

**URL:** https://www.sfc.hk/en/Regulatory-functions/Market/Short-position-reporting/Aggregated-reportable-short-positions-of-specified-shares

**Data Includes:**
- Aggregated reportable short positions (shares)
- Aggregated reportable short positions (HK$)
- Stock code and name
- Historical data back to 2015

**Format:** CSV download (direct link pattern)

**Frequency:** Weekly (typically Friday publication)

**Cost:** FREE

**Threshold:** Only positions ≥ HK$30M or ≥0.02% of issued shares

**CSV URL Pattern:**
```
https://www.sfc.hk/-/media/EN/pdf/spr/{YYYY}/{MM}/{DD}/Short_Position_Reporting_Aggregated_Data_{YYYYMMDD}.csv
```

**CSV Format:**
```csv
Date,Stock Code,Stock Name,Aggregated Reportable Short Positions (Shares),Aggregated Reportable Short Positions (HK$)
20/10/2023,1,CKH HOLDINGS,14169933,562546340
20/10/2023,2,CLP HOLDINGS,23238373,1311806156
```

**Pros:**
- Position-based (comparable to US short interest)
- CSV format (easy to parse)
- Historical data available
- Direct download links

**Cons:**
- Weekly only (not daily)
- Only covers positions above threshold
- ~1 week reporting lag

---

## Comparison: HK vs US Short Interest

| Aspect | HK (SFC Positions) | US (FINRA) |
|--------|-------------------|------------|
| Frequency | Weekly | Bi-monthly |
| Threshold | HK$30M / 0.02% | None |
| Data Type | Positions | Positions |
| Historical | Since 2015 | Varies |
| Cost | Free | Free |

| Aspect | HK (HKEX Turnover) | US Equivalent |
|--------|-------------------|---------------|
| Frequency | Daily/Real-time | N/A directly |
| Data Type | Turnover (flow) | N/A |
| Cost | Free | N/A |

---

## Proposed Implementation

### Phase 1: Data Collection Scripts

```python
# SFC Weekly Position Data Fetcher
def fetch_sfc_short_positions(date: str) -> pd.DataFrame:
    """Fetch SFC aggregated short positions CSV"""
    url = f"https://www.sfc.hk/-/media/EN/pdf/spr/{date[:4]}/{date[4:6]}/{date[6:8]}/Short_Position_Reporting_Aggregated_Data_{date}.csv"
    return pd.read_csv(url)

# HKEX Daily Turnover Scraper
def fetch_hkex_short_turnover() -> dict:
    """Scrape HKEX short selling turnover page"""
    # Requires Selenium/Playwright for dynamic content
    pass
```

### Phase 2: Database Schema

```sql
-- Daily short selling turnover (from HKEX)
CREATE TABLE hk_short_turnover (
    date DATE,
    stock_code VARCHAR(10),
    short_turnover BIGINT,
    total_turnover BIGINT,
    short_ratio DECIMAL(5,2),
    PRIMARY KEY (date, stock_code)
);

-- Weekly short positions (from SFC)
CREATE TABLE hk_short_positions (
    report_date DATE,
    stock_code VARCHAR(10),
    stock_name VARCHAR(100),
    short_shares BIGINT,
    short_value_hkd BIGINT,
    PRIMARY KEY (report_date, stock_code)
);
```

### Phase 3: Integration with Market Analyzer

Add to existing `/stock` command output:
- Short selling ratio (from HKEX daily)
- Short position % of float (from SFC weekly)
- Week-over-week change in short interest

---

## Technical Challenges

1. **HKEX Scraping:** Page uses JavaScript rendering - need Playwright/Selenium
2. **SFC URL Pattern:** Date format may vary, need robust URL builder
3. **Data Reconciliation:** Turnover vs Position data measure different things
4. **Float Calculation:** Need shares outstanding data to calculate % of float

---

## Estimated Development Effort

| Task | Effort |
|------|--------|
| SFC CSV fetcher | 2 hours |
| HKEX scraper (with browser automation) | 4-6 hours |
| Database schema & storage | 2 hours |
| Historical backfill | 2 hours |
| Integration with TA analyzer | 3 hours |
| Testing & refinement | 3 hours |
| **Total** | **16-18 hours** |

---

## Recommendation

**Start with SFC Position Data (Phase 1):**
1. Easier to implement (direct CSV)
2. Position-based data is more meaningful for analysis
3. Historical data available for backtesting

**Then add HKEX Turnover (Phase 2):**
1. Daily granularity for active monitoring
2. Requires browser automation
3. Good for intraday/short-term signals

---

## Alternative: Commercial Data Providers

If free sources prove unreliable:

| Provider | Coverage | Cost |
|----------|----------|------|
| Refinitiv | Full HK short data | $$$ |
| Bloomberg | Full HK short data | $$$ |
| HKEX Data Products | Official API | ~HK$500-2000/month |

---

## Next Steps

1. ✅ Feasibility confirmed
2. 🔲 Confirm implementation priority (SFC first?)
3. 🔲 Set up cron job for weekly SFC fetch
4. 🔲 Build HKEX scraper with Playwright
5. 🔲 Integrate into market analyzer

---

*Report generated by Oracle 🐷*
