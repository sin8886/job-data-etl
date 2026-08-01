SELECT COUNT(DISTINCT name)
FROM companies;

SELECT COUNT(*)
FROM jobs
WHERE company_id IN (
    SELECT id
    FROM companies
    WHERE industry ILIKE '%tech%'
);

SELECT name
FROM companies c
WHERE EXISTS (
    SELECT 1
    FROM jobs j
    WHERE j.company_id = c.id
);

SELECT title, COUNT(*)
FROM jobs
GROUP BY title
HAVING COUNT(*) > 1;

SELECT location, COUNT(*)
FROM jobs
GROUP BY location
ORDER BY COUNT(*) DESC;

