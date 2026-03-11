-- ============================================================
-- Ireland Job Market Analytics — SQL Analysis Queries
-- ============================================================
-- Author:      Ishan Kasare
-- GitHub:      https://github.com/Ishankasare/Ireland-Job-Market-Analytics
--
-- Description:
--   Analytical queries against the jobs table in SQLite.
--   Run these after scraper.py has populated the database.
--
-- Techniques:
--   - Window functions (RANK, ROW_NUMBER, PERCENT_RANK)
--   - CTEs (Common Table Expressions)
--   - CASE WHEN classification
--   - GROUP BY aggregations
--   - Subqueries
--   - String pattern matching
-- ============================================================


-- ── TABLE SCHEMA ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT,
    company         TEXT,
    location        TEXT,
    salary          TEXT,
    salary_clean    TEXT,
    summary         TEXT,
    posted          TEXT,
    source          TEXT,
    search_term     TEXT,
    job_type        TEXT,
    seniority       TEXT,
    skills_mentioned TEXT,
    scraped_at      TEXT
);


-- ============================================================
-- SECTION 1 — OVERVIEW
-- ============================================================

-- Q1: How many total job listings did we collect?
SELECT
    COUNT(*)            AS total_listings,
    COUNT(DISTINCT company) AS unique_companies,
    COUNT(DISTINCT title)   AS unique_job_titles,
    MIN(scraped_at)     AS first_scraped,
    MAX(scraped_at)     AS last_scraped
FROM jobs;


-- Q2: How many listings per source?
SELECT
    source,
    COUNT(*) AS total_listings,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_total
FROM jobs
GROUP BY source
ORDER BY total_listings DESC;


-- Q3: Breakdown by job type
SELECT
    job_type,
    COUNT(*) AS total,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM jobs
GROUP BY job_type
ORDER BY total DESC;


-- ============================================================
-- SECTION 2 — COMPANIES
-- ============================================================

-- Q4: Top 20 companies hiring the most data roles in Ireland
SELECT
    company,
    COUNT(*) AS open_roles,
    COUNT(DISTINCT job_type) AS role_types,
    GROUP_CONCAT(DISTINCT job_type) AS types_hiring
FROM jobs
GROUP BY company
ORDER BY open_roles DESC
LIMIT 20;


-- Q5: Companies hiring interns specifically
SELECT
    company,
    COUNT(*) AS intern_roles,
    GROUP_CONCAT(DISTINCT title) AS intern_titles
FROM jobs
WHERE job_type = 'Internship / Graduate'
GROUP BY company
ORDER BY intern_roles DESC
LIMIT 20;


-- Q6: Which companies are hiring across the most seniority levels?
-- (signals large data teams = good for career growth)
SELECT
    company,
    COUNT(DISTINCT seniority) AS seniority_levels,
    GROUP_CONCAT(DISTINCT seniority) AS levels
FROM jobs
GROUP BY company
HAVING seniority_levels >= 2
ORDER BY seniority_levels DESC, company
LIMIT 20;


-- ============================================================
-- SECTION 3 — SKILLS DEMAND
-- ============================================================

-- Q7: Most in-demand skills across all data roles
-- (unnests the comma-separated skills_mentioned column)
WITH skill_rows AS (
    SELECT TRIM(value) AS skill
    FROM jobs, json_each('["' || REPLACE(skills_mentioned, ', ', '","') || '"]')
    WHERE skills_mentioned IS NOT NULL AND skills_mentioned != ''
)
SELECT
    skill,
    COUNT(*) AS mentions,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS demand_rank
FROM skill_rows
WHERE skill != ''
GROUP BY skill
ORDER BY mentions DESC
LIMIT 20;


-- Q8: Top skills required for internship/graduate roles specifically
WITH skill_rows AS (
    SELECT TRIM(value) AS skill
    FROM jobs, json_each('["' || REPLACE(skills_mentioned, ', ', '","') || '"]')
    WHERE skills_mentioned IS NOT NULL
      AND skills_mentioned != ''
      AND job_type = 'Internship / Graduate'
)
SELECT
    skill,
    COUNT(*) AS mentions
FROM skill_rows
WHERE skill != ''
GROUP BY skill
ORDER BY mentions DESC
LIMIT 15;


-- Q9: Skills gap — skills in senior roles vs entry roles
WITH senior_skills AS (
    SELECT TRIM(value) AS skill, 'Senior' AS level
    FROM jobs, json_each('["' || REPLACE(skills_mentioned, ', ', '","') || '"]')
    WHERE seniority = 'Senior' AND skills_mentioned != ''
),
junior_skills AS (
    SELECT TRIM(value) AS skill, 'Junior' AS level
    FROM jobs, json_each('["' || REPLACE(skills_mentioned, ', ', '","') || '"]')
    WHERE seniority = 'Junior / Entry' AND skills_mentioned != ''
)
SELECT
    COALESCE(s.skill, j.skill) AS skill,
    COUNT(DISTINCT CASE WHEN s.level = 'Senior' THEN 1 END) AS senior_demand,
    COUNT(DISTINCT CASE WHEN j.level = 'Junior' THEN 1 END) AS junior_demand
