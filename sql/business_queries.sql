-- 1. Count the number of distinct companies
SELECT COUNT(DISTINCT name)
FROM companies;


-- 2. Count jobs from companies in the tech industry
SELECT COUNT(*)
FROM jobs
WHERE company_id IN (
    SELECT id
    FROM companies
    WHERE industry ILIKE '%tech%'
);


-- 3. Find companies that have at least one job posting
SELECT name
FROM companies c
WHERE EXISTS (
    SELECT 1
    FROM jobs j
    WHERE j.company_id = c.id
);


-- 4. Find duplicate job titles
SELECT
    title,
    COUNT(*) AS job_count
FROM jobs
GROUP BY title
HAVING COUNT(*) > 1;


-- 5. Count jobs by location
SELECT
    location,
    COUNT(*) AS job_count
FROM jobs
GROUP BY location
ORDER BY job_count DESC;