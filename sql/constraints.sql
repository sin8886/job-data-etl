ALTER TABLE companies
ADD CONSTRAINT companies_name_unique
UNIQUE(name);

ALTER TABLE jobs
ADD CONSTRAINT jobs_unique
UNIQUE (
    company_id,
    title,
    location
);