FROM senior_skills s
FULL OUTER JOIN junior_skills j ON s.skill = j.skill
GROUP BY skill
ORDER BY senior_demand DESC
LIMIT 20;


-- ============================================================
-- SECTION 4 — LOCATION ANALYSIS
-- ============================================================

-- Q10: Which cities/counties have the most data jobs?
SELECT
    CASE
        WHEN location LIKE '%Dublin%'    THEN 'Dublin'
        WHEN location LIKE '%Cork%'      THEN 'Cork'
        WHEN location LIKE '%Limerick%'  THEN 'Limerick'
        WHEN location LIKE '%Galway%'    THEN 'Galway'
        WHEN location LIKE '%Remote%'    THEN 'Remote'
        WHEN location LIKE '%Hybrid%'    THEN 'Hybrid / Flexible'
        ELSE 'Other / Not Specified'
    END AS city,
    COUNT(*) AS listings,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM jobs
GROUP BY city
ORDER BY listings DESC;


-- Q11: Remote vs hybrid vs on-site split
SELECT
    CASE
        WHEN LOWER(title || ' ' || COALESCE(summary, '')) LIKE '%remote%' THEN 'Remote'
        WHEN LOWER(title || ' ' || COALESCE(summary, '')) LIKE '%hybrid%' THEN 'Hybrid'
        ELSE 'On-site / Not Specified'
    END AS work_model,
    COUNT(*) AS listings
FROM jobs
GROUP BY work_model
ORDER BY listings DESC;


-- ============================================================
-- SECTION 5 — SALARY ANALYSIS
-- ============================================================

-- Q12: Jobs that specify a salary vs those that don't
SELECT
    CASE WHEN salary_clean = 'Not specified' THEN 'No Salary Listed'
         ELSE 'Salary Listed' END AS salary_transparency,
    COUNT(*) AS listings,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM jobs
GROUP BY salary_transparency;


-- Q13: Which companies are most transparent about salary?
SELECT
    company,
    COUNT(*) AS total_roles,
    SUM(CASE WHEN salary_clean != 'Not specified' THEN 1 ELSE 0 END) AS roles_with_salary,
    ROUND(
        SUM(CASE WHEN salary_clean != 'Not specified' THEN 1.0 ELSE 0 END) / COUNT(*) * 100,
        0
    ) AS salary_transparency_pct
FROM jobs
GROUP BY company
HAVING total_roles >= 3
ORDER BY salary_transparency_pct DESC
LIMIT 20;


-- ============================================================
-- SECTION 6 — TREND ANALYSIS
-- ============================================================

-- Q14: Listings scraped per day (trend over time)
SELECT
    DATE(scraped_at) AS scrape_date,
    COUNT(*) AS new_listings,
    SUM(COUNT(*)) OVER (ORDER BY DATE(scraped_at)) AS cumulative_total
FROM jobs
GROUP BY scrape_date
ORDER BY scrape_date;


-- Q15: Which job types are growing fastest week over week?
WITH weekly AS (
    SELECT
        strftime('%W', scraped_at) AS week_num,
        job_type,
        COUNT(*) AS listings
    FROM jobs
    GROUP BY week_num, job_type
)
SELECT
    job_type,
    week_num,
    listings,
    LAG(listings) OVER (PARTITION BY job_type ORDER BY week_num) AS prev_week,
    listings - LAG(listings) OVER (PARTITION BY job_type ORDER BY week_num) AS week_on_week_change
FROM weekly
ORDER BY job_type, week_num;


-- ============================================================
-- SECTION 7 — RANKING & SCORING
-- ============================================================

-- Q16: Score each company as an internship target
-- (more roles + more skill variety + salary transparency = higher score)
WITH company_stats AS (
    SELECT
        company,
        COUNT(*) AS total_roles,
        SUM(CASE WHEN job_type = 'Internship / Graduate' THEN 1 ELSE 0 END) AS intern_roles,
        COUNT(DISTINCT job_type) AS role_diversity,
        ROUND(
            SUM(CASE WHEN salary_clean != 'Not specified' THEN 1.0 ELSE 0 END) / COUNT(*) * 100,
            0
        ) AS salary_transparency
    FROM jobs
    GROUP BY company
    HAVING total_roles >= 2
)
SELECT
    company,
    total_roles,
    intern_roles,
    role_diversity,
    salary_transparency,
    -- Simple composite score
    (intern_roles * 3 + role_diversity * 2 + ROUND(salary_transparency / 20)) AS internship_target_score
FROM company_stats
ORDER BY internship_target_score DESC
LIMIT 20;


-- Q17: Rank companies by total data hiring volume
SELECT
    RANK() OVER (ORDER BY COUNT(*) DESC) AS hiring_rank,
    company,
    COUNT(*) AS total_listings,
    GROUP_CONCAT(DISTINCT job_type) AS role_types
FROM jobs
GROUP BY company
ORDER BY total_listings DESC
LIMIT 25;
