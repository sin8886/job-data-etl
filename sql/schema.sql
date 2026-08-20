-- =========================================
-- Schema for ETL Project
-- =========================================


-- =========================================
-- Companies table
-- =========================================

CREATE TABLE IF NOT EXISTS public.companies
(
    id integer NOT NULL DEFAULT nextval('companies_id_seq'::regclass),
    name text NOT NULL,
    industry text,
    sector text,
    rating double precision,
    revenue text,
    headquarters text,
    size text,
    founded text,

    CONSTRAINT companies_pkey PRIMARY KEY (id)
);

-- Company identity is case-insensitive and ignores leading/trailing spaces.
-- A functional unique index is required because UNIQUE(name) is case-sensitive.
CREATE UNIQUE INDEX IF NOT EXISTS companies_name_ci_unique
ON public.companies ((lower(btrim(name))));


-- =========================================
-- Jobs table
-- =========================================

CREATE TABLE IF NOT EXISTS public.jobs
(
    id integer NOT NULL DEFAULT nextval('jobs_id_seq'::regclass),
    title text NOT NULL,
    company_id integer NOT NULL,
    location text,
    salary_estimate text,
    easy_apply text,

    CONSTRAINT jobs_pkey PRIMARY KEY (id),

    CONSTRAINT jobs_unique
        UNIQUE (company_id, title, location),

    CONSTRAINT jobs_company_id_fkey
        FOREIGN KEY (company_id)
        REFERENCES public.companies(id)
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);


-- =========================================
-- Pipeline audit table
-- =========================================

CREATE TABLE IF NOT EXISTS public.pipeline_runs
(
    run_id integer NOT NULL DEFAULT nextval('pipeline_runs_run_id_seq'::regclass),

    started_at timestamp NOT NULL,

    finished_at timestamp,

    row_count integer,

    status varchar(20),

    run_type varchar(20),

    failed_step varchar(50),

    error_message text,

    CONSTRAINT pipeline_runs_pkey PRIMARY KEY (run_id)
);
