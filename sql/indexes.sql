-- optimize jobs-company relationship
CREATE INDEX IF NOT EXISTS idx_jobs_company_id
ON jobs(company_id);


-- optimize grouping/search by job title
CREATE INDEX IF NOT EXISTS idx_jobs_title
ON jobs(title);