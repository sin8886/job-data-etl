-- Day 20: make company identity case-insensitive and require every job
-- to reference a company.
--
-- This migration is safe to run again. It keeps existing primary-key values:
--   1146 (Taskrabbit) and 1164 (TEXAS EDUCATION AGENCY).
-- It first repoints jobs, then deletes only the duplicate company rows.

BEGIN;

LOCK TABLE public.companies, public.jobs IN SHARE ROW EXCLUSIVE MODE;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.jobs WHERE company_id IS NULL) THEN
        RAISE EXCEPTION 'Cannot set jobs.company_id to NOT NULL: NULL values exist';
    END IF;

    -- Do not silently merge any unreviewed duplicate company groups.
    IF EXISTS (
        SELECT 1
        FROM public.companies
        GROUP BY lower(btrim(name))
        HAVING COUNT(*) > 1
           AND lower(btrim(name)) NOT IN ('taskrabbit', 'texas education agency')
    ) THEN
        RAISE EXCEPTION 'Unreviewed case-insensitive company duplicates exist';
    END IF;

    -- Before changing foreign keys, prove that the target company does not
    -- already have an identical job under jobs_unique.
    IF EXISTS (
        SELECT 1
        FROM public.jobs source_job
        JOIN (VALUES (1339, 1146), (1191, 1164)) AS company_map(old_id, keep_id)
          ON source_job.company_id = company_map.old_id
        JOIN public.jobs target_job
          ON target_job.company_id = company_map.keep_id
         AND target_job.title IS NOT DISTINCT FROM source_job.title
         AND target_job.location IS NOT DISTINCT FROM source_job.location
    ) THEN
        RAISE EXCEPTION 'Company merge would violate jobs_unique';
    END IF;
END $$;

UPDATE public.jobs AS j
SET company_id = company_map.keep_id
FROM (VALUES (1339, 1146), (1191, 1164)) AS company_map(old_id, keep_id)
WHERE j.company_id = company_map.old_id;

DELETE FROM public.companies AS c
USING (VALUES (1339), (1191)) AS duplicate_company(id)
WHERE c.id = duplicate_company.id;

ALTER TABLE public.companies
    DROP CONSTRAINT IF EXISTS companies_name_unique;

CREATE UNIQUE INDEX IF NOT EXISTS companies_name_ci_unique
    ON public.companies ((lower(btrim(name))));

ALTER TABLE public.jobs
    ALTER COLUMN company_id SET NOT NULL;

COMMIT;
