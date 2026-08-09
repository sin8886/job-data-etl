-- Table: public.jobs

-- DROP TABLE IF EXISTS public.jobs;

CREATE TABLE IF NOT EXISTS public.jobs
(
    id integer NOT NULL DEFAULT nextval('jobs_id_seq'::regclass),
    title text COLLATE pg_catalog."default" NOT NULL,
    company_id integer,
    location text COLLATE pg_catalog."default",
    salary_estimate text COLLATE pg_catalog."default",
    easy_apply text COLLATE pg_catalog."default",
    CONSTRAINT jobs_pkey PRIMARY KEY (id),
    CONSTRAINT jobs_unique UNIQUE (company_id, title, location),
    CONSTRAINT jobs_company_id_fkey FOREIGN KEY (company_id)
        REFERENCES public.companies (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.jobs
    OWNER to postgres;
-- Index: idx_jobs_company_id

-- DROP INDEX IF EXISTS public.idx_jobs_company_id;

CREATE INDEX IF NOT EXISTS idx_jobs_company_id
    ON public.jobs USING btree
    (company_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: idx_jobs_title

-- DROP INDEX IF EXISTS public.idx_jobs_title;

CREATE INDEX IF NOT EXISTS idx_jobs_title
    ON public.jobs USING btree
    (title COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
    -- Table: public.companies

-- DROP TABLE IF EXISTS public.companies;

CREATE TABLE IF NOT EXISTS public.companies
(
    id integer NOT NULL DEFAULT nextval('companies_id_seq'::regclass),
    name text COLLATE pg_catalog."default" NOT NULL,
    industry text COLLATE pg_catalog."default",
    sector text COLLATE pg_catalog."default",
    rating double precision,
    revenue text COLLATE pg_catalog."default",
    headquarters text COLLATE pg_catalog."default",
    size text COLLATE pg_catalog."default",
    founded text COLLATE pg_catalog."default",
    CONSTRAINT companies_pkey PRIMARY KEY (id),
    CONSTRAINT companies_name_unique UNIQUE (name)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.companies
    OWNER to postgres;
    -- Table: public.pipeline_runs

-- DROP TABLE IF EXISTS public.pipeline_runs;

CREATE TABLE IF NOT EXISTS public.pipeline_runs
(
    run_id integer NOT NULL DEFAULT nextval('pipeline_runs_run_id_seq'::regclass),
    started_at timestamp without time zone NOT NULL,
    finished_at timestamp without time zone,
    row_count integer,
    status character varying(20) COLLATE pg_catalog."default",
    CONSTRAINT pipeline_runs_pkey PRIMARY KEY (run_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.pipeline_runs
    OWNER to postgres;