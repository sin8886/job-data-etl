-- Check whether the index on company_id is used
EXPLAIN ANALYZE
SELECT *
FROM jobs
WHERE company_id = 10;


-- Check whether the index on title is used
EXPLAIN ANALYZE
SELECT *
FROM jobs
WHERE title = 'Data Analyst';


-- Check the performance of joining jobs and companies
EXPLAIN ANALYZE
SELECT
    j.title,
    c.name
FROM jobs j
JOIN companies c
ON j.company_id = c.id;