# Project Insights — Ireland Data Job Market Analytics

These are my personal observations from running this scraper and analysing the results. Not just "here are the numbers" — but what the numbers actually mean for someone trying to get their first data role in Ireland.

---

## On the Skills Question — What Irish Employers Actually Want

Before I built this, I assumed the Irish tech market would be heavily skewed toward cloud tools and modern data stack technologies — dbt, Snowflake, Airflow — because of the density of large multinationals in Dublin (Google, Meta, LinkedIn, Stripe, Salesforce).

The reality is more nuanced. SQL and Python dominate across every role type and seniority level. They appear in more listings than any other skill by a factor of 2–3x. Excel still appears more than most data professionals expect — particularly in analyst roles at financial services firms, of which there are many in Dublin (Citi, Bank of America, JP Morgan all have major operations here).

For someone just starting out, this data gives a clear prioritisation: SQL first, Python second, Excel third, then pick one visualisation tool (Power BI is more common than Tableau in the Irish market based on this data). Everything else — dbt, Snowflake, Spark — comes after you have the fundamentals down.

---

## On the Internship Market Specifically

Internship and graduate listings are a smaller proportion of total data job listings than I expected. They are also less likely to specify salary, which makes it harder to benchmark.

The companies that consistently post internship and graduate roles tend to be larger organisations with structured graduate programmes — multinationals and large Irish companies rather than startups. This matters because it tells you where to focus your applications: a targeted list of 20 companies with structured programmes is more effective than a broad spray of applications across 200 listings.

The SQL query in this project (Q16 — the internship target score) attempts to formalise this: it ranks companies by intern role volume, role diversity, and salary transparency. That ranked list is arguably the most practically useful output of this entire project for someone in my position.

---

## On Dublin vs the Rest of Ireland

Dublin accounts for roughly 70–75% of data role listings in this dataset. That is a large concentration, but the Remote and Hybrid share is meaningful — roughly 15–20% of listings depending on the week. Post-2020, hybrid working is genuinely embedded in Irish tech culture in a way it is not in many other European markets.

Cork is the second city for data roles, driven by Apple, VMware, and a growing startup scene around the Cork tech cluster. Galway is smaller but has Medtronic, Abbott and a number of other large employers with data functions. For someone who cannot or does not want to be in Dublin, the Cork and Galway markets are worth targeting specifically rather than treating as fallbacks.

---

## On the Automation — Why GitHub Actions Matters

Most portfolio projects are static. They were built once, the data was collected once, and nothing has changed since. This project is different because GitHub Actions runs the scraper every Monday. The data in the dashboard reflects the actual state of the Irish job market this week, not six months ago.

This matters for two reasons. First, it means the insights stay relevant — if demand for a particular skill spikes or a wave of new internship postings appears, the dashboard captures it. Second, it demonstrates a skill that is genuinely valued in data roles: the ability to build automated pipelines that run without manual intervention. Any data team running production pipelines will recognise that capability immediately.

---

## On Salary Transparency

The salary transparency picture in Irish job listings is poor. Most listings do not include salary information. When I dug into which companies do list salaries consistently, a pattern emerged: it tends to be either large multinationals with structured compensation bands (where salary is not a negotiating point, it is a published range) or companies actively competing for scarce talent who use salary transparency as a differentiator.

For a job seeker, this is actually useful information. A company that consistently lists salary ranges is signalling something about its culture and HR maturity — both of which correlate with better candidate experience and more structured onboarding. These companies are worth prioritising not just for the salary information but for what that transparency signals about the organisation.

---

*This project was built to answer real questions I had as someone actively looking for data internships in Ireland. Every query, every dashboard view, and every insight here started with a question I genuinely needed answered.*
