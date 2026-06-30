--
-- PostgreSQL database dump
--

\restrict dxS8nbJ2rhubT4jrjMOiyCWmDjWTo2BcVhGvsZ0Hssujn9H7aNJZTIhZ48Cj8mg

-- Dumped from database version 16.14 (Debian 16.14-1.pgdg13+1)
-- Dumped by pg_dump version 16.14 (Debian 16.14-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.weekly_timesheets DROP CONSTRAINT IF EXISTS weekly_timesheets_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.weekly_timesheet_entries DROP CONSTRAINT IF EXISTS weekly_timesheet_entries_timesheet_id_fkey;
ALTER TABLE IF EXISTS ONLY public.weekly_timesheet_entries DROP CONSTRAINT IF EXISTS weekly_timesheet_entries_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_manager_id_fkey;
ALTER TABLE IF EXISTS ONLY public.timesheets DROP CONSTRAINT IF EXISTS timesheets_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.timesheets DROP CONSTRAINT IF EXISTS timesheets_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.teams DROP CONSTRAINT IF EXISTS teams_team_lead_id_fkey;
ALTER TABLE IF EXISTS ONLY public.teams DROP CONSTRAINT IF EXISTS teams_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.team_members DROP CONSTRAINT IF EXISTS team_members_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.team_members DROP CONSTRAINT IF EXISTS team_members_team_id_fkey;
ALTER TABLE IF EXISTS ONLY public.tasks DROP CONSTRAINT IF EXISTS tasks_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.tasks DROP CONSTRAINT IF EXISTS tasks_assigned_to_fkey;
ALTER TABLE IF EXISTS ONLY public.tasks DROP CONSTRAINT IF EXISTS tasks_assigned_by_fkey;
ALTER TABLE IF EXISTS ONLY public.subtasks DROP CONSTRAINT IF EXISTS subtasks_task_id_fkey;
ALTER TABLE IF EXISTS ONLY public.subtasks DROP CONSTRAINT IF EXISTS subtasks_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.salary_slips DROP CONSTRAINT IF EXISTS salary_slips_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.reimbursements DROP CONSTRAINT IF EXISTS reimbursements_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.projects DROP CONSTRAINT IF EXISTS projects_client_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_assignments DROP CONSTRAINT IF EXISTS project_assignments_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.project_assignments DROP CONSTRAINT IF EXISTS project_assignments_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.leave_requests DROP CONSTRAINT IF EXISTS leave_requests_employee_id_fkey;
ALTER TABLE IF EXISTS ONLY public.invoices DROP CONSTRAINT IF EXISTS invoices_project_id_fkey;
ALTER TABLE IF EXISTS ONLY public.invoices DROP CONSTRAINT IF EXISTS invoices_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.invoices DROP CONSTRAINT IF EXISTS invoices_client_id_fkey;
ALTER TABLE IF EXISTS ONLY public.invoices DROP CONSTRAINT IF EXISTS invoices_bank_account_id_fkey;
ALTER TABLE IF EXISTS ONLY public.invoice_items DROP CONSTRAINT IF EXISTS invoice_items_invoice_id_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_added_by_fkey;
ALTER TABLE IF EXISTS ONLY public.estimates DROP CONSTRAINT IF EXISTS estimates_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.estimate_employees DROP CONSTRAINT IF EXISTS estimate_employees_estimate_id_fkey;
ALTER TABLE IF EXISTS ONLY public.attendance DROP CONSTRAINT IF EXISTS attendance_employee_id_fkey;
DROP INDEX IF EXISTS public.ix_weekly_timesheets_id;
DROP INDEX IF EXISTS public.ix_teams_project_id;
DROP INDEX IF EXISTS public.ix_team_members_user_id;
DROP INDEX IF EXISTS public.ix_team_members_team_id;
ALTER TABLE IF EXISTS ONLY public.weekly_timesheets DROP CONSTRAINT IF EXISTS weekly_timesheets_pkey;
ALTER TABLE IF EXISTS ONLY public.weekly_timesheet_entries DROP CONSTRAINT IF EXISTS weekly_timesheet_entries_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_studio_email_key;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_personal_mail_key;
ALTER TABLE IF EXISTS ONLY public.team_members DROP CONSTRAINT IF EXISTS uq_team_user;
ALTER TABLE IF EXISTS ONLY public.salary_slips DROP CONSTRAINT IF EXISTS uq_salary_slip_employee_month;
ALTER TABLE IF EXISTS ONLY public.timesheets DROP CONSTRAINT IF EXISTS timesheets_pkey;
ALTER TABLE IF EXISTS ONLY public.teams DROP CONSTRAINT IF EXISTS teams_pkey;
ALTER TABLE IF EXISTS ONLY public.team_members DROP CONSTRAINT IF EXISTS team_members_pkey;
ALTER TABLE IF EXISTS ONLY public.tasks DROP CONSTRAINT IF EXISTS tasks_pkey;
ALTER TABLE IF EXISTS ONLY public.subtasks DROP CONSTRAINT IF EXISTS subtasks_pkey;
ALTER TABLE IF EXISTS ONLY public.settings DROP CONSTRAINT IF EXISTS settings_pkey;
ALTER TABLE IF EXISTS ONLY public.salary_slips DROP CONSTRAINT IF EXISTS salary_slips_pkey;
ALTER TABLE IF EXISTS ONLY public.reimbursements DROP CONSTRAINT IF EXISTS reimbursements_pkey;
ALTER TABLE IF EXISTS ONLY public.projects DROP CONSTRAINT IF EXISTS projects_project_number_key;
ALTER TABLE IF EXISTS ONLY public.projects DROP CONSTRAINT IF EXISTS projects_pkey;
ALTER TABLE IF EXISTS ONLY public.project_assignments DROP CONSTRAINT IF EXISTS project_assignments_pkey;
ALTER TABLE IF EXISTS ONLY public.leave_requests DROP CONSTRAINT IF EXISTS leave_requests_pkey;
ALTER TABLE IF EXISTS ONLY public.invoices DROP CONSTRAINT IF EXISTS invoices_pkey;
ALTER TABLE IF EXISTS ONLY public.invoice_items DROP CONSTRAINT IF EXISTS invoice_items_pkey;
ALTER TABLE IF EXISTS ONLY public.holidays DROP CONSTRAINT IF EXISTS holidays_pkey;
ALTER TABLE IF EXISTS ONLY public.holidays DROP CONSTRAINT IF EXISTS holidays_date_key;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_pkey;
ALTER TABLE IF EXISTS ONLY public.estimates DROP CONSTRAINT IF EXISTS estimates_pkey;
ALTER TABLE IF EXISTS ONLY public.estimate_employees DROP CONSTRAINT IF EXISTS estimate_employees_pkey;
ALTER TABLE IF EXISTS ONLY public.clients DROP CONSTRAINT IF EXISTS clients_pkey;
ALTER TABLE IF EXISTS ONLY public.bank_accounts DROP CONSTRAINT IF EXISTS bank_accounts_pkey;
ALTER TABLE IF EXISTS ONLY public.attendance DROP CONSTRAINT IF EXISTS attendance_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS public.weekly_timesheets ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.weekly_timesheet_entries ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.timesheets ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.teams ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.team_members ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.tasks ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.subtasks ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.salary_slips ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.reimbursements ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.projects ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.project_assignments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.leave_requests ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.invoices ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.invoice_items ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.holidays ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.expenses ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.estimates ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.estimate_employees ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.clients ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.bank_accounts ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.attendance ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.weekly_timesheets_id_seq;
DROP TABLE IF EXISTS public.weekly_timesheets;
DROP SEQUENCE IF EXISTS public.weekly_timesheet_entries_id_seq;
DROP TABLE IF EXISTS public.weekly_timesheet_entries;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.timesheets_id_seq;
DROP TABLE IF EXISTS public.timesheets;
DROP SEQUENCE IF EXISTS public.teams_id_seq;
DROP TABLE IF EXISTS public.teams;
DROP SEQUENCE IF EXISTS public.team_members_id_seq;
DROP TABLE IF EXISTS public.team_members;
DROP SEQUENCE IF EXISTS public.tasks_id_seq;
DROP TABLE IF EXISTS public.tasks;
DROP SEQUENCE IF EXISTS public.subtasks_id_seq;
DROP TABLE IF EXISTS public.subtasks;
DROP TABLE IF EXISTS public.settings;
DROP SEQUENCE IF EXISTS public.salary_slips_id_seq;
DROP TABLE IF EXISTS public.salary_slips;
DROP SEQUENCE IF EXISTS public.reimbursements_id_seq;
DROP TABLE IF EXISTS public.reimbursements;
DROP SEQUENCE IF EXISTS public.projects_id_seq;
DROP TABLE IF EXISTS public.projects;
DROP SEQUENCE IF EXISTS public.project_assignments_id_seq;
DROP TABLE IF EXISTS public.project_assignments;
DROP SEQUENCE IF EXISTS public.leave_requests_id_seq;
DROP TABLE IF EXISTS public.leave_requests;
DROP SEQUENCE IF EXISTS public.invoices_id_seq;
DROP TABLE IF EXISTS public.invoices;
DROP SEQUENCE IF EXISTS public.invoice_items_id_seq;
DROP TABLE IF EXISTS public.invoice_items;
DROP SEQUENCE IF EXISTS public.holidays_id_seq;
DROP TABLE IF EXISTS public.holidays;
DROP SEQUENCE IF EXISTS public.expenses_id_seq;
DROP TABLE IF EXISTS public.expenses;
DROP SEQUENCE IF EXISTS public.estimates_id_seq;
DROP TABLE IF EXISTS public.estimates;
DROP SEQUENCE IF EXISTS public.estimate_employees_id_seq;
DROP TABLE IF EXISTS public.estimate_employees;
DROP SEQUENCE IF EXISTS public.clients_id_seq;
DROP TABLE IF EXISTS public.clients;
DROP SEQUENCE IF EXISTS public.bank_accounts_id_seq;
DROP TABLE IF EXISTS public.bank_accounts;
DROP SEQUENCE IF EXISTS public.attendance_id_seq;
DROP TABLE IF EXISTS public.attendance;
DROP TABLE IF EXISTS public.alembic_version;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: attendance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attendance (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    date date NOT NULL,
    check_in character varying,
    check_out character varying,
    is_site_visit boolean,
    site_name character varying,
    site_timing character varying
);


--
-- Name: attendance_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.attendance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: attendance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.attendance_id_seq OWNED BY public.attendance.id;


--
-- Name: bank_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bank_accounts (
    id integer NOT NULL,
    bank_name character varying NOT NULL,
    account_number character varying NOT NULL,
    account_type character varying NOT NULL,
    account_holder_name character varying NOT NULL,
    ifsc_code character varying NOT NULL,
    is_active boolean
);


--
-- Name: bank_accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.bank_accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: bank_accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.bank_accounts_id_seq OWNED BY public.bank_accounts.id;


--
-- Name: clients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clients (
    id integer NOT NULL,
    name character varying NOT NULL,
    email character varying NOT NULL,
    phone character varying NOT NULL,
    address character varying NOT NULL,
    gstin character varying
);


--
-- Name: clients_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.clients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: clients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.clients_id_seq OWNED BY public.clients.id;


--
-- Name: estimate_employees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.estimate_employees (
    id integer NOT NULL,
    estimate_id integer,
    emp_type character varying NOT NULL,
    base_pay numeric(10,2) NOT NULL,
    hrs_per_day numeric(4,1) DEFAULT 8,
    pay_per_hour numeric(10,2) DEFAULT 0,
    total_hours numeric(10,2) DEFAULT 0,
    total_cost numeric(12,2) DEFAULT 0
);


--
-- Name: estimate_employees_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.estimate_employees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: estimate_employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.estimate_employees_id_seq OWNED BY public.estimate_employees.id;


--
-- Name: estimates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.estimates (
    id integer NOT NULL,
    project_name character varying NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    working_days integer DEFAULT 0,
    partner_pay_per_hour numeric(10,2) DEFAULT 0,
    partner_cost numeric(12,2) DEFAULT 0,
    team_cost numeric(12,2) DEFAULT 0,
    grand_total numeric(12,2) DEFAULT 0,
    project_color character varying DEFAULT '#287475'::character varying,
    status character varying DEFAULT 'draft'::character varying,
    created_by integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: estimates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.estimates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: estimates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.estimates_id_seq OWNED BY public.estimates.id;


--
-- Name: expenses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expenses (
    id integer NOT NULL,
    title character varying NOT NULL,
    category character varying NOT NULL,
    amount numeric(10,2) NOT NULL,
    date date NOT NULL,
    recurring boolean,
    notes character varying,
    added_by integer NOT NULL
);


--
-- Name: expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expenses_id_seq OWNED BY public.expenses.id;


--
-- Name: holidays; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.holidays (
    id integer NOT NULL,
    date date NOT NULL,
    name character varying NOT NULL
);


--
-- Name: holidays_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.holidays_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: holidays_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.holidays_id_seq OWNED BY public.holidays.id;


--
-- Name: invoice_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.invoice_items (
    id integer NOT NULL,
    invoice_id integer NOT NULL,
    description character varying NOT NULL,
    hsn_sac character varying,
    amount numeric(12,2) NOT NULL
);


--
-- Name: invoice_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.invoice_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: invoice_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.invoice_items_id_seq OWNED BY public.invoice_items.id;


--
-- Name: invoices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.invoices (
    id integer NOT NULL,
    invoice_type character varying NOT NULL,
    invoice_number character varying,
    invoice_date date,
    place_of_supply character varying,
    bill_to_name character varying,
    bill_to_address character varying,
    bill_to_gstin character varying,
    ship_to_name character varying,
    ship_to_address character varying,
    ship_to_gstin character varying,
    subject character varying,
    subtotal numeric(12,2),
    cgst numeric(12,2),
    sgst numeric(12,2),
    igst numeric(12,2),
    total numeric(12,2),
    tax_type character varying,
    project_id integer,
    client_id integer,
    bank_account_id integer,
    created_by integer
);


--
-- Name: invoices_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.invoices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: invoices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.invoices_id_seq OWNED BY public.invoices.id;


--
-- Name: leave_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.leave_requests (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    reason character varying,
    status character varying,
    days_count integer NOT NULL,
    paid_days integer DEFAULT 0,
    unpaid_days integer DEFAULT 0
);


--
-- Name: leave_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.leave_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: leave_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.leave_requests_id_seq OWNED BY public.leave_requests.id;


--
-- Name: project_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_assignments (
    id integer NOT NULL,
    user_id integer NOT NULL,
    project_id integer NOT NULL,
    base_pay numeric(10,2),
    hourly_rate numeric(8,2)
);


--
-- Name: project_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_assignments_id_seq OWNED BY public.project_assignments.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    project_number character varying NOT NULL,
    name character varying NOT NULL,
    location character varying,
    gmap_link character varying,
    year integer,
    current_stage character varying,
    is_billed character varying,
    client_id integer,
    partner_remuneration numeric(10,2),
    employee_remuneration numeric(10,2),
    project_remuneration numeric(10,2),
    work_order_urls character varying,
    total_assigned_hours numeric(10,2),
    partner_hourly_rate numeric(10,2),
    billed_amount numeric(12,2),
    start_date date,
    end_date date,
    employee_budget numeric(12,2),
    partner_budget numeric(12,2),
    color character varying DEFAULT '#287475'::character varying,
    advance_amount numeric(12,2) DEFAULT 0
);


--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: reimbursements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reimbursements (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    reason character varying NOT NULL,
    date date NOT NULL,
    proof_url character varying,
    status character varying,
    month_added character varying
);


--
-- Name: reimbursements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.reimbursements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reimbursements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.reimbursements_id_seq OWNED BY public.reimbursements.id;


--
-- Name: salary_slips; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.salary_slips (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    month character varying NOT NULL,
    base_salary numeric(12,2) DEFAULT 0,
    tds_percent numeric(5,2) DEFAULT 0,
    tds_amount numeric(12,2) DEFAULT 0,
    reimbursement_total numeric(12,2) DEFAULT 0,
    net_total numeric(12,2) DEFAULT 0,
    payout_date date,
    status character varying DEFAULT 'pending'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    approved_at timestamp without time zone,
    paid_leave_days numeric(5,1) DEFAULT 0,
    unpaid_leave_days numeric(5,1) DEFAULT 0,
    leave_deduction numeric(12,2) DEFAULT 0
);


--
-- Name: salary_slips_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.salary_slips_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: salary_slips_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.salary_slips_id_seq OWNED BY public.salary_slips.id;


--
-- Name: settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.settings (
    id integer NOT NULL,
    company_name character varying,
    company_address character varying,
    company_gstin character varying,
    company_phone character varying,
    company_email character varying,
    company_signatory_name character varying,
    company_signatory_role character varying,
    working_hours_per_month numeric(6,2),
    salary_months_per_year numeric(4,2),
    tds_percent numeric(5,2)
);


--
-- Name: subtasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subtasks (
    id integer NOT NULL,
    task_id integer NOT NULL,
    title character varying NOT NULL,
    description character varying,
    duration_hours numeric(6,2),
    status character varying DEFAULT 'pending'::character varying,
    created_by integer,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: subtasks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.subtasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: subtasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.subtasks_id_seq OWNED BY public.subtasks.id;


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tasks (
    id integer NOT NULL,
    title character varying NOT NULL,
    description character varying,
    date date NOT NULL,
    priority character varying,
    status character varying,
    project_id integer,
    assigned_to integer NOT NULL,
    assigned_by integer NOT NULL,
    duration_hours integer,
    end_date date
);


--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- Name: team_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.team_members (
    id integer NOT NULL,
    team_id integer NOT NULL,
    user_id integer NOT NULL
);


--
-- Name: team_members_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.team_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: team_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.team_members_id_seq OWNED BY public.team_members.id;


--
-- Name: teams; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teams (
    id integer NOT NULL,
    project_id integer NOT NULL,
    name character varying NOT NULL,
    team_lead_id integer,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: teams_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.teams_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: teams_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.teams_id_seq OWNED BY public.teams.id;


--
-- Name: timesheets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.timesheets (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    project_id integer,
    date date NOT NULL,
    hours_logged numeric(5,2) NOT NULL,
    notes character varying
);


--
-- Name: timesheets_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.timesheets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: timesheets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.timesheets_id_seq OWNED BY public.timesheets.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying NOT NULL,
    designation character varying NOT NULL,
    joining_date date NOT NULL,
    end_date date,
    salary_month numeric(10,2),
    leaves_allowed integer,
    pan_number character varying,
    aadhar_number character varying,
    personal_mail character varying NOT NULL,
    studio_email character varying NOT NULL,
    photo_url character varying,
    role character varying,
    is_active boolean,
    hashed_password character varying NOT NULL,
    manager_id integer,
    salary_hour numeric(8,2),
    documents_url character varying,
    time_tracker_login character varying,
    time_tracker_password character varying,
    phone_number character varying,
    emergency_contact_number character varying,
    emergency_contact_relationship character varying,
    gender character varying,
    location character varying,
    bank_name character varying,
    bank_account_number character varying,
    paid_leave_balance numeric(6,1) DEFAULT 0,
    leave_accrued_through character varying
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: weekly_timesheet_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weekly_timesheet_entries (
    id integer NOT NULL,
    timesheet_id integer NOT NULL,
    project_id integer,
    hours numeric(5,2) NOT NULL,
    description character varying,
    daily_hours json
);


--
-- Name: weekly_timesheet_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.weekly_timesheet_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weekly_timesheet_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.weekly_timesheet_entries_id_seq OWNED BY public.weekly_timesheet_entries.id;


--
-- Name: weekly_timesheets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.weekly_timesheets (
    id integer NOT NULL,
    employee_id integer,
    week_start date NOT NULL,
    week_end date NOT NULL,
    total_hours numeric(6,2),
    status character varying NOT NULL,
    description character varying,
    rejection_reason character varying
);


--
-- Name: weekly_timesheets_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.weekly_timesheets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: weekly_timesheets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.weekly_timesheets_id_seq OWNED BY public.weekly_timesheets.id;


--
-- Name: attendance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance ALTER COLUMN id SET DEFAULT nextval('public.attendance_id_seq'::regclass);


--
-- Name: bank_accounts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_accounts ALTER COLUMN id SET DEFAULT nextval('public.bank_accounts_id_seq'::regclass);


--
-- Name: clients id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients ALTER COLUMN id SET DEFAULT nextval('public.clients_id_seq'::regclass);


--
-- Name: estimate_employees id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estimate_employees ALTER COLUMN id SET DEFAULT nextval('public.estimate_employees_id_seq'::regclass);


--
-- Name: estimates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estimates ALTER COLUMN id SET DEFAULT nextval('public.estimates_id_seq'::regclass);


--
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.expenses_id_seq'::regclass);


--
-- Name: holidays id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.holidays ALTER COLUMN id SET DEFAULT nextval('public.holidays_id_seq'::regclass);


--
-- Name: invoice_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice_items ALTER COLUMN id SET DEFAULT nextval('public.invoice_items_id_seq'::regclass);


--
-- Name: invoices id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices ALTER COLUMN id SET DEFAULT nextval('public.invoices_id_seq'::regclass);


--
-- Name: leave_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_requests ALTER COLUMN id SET DEFAULT nextval('public.leave_requests_id_seq'::regclass);


--
-- Name: project_assignments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_assignments ALTER COLUMN id SET DEFAULT nextval('public.project_assignments_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: reimbursements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursements ALTER COLUMN id SET DEFAULT nextval('public.reimbursements_id_seq'::regclass);


--
-- Name: salary_slips id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salary_slips ALTER COLUMN id SET DEFAULT nextval('public.salary_slips_id_seq'::regclass);


--
-- Name: subtasks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subtasks ALTER COLUMN id SET DEFAULT nextval('public.subtasks_id_seq'::regclass);


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- Name: team_members id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_members ALTER COLUMN id SET DEFAULT nextval('public.team_members_id_seq'::regclass);


--
-- Name: teams id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams ALTER COLUMN id SET DEFAULT nextval('public.teams_id_seq'::regclass);


--
-- Name: timesheets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheets ALTER COLUMN id SET DEFAULT nextval('public.timesheets_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: weekly_timesheet_entries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_timesheet_entries ALTER COLUMN id SET DEFAULT nextval('public.weekly_timesheet_entries_id_seq'::regclass);


--
-- Name: weekly_timesheets id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_timesheets ALTER COLUMN id SET DEFAULT nextval('public.weekly_timesheets_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
9b92c826420c
\.


--
-- Data for Name: attendance; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.attendance (id, employee_id, date, check_in, check_out, is_site_visit, site_name, site_timing) FROM stdin;
\.


--
-- Data for Name: bank_accounts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.bank_accounts (id, bank_name, account_number, account_type, account_holder_name, ifsc_code, is_active) FROM stdin;
1	HDFC BANK	50200066919259	Current	STUDIO MH02 LLP	HDFC0009353	t
\.


--
-- Data for Name: clients; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.clients (id, name, email, phone, address, gstin) FROM stdin;
2	Navi Mumbai International Airport Limited	nmial@gmail.com	+919594110281	Office of the Airport Director, Terminal – 1B,\nCSI Airport. Santacruz (E), Mumbai - 400099, Maharashtra.	27AACCN6836G1ZB
3	Studio Changani	changan@gmail.com	+91 98333 50130	Studio Changani Consultancy Private Limited\n3rd Floor, 301, Satya House, Ram Tekdi Marg, Laxman Tekadi, Opposite Dosti. Sewri, Mumbai - 400015	27ABICS9019D1Z7
4	Rocks & Logs	rnl@gmail.com	+91 97690 81171	Dubai	\N
5	Kalpana Struct-Con	kalpanastruct@gmail.com	+91 877 960 9696	Kalpana Struct-Con Pvt. Ltd.\n1006-1008, Cyber One, Greenscape, Plot No. 4&6, Sector-30A, Vashi, Navi Mumbai - 400 703	27AAACK5108Q1Z8
6	Viyonna LLP	viyonna@gmail.com	+91 99301 98622	VIYONAA WORLD LLP \nOffice no-401, Plot no- A-10/2 & A-11, Kamdhenu 23 West, TTC Industrial Area MIDC, Millenium Business Park Sub Post Office, Mahape, Navi Mumbai, Thane,Maharashtra, 400710	27AAXFV0821B1Z5
7	Arsh Consulting Services	arsh@gmail.com	+91 98198 07503	ARSH CONSULTING SERVICES - Sixth Floor,605/A, Asher 16, Road Number 16Z,Wagle Estate MIDC	27AOPPM8543R1ZS
8	Greenscape	gsc@gmail.com	+91 96199 92381	1908, Cyber One, Plot No.1908, Cyber One, Plot No. 4 and 6, Sector 30A, Vashi, Mumbai City, Maharashtra,\nMumbai\n400703 Maharashtra\nIndia	27AAUFG6027H1Z1
9	Neelkanth	neelkanth@gmail.com	+91 77380 20000	Neelkanth Deep Relcon LLP - 4th, F-408, Tower 2, Seawoods Grand Central, Plot No R-1, Sector 40, Seawoods, Navi Mumbai, Thane, Maharashtra, 400706	27AAUFN7075L1ZB
10	Larsen & Toubro	l&t@gmail.com	+91 75499 71563	Larsen and Toubro Limited - Infrastructure Vertical - Navi Mumbai International Airport Project, Near Ambuja Cement, Dapoli, Ulwe - 410206. Landmark - NMMC Head Office, CBD Belapur	27AAACL0140P5ZF
11	PK Das	pkdas@gmail.com	+91 98197 32716	PK Das & Associates - Sankalp, 5th Floor, Plot No. 1040, Off Sayani Road, Prabhadevi, Mumbai - 400025	27AEFPD08471Z5
12	Sandeep Shirke and Associates	ssa@gmail.com	+91 98205 74168	SANDEEP SHIKRE & ASSOCIATES - 2ND FLOOR,203/204, Prabhadevi Industrial Estate, Swatantrya veer sawarkar marg, Prabhadevi, Mumbai, 400025	27AAZPS8232R1ZB
13	MH02	mh02@gmail.com	0000000000	1234	0000000000000
14	ENGINEERING CREATIONS PUBLIC HEALTH CONSULTANCY PVT. LTD.	suyash@ecphc.com	9920905181	1st Floor, 104, Shree Sarika CHS, A K Vaidya Marg, Thane, Maharashtra, 400602	27AAACE8426D1ZU
15	ROCKS AND LOGS PVT. LTD.	Yogesh@rocksnlogs.com	9769081171	74, Juhu Supreme Shopping Center, Gulmohar Cross road no.09\nGulmohar Cross road no.09, JVPD Scheme, Juhu,\nMumbai\n400049 Maharashtra\nIndia	27AAACR4857K1ZZ
16	KESHAV SRUSHTI	srujanggadgil@gmail.com	9769911588	Uttan\nBhayandar (W)\nThane\n401106 Maharashtra\nIndia	27AAATK3599G1ZB
\.


--
-- Data for Name: estimate_employees; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.estimate_employees (id, estimate_id, emp_type, base_pay, hrs_per_day, pay_per_hour, total_hours, total_cost) FROM stdin;
1	1	Junior	30000.00	8.0	203.13	704.00	143003.52
2	1	Junior	10000.00	8.0	67.71	704.00	47667.84
5	3	Junior	30000.00	8.0	203.13	696.00	141378.48
6	3	Mid-Level	45000.00	8.0	304.69	696.00	212064.24
7	3	Senior	60000.00	2.0	406.25	174.00	70687.50
8	3	Junior	30000.00	8.0	203.13	696.00	141378.48
9	2	Junior	30000.00	8.0	203.13	192.00	39000.96
10	2	Junior	25000.00	6.0	169.27	144.00	24374.88
11	2	Senior	50000.00	1.0	338.54	24.00	8124.96
17	5	Junior	30000.00	5.0	203.13	3645.00	740408.85
18	5	Mid-Level	50000.00	3.0	338.54	2187.00	740386.98
19	5	Junior	30000.00	5.0	203.13	3645.00	740408.85
20	5	Junior	30000.00	5.0	203.13	3645.00	740408.85
21	5	Mid-Level	50000.00	2.0	338.54	1458.00	493591.32
22	5	Senior	100000.00	1.0	677.08	729.00	493591.32
23	6	Mid-Level	30000.00	8.0	203.13	400.00	81252.00
24	6	Junior	20000.00	4.0	135.42	200.00	27084.00
\.


--
-- Data for Name: estimates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.estimates (id, project_name, start_date, end_date, working_days, partner_pay_per_hour, partner_cost, team_cost, grand_total, project_color, status, created_by, created_at, updated_at) FROM stdin;
1	INTEROR PROJECT - SSA	2026-05-29	2026-09-29	88	600.00	844800.00	190671.36	1035471.36	#287475	draft	1	2026-05-29 04:17:16.03248	2026-05-29 04:17:16.032484
3	ADANI MOTILAL NAGAR - R1 M1 - 	2026-06-02	2026-09-30	87	545.00	1232790.00	565508.70	1798298.70	#287475	draft	1	2026-05-29 04:48:19.299933	2026-05-29 04:48:19.299935
2	ROCKS AND LOGS - FACADE DESIGN - MALPANI	2026-05-28	2026-06-30	24	550.00	198000.00	71500.80	269500.80	#287475	draft	1	2026-05-29 04:20:32.125952	2026-05-29 04:50:41.923015
5	cyber square	2026-06-16	2029-03-31	729	550.00	8419950.00	3948796.17	12368746.17	#287475	draft	1	2026-06-16 07:47:49.610039	2026-06-16 07:47:49.610044
6	CSMT - DMR Project	2026-06-23	2026-08-31	50	550.00	330000.00	108336.00	438336.00	#475569	draft	1	2026-06-23 11:37:33.212674	2026-06-23 11:37:33.212677
\.


--
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.expenses (id, title, category, amount, date, recurring, notes, added_by) FROM stdin;
\.


--
-- Data for Name: holidays; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.holidays (id, date, name) FROM stdin;
\.


--
-- Data for Name: invoice_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.invoice_items (id, invoice_id, description, hsn_sac, amount) FROM stdin;
4	3	5% ADVANCE PAYMENT	998399	90000.00
5	4	30% SUBMISSION FOR ASB-01 BUILDING	998399	180000.00
6	5	BIM Works for the month of December 2025 to March 2026	998399	75000.00
7	6	CFC Design and Consultation Fee	998399	50000.00
8	7	Task 6A: Preparation of drawings for Boulevard - GFC (100%)	998399	88000.00
9	7	Task 7A: Preparation of drawings for Gateway Park - GFC (100%)	998399	46000.00
10	7	Task 8A: Preparation of drawings for W-MAR Edges - GFC (100%)	998399	17000.00
11	7	Task 9A: Preparation of drawings For E-MAR Upto 1st Junction- GFC (100%)	998399	35000.00
12	7	Task 10: Preparation of drawings For Landside Roads GFC (100%)	998399	91000.00
14	9	Part Payment BIM Modelling Ancillary Buildings	998399	400000.00
15	10	20% Payment - Modeling and GFC drawing completion	998399	150000.00
16	11	10% Advance Payment for Cyber Square Project	998399	1200000.00
21	13	5% Billing For Next Stage	998399	270000.00
\.


--
-- Data for Name: invoices; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.invoices (id, invoice_type, invoice_number, invoice_date, place_of_supply, bill_to_name, bill_to_address, bill_to_gstin, ship_to_name, ship_to_address, ship_to_gstin, subject, subtotal, cgst, sgst, igst, total, tax_type, project_id, client_id, bank_account_id, created_by) FROM stdin;
3	tax	A0-008	2026-05-20	Maharashtra	ENGINEERING CREATIONS PUBLIC HEALTH CONSULTANCY PVT. LTD.	1st Floor, 104, Shree Sarika CHS, A K Vaidya Marg, Thane, Maharashtra, 400602	27AAACE8426D1ZU	ENGINEERING CREATIONS PUBLIC HEALTH CONSULTANCY PVT. LTD.	1st Floor, 104, Shree Sarika CHS, A K Vaidya Marg, Thane, Maharashtra, 400602	27AAACE8426D1ZU	ADANI MOTILAL NAGAR - R1 M1 - MEP BIM MODELLING	90000.00	8100.00	8100.00	0.00	106200.00	CGST_SGST	19	14	1	1
4	tax	AO-001	2026-04-06	Maharashtra	Kalpana Struct-Con	Kalpana Struct-Con Pvt. Ltd.\n1006-1008, Cyber One, Greenscape, Plot No. 4&6, Sector-30A, Vashi, Navi Mumbai - 400 703	27AAACK5108Q1Z8	Kalpana Struct-Con	Kalpana Struct-Con Pvt. Ltd.\n1006-1008, Cyber One, Greenscape, Plot No. 4&6, Sector-30A, Vashi, Navi Mumbai - 400 703	27AAACK5108Q1Z8	IIT B - ASB01 SHOP DRAWINGS	180000.00	16200.00	16200.00	0.00	212400.00	CGST_SGST	6	5	1	1
5	tax	AO-002	2026-04-06	Maharashtra	ROCKS AND LOGS PVT. LTD.	74, Juhu Supreme Shopping Center, Gulmohar Cross road no.09\nGulmohar Cross road no.09, JVPD Scheme, Juhu,\nMumbai\n400049 Maharashtra\nIndia	27AAACR4857K1ZZ	ROCKS AND LOGS PVT. LTD.	74, Juhu Supreme Shopping Center, Gulmohar Cross road no.09\nGulmohar Cross road no.09, JVPD Scheme, Juhu,\nMumbai\n400049 Maharashtra\nIndia	27AAACR4857K1ZZ	NMIAL Flooring - R&L	75000.00	6750.00	6750.00	0.00	88500.00	CGST_SGST	5	15	1	1
6	tax	AO-003	2026-04-06	Maharashtra	KESHAV SRUSHTI	Uttan\nBhayandar (W)\nThane\n401106 Maharashtra\nIndia	27AAATK3599G1ZB	KESHAV SRUSHTI	Uttan\nBhayandar (W)\nThane\n401106 Maharashtra\nIndia	27AAATK3599G1ZB	KSOP CFC	50000.00	4500.00	4500.00	0.00	59000.00	CGST_SGST	20	16	\N	1
7	tax	AO-005	2026-04-27	Maharashtra	Navi Mumbai International Airport Limited	Office of the Airport Director, Terminal – 1B,\nCSI Airport. Santacruz (E), Mumbai - 400099, Maharashtra.	27AACCN6836G1ZB	NMIAL	S17-C, New Project Office,\nNavi Mumbai International Airport,\nAmar Marg, Near Ulwe Gaothan, Bus Stop, Ulwe,\nNavi Mumbai, Raigad,\nNavi Mumbai\n410206 Maharashtra\nIndia	27AACCN6836G1ZB	Landscape Package	277000.00	24930.00	24930.00	0.00	326860.00	CGST_SGST	2	2	1	1
9	tax	AO-006	2026-04-28	Maharashtra	PK Das	PK Das & Associates - Sankalp, 5th Floor, Plot No. 1040, Off Sayani Road, Prabhadevi, Mumbai - 400025	27AEFPD08471Z5	PK Das	PK Das & Associates - Sankalp, 5th Floor, Plot No. 1040, Off Sayani Road, Prabhadevi, Mumbai - 400025	27AEFPD08471Z5	NMIAL Ancillary Building BIM Work	400000.00	36000.00	36000.00	0.00	472000.00	CGST_SGST	16	11	1	1
10	tax	AO-007	2026-05-10	Maharashtra	Viyonna LLP	VIYONAA WORLD LLP \nOffice no-401, Plot no- A-10/2 & A-11, Kamdhenu 23 West, TTC Industrial Area MIDC, Millenium Business Park Sub Post Office, Mahape, Navi Mumbai, Thane,Maharashtra, 400710	27AAXFV0821B1Z5	Viyonna LLP	VIYONAA WORLD LLP \nOffice no-401, Plot no- A-10/2 & A-11, Kamdhenu 23 West, TTC Industrial Area MIDC, Millenium Business Park Sub Post Office, Mahape, Navi Mumbai, Thane,Maharashtra, 400710	27AAXFV0821B1Z5	KHALAPUR SITE DEVELOPMENT	150000.00	13500.00	13500.00	0.00	177000.00	CGST_SGST	7	6	1	1
11	tax	AO-004	2026-04-22	Maharashtra	Greenscape	1908, Cyber One, Plot No.1908, Cyber One, Plot No. 4 and 6, Sector 30A, Vashi, Mumbai City, Maharashtra,\nMumbai\n400703 Maharashtra\nIndia	27AAUFG6027H1Z1	Greenscape	1908, Cyber One, Plot No.1908, Cyber One, Plot No. 4 and 6, Sector 30A, Vashi, Mumbai City, Maharashtra,\nMumbai\n400703 Maharashtra\nIndia	27AAUFG6027H1Z1	CYBER SQUARE PROJECT	1200000.00	108000.00	108000.00	0.00	1416000.00	CGST_SGST	13	8	1	1
13	tax	AO-009	2026-06-17	Maharashtra	Neelkanth Deep Relcon LLP	Neelkanth Deep Relcon LLP - 4th, F-408, Tower 2, Seawoods Grand Central, Plot No R-1, Sector 40, Seawoods, Navi Mumbai, Thane, Maharashtra, 400706	27AAUFN7075L1ZB	Neelkanth Deep Relcon LLP	Neelkanth Deep Relcon LLP - 4th, F-408, Tower 2, Seawoods Grand Central, Plot No R-1, Sector 40, Seawoods, Navi Mumbai, Thane, Maharashtra, 400706	27AAUFN7075L1ZB	Paradise CHS	270000.00	24300.00	24300.00	0.00	318600.00	CGST_SGST	14	9	1	1
\.


--
-- Data for Name: leave_requests; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.leave_requests (id, employee_id, start_date, end_date, reason, status, days_count, paid_days, unpaid_days) FROM stdin;
1	2	2026-05-28	2026-05-31	vacaton	approved	4	0	0
2	7	2026-05-29	2026-06-02	Vacation	pending	5	0	0
3	12	2026-05-29	2026-06-06	vaaction	pending	9	0	0
8	4	2026-06-01	2026-06-09	Planned Trip	pending	7	0	0
\.


--
-- Data for Name: project_assignments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.project_assignments (id, user_id, project_id, base_pay, hourly_rate) FROM stdin;
1	1	21	600000.00	4062.50
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.projects (id, project_number, name, location, gmap_link, year, current_stage, is_billed, client_id, partner_remuneration, employee_remuneration, project_remuneration, work_order_urls, total_assigned_hours, partner_hourly_rate, billed_amount, start_date, end_date, employee_budget, partner_budget, color, advance_amount) FROM stdin;
2	24007	Landscape Package	Navi Mumbai International Airport Pvt. Ltd. Office of the Airport Director, Terminal – 1B, CSI Airport. Santacruz (E), Mumbai - 400099, Maharashtra.	\N	2024	\N	partial	2	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#CDE7BE	0.00
3	26005	Kalyan Station	Studio Changani Consultancy Private Limited 3rd Floor, 301, Satya House, Ram Tekdi Marg, Laxman Tekadi, Opposite Dosti. Sewri, Mumbai - 400015	\N	2026	\N	partial	3	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#B8D8F8	0.00
6	26003	IIT B - ASB01 SHOP DRAWINGS	Kalpana Struct-Con Pvt. Ltd. 1006-1008, Cyber One, Greenscape, Plot No. 4&6, Sector-30A, Vashi, Navi Mumbai - 400 703	\N	2026	\N	partial	5	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#FFD8B1	0.00
7	26002	KHALAPUR SITE DEVELOPMENT	VIYONAA WORLD LLP  Office no-401, Plot no- A-10/2 & A-11, Kamdhenu 23 West, TTC Industrial Area MIDC, Millenium Business Park Sub Post Office, Mahape, Navi Mumbai, Thane,Maharashtra, 400710	\N	2026	\N	partial	6	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#FFF1B6	0.00
9	25020	IITB B26 B27	ARSH CONSULTING SERVICES - Sixth Floor,605/A, Asher 16, Road Number 16Z,Wagle Estate MIDC	\N	2025	\N	partial	7	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#D7C4F2	0.00
8	25019	AO-IITB EFFICIENCY	ARSH CONSULTING SERVICES - Sixth Floor,605/A, Asher 16, Road Number 16Z,Wagle Estate MIDC	\N	2025	\N	partial	7	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#B8D8F8	0.00
10	25021	IITB 2B	ARSH CONSULTING SERVICES - Sixth Floor,605/A, Asher 16, Road Number 16Z,Wagle Estate MIDC	\N	2025	\N	partial	7	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#E8C7E8	0.00
11	25017	IITB ASB 01	ARSH CONSULTING SERVICES - Sixth Floor,605/A, Asher 16, Road Number 16Z,Wagle Estate MIDC	\N	2025	\N	partial	7	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#E8C7E8	0.00
12	26007	IITB-Hostel 09	ARSH CONSULTING SERVICES - Sixth Floor,605/A, Asher 16, Road Number 16Z,Wagle Estate MIDC	\N	2026	\N	partial	7	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#F4C2C2	0.00
18	0000	Development	\N	\N	2026	\N	unbilled	13	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#94A3B8	0.00
19	26009	ADANI MOTILAL NAGAR - R1 M1 - MEP BIM MODELLING	MUMBAI	\N	2026	In Progress	unbilled	14	1250000.00	550000.00	1800000.00	\N	500.00	550.00	0.00	\N	\N	0.00	0.00	#7DD3FC	0.00
4	23022	Rocks & Logs Dry Cladding PTB	Dubai	\N	2023	\N	partial	15	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#E2D5C7	0.00
5	23017	NMIAL Flooring - R&L	Dubai	\N	2023	\N	unbilled	15	0.00	0.00	0.00	\N	0.00	0.00	0.00	\N	\N	0.00	0.00	#FADADD	0.00
20	25025	KSOP CFC	WADA PALGHAR	\N	2025	In Progress	unbilled	16	25000.00	25000.00	50000.00	\N	500.00	0.00	0.00	\N	\N	0.00	0.00	#C084FC	0.00
13	26006	CYBER SQUARE PROJECT	1908, Cyber One, Plot No.1908, Cyber One, Plot No. 4 and 6, Sector 30A, Vashi, Mumbai City, Maharashtra, Mumbai 400703 Maharashtra India	\N	2026	In Progress	partial	8	8000000.00	4000000.00	12000000.00	\N	12000.00	550.00	0.00	\N	\N	0.00	0.00	#FBBF24	0.00
15	25013	BOH Forecourt	Larsen and Toubro Limited - Infrastructure Vertical - Navi Mumbai International Airport Project, Near Ambuja Cement, Dapoli, Ulwe - 410206. Landmark - NMMC Head Office, CBD Belapur	\N	2025	\N	unbilled	10	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	0.00	0.00	#FADADD	0.00
21	26008	MALPANI ARYABHATTA STONE SCOPE	\N	\N	2026	In Progress	unbilled	15	132000.00	48751.20	180751.20	\N	\N	0.00	0.00	\N	\N	0.00	0.00	#FCA5A5	0.00
16	25014	NMIAL Ancillary Building BIM Work	PK Das & Associates - Sankalp, 5th Floor, Plot No. 1040, Off Sayani Road, Prabhadevi, Mumbai - 400025	\N	2025	\N	partial	11	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	0.00	0.00	#FFD8B1	0.00
17	25015	IITB ASB 02	SANDEEP SHIKRE & ASSOCIATES - 2ND FLOOR,203/204, Prabhadevi Industrial Estate, Swatantrya veer sawarkar marg, Prabhadevi, Mumbai, 400025	\N	2025	\N	partial	12	\N	\N	\N	\N	\N	500.00	0.00	\N	\N	0.00	0.00	#FFF1B6	0.00
14	25018	Paradise CHS	Neelkanth Deep Relcon LLP - 4th, F-408, Tower 2, Seawoods Grand Central, Plot No R-1, Sector 40, Seawoods, Navi Mumbai, Thane, Maharashtra, 400706	\N	2025	\N	partial	9	\N	\N	\N	\N	\N	0.00	0.00	\N	\N	0.00	0.00	#E2D5C7	0.00
22	25022	SWAMINARAYAN MANDIR KHED	KHED	\N	2025	\N	billed	\N	300000.00	100000.00	400000.00	\N	600.00	0.00	0.00	\N	\N	0.00	0.00	#B5EAD7	0.00
\.


--
-- Data for Name: reimbursements; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.reimbursements (id, employee_id, amount, reason, date, proof_url, status, month_added) FROM stdin;
4	8	251.00	site visit lunch	2026-05-28	/static/uploads/reimbursements/40408a5b-b879-491b-a956-65ce628479aa.jpeg	approved	2026-05
1	8	282.00	Late working hours	2026-05-18	/static/uploads/reimbursements/48796eb0-6bc8-4f0e-a5d9-8969b8b0cfc7.jpeg	approved	2026-05
2	7	350.00	Late working hours	2026-05-18	/static/uploads/reimbursements/e5f01fb9-0c3e-4291-8bd1-a447c8a982ec.jpeg	approved	2026-05
3	8	497.00	Late working hours food ordered	2026-05-18	/static/uploads/reimbursements/8d8276ca-c7d9-481e-9b74-6f2a69edfcfa.jpeg	approved	2026-05
5	5	409.00	Birthday	2026-05-05	/static/uploads/reimbursements/8629cc47-9fc2-44a1-880d-2423b99bc8f6.jpeg	approved	2026-05
\.


--
-- Data for Name: salary_slips; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.salary_slips (id, employee_id, month, base_salary, tds_percent, tds_amount, reimbursement_total, net_total, payout_date, status, created_at, approved_at, paid_leave_days, unpaid_leave_days, leave_deduction) FROM stdin;
1	1	2026-05	0.00	10.00	0.00	0.00	0.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
2	3	2026-05	0.00	10.00	0.00	0.00	0.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
3	6	2026-05	0.00	10.00	0.00	0.00	0.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
4	8	2026-05	0.00	10.00	0.00	1030.00	1030.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
5	9	2026-05	0.00	10.00	0.00	0.00	0.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
6	10	2026-05	0.00	10.00	0.00	0.00	0.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
7	2	2026-05	0.00	10.00	0.00	0.00	0.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
8	11	2026-05	0.00	10.00	0.00	0.00	0.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
9	5	2026-05	0.00	10.00	0.00	409.00	409.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
10	4	2026-05	0.00	10.00	0.00	0.00	0.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
12	12	2026-05	0.00	10.00	0.00	0.00	0.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
13	7	2026-04	50000.00	10.00	5000.00	0.00	45000.00	2026-05-07	approved	2026-06-02 08:20:59.934377	2026-06-02 07:25:44.832585	0.0	0.0	0.00
14	7	2026-03	50000.00	10.00	5000.00	0.00	45000.00	2026-04-07	approved	2026-06-02 08:20:59.934377	2026-06-02 07:25:44.832585	0.0	0.0	0.00
15	7	2026-02	50000.00	10.00	5000.00	0.00	45000.00	2026-03-07	approved	2026-06-02 08:20:59.934377	2026-06-02 07:25:44.832585	0.0	0.0	0.00
16	7	2026-01	50000.00	10.00	5000.00	0.00	45000.00	2026-02-07	approved	2026-06-02 08:20:59.934377	2026-06-02 07:25:44.832585	0.0	0.0	0.00
17	7	2025-12	50000.00	10.00	5000.00	0.00	45000.00	2026-01-07	approved	2026-06-02 08:20:59.934377	2026-06-02 07:25:44.832585	0.0	0.0	0.00
18	7	2025-11	50000.00	10.00	5000.00	0.00	45000.00	2025-12-05	approved	2026-06-02 08:20:59.934377	2026-06-02 07:25:44.832585	0.0	0.0	0.00
19	7	2025-10	50000.00	10.00	5000.00	0.00	45000.00	2025-11-07	approved	2026-06-02 08:20:59.934377	2026-06-02 07:25:44.832585	0.0	0.0	0.00
20	7	2025-09	50000.00	10.00	5000.00	0.00	45000.00	2025-10-07	approved	2026-06-02 08:20:59.934377	2026-06-02 07:25:44.832585	0.0	0.0	0.00
11	7	2026-05	50000.00	10.00	5000.00	350.00	45350.00	2026-06-05	approved	2026-06-02 08:12:06.548081	2026-06-02 07:25:44.832585	0.0	0.0	0.00
21	5	2026-04	25000.00	10.00	2500.00	0.00	22500.00	2026-05-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
22	5	2026-03	25000.00	10.00	2500.00	0.00	22500.00	2026-04-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
23	5	2026-02	25000.00	10.00	2500.00	0.00	22500.00	2026-03-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
24	5	2026-01	25000.00	10.00	2500.00	0.00	22500.00	2026-02-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
25	5	2025-12	25000.00	10.00	2500.00	0.00	22500.00	2026-01-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
26	5	2025-11	25000.00	10.00	2500.00	0.00	22500.00	2025-12-05	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
27	5	2025-10	25000.00	10.00	2500.00	0.00	22500.00	2025-11-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
28	5	2025-09	25000.00	10.00	2500.00	0.00	22500.00	2025-10-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
29	5	2025-08	25000.00	10.00	2500.00	0.00	22500.00	2025-09-05	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
30	4	2026-04	30000.00	10.00	3000.00	0.00	27000.00	2026-05-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
31	4	2026-03	30000.00	10.00	3000.00	0.00	27000.00	2026-04-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
32	4	2026-02	30000.00	10.00	3000.00	0.00	27000.00	2026-03-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
33	3	2026-04	25000.00	10.00	2500.00	0.00	22500.00	2026-05-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
34	3	2026-03	25000.00	10.00	2500.00	0.00	22500.00	2026-04-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
35	3	2026-02	25000.00	10.00	2500.00	0.00	22500.00	2026-03-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
36	3	2026-01	25000.00	10.00	2500.00	0.00	22500.00	2026-02-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
37	10	2026-04	30000.00	10.00	3000.00	0.00	27000.00	2026-05-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
38	10	2026-03	30000.00	10.00	3000.00	0.00	27000.00	2026-04-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
39	10	2026-02	30000.00	10.00	3000.00	0.00	27000.00	2026-03-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
40	10	2026-01	30000.00	10.00	3000.00	0.00	27000.00	2026-02-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
41	10	2025-12	30000.00	10.00	3000.00	0.00	27000.00	2026-01-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
42	11	2026-04	30000.00	10.00	3000.00	0.00	27000.00	2026-05-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
43	11	2026-03	30000.00	10.00	3000.00	0.00	27000.00	2026-04-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
44	11	2026-02	30000.00	10.00	3000.00	0.00	27000.00	2026-03-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
45	11	2026-01	30000.00	10.00	3000.00	0.00	27000.00	2026-02-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
46	11	2025-12	30000.00	10.00	3000.00	0.00	27000.00	2026-01-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
47	11	2025-11	30000.00	10.00	3000.00	0.00	27000.00	2025-12-05	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
48	11	2025-10	30000.00	10.00	3000.00	0.00	27000.00	2025-11-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
49	11	2025-09	30000.00	10.00	3000.00	0.00	27000.00	2025-10-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
50	11	2025-08	30000.00	10.00	3000.00	0.00	27000.00	2025-09-05	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
51	11	2025-07	30000.00	10.00	3000.00	0.00	27000.00	2025-08-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
52	11	2025-06	30000.00	10.00	3000.00	0.00	27000.00	2025-07-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
53	11	2025-05	30000.00	10.00	3000.00	0.00	27000.00	2025-06-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
54	9	2026-04	25000.00	10.00	2500.00	0.00	22500.00	2026-05-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
55	9	2026-03	25000.00	10.00	2500.00	0.00	22500.00	2026-04-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
56	9	2026-02	25000.00	10.00	2500.00	0.00	22500.00	2026-03-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
57	9	2026-01	25000.00	10.00	2500.00	0.00	22500.00	2026-02-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
58	6	2026-04	25000.00	10.00	2500.00	0.00	22500.00	2026-05-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
59	6	2026-03	25000.00	10.00	2500.00	0.00	22500.00	2026-04-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
60	6	2026-02	25000.00	10.00	2500.00	0.00	22500.00	2026-03-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
61	6	2026-01	25000.00	10.00	2500.00	0.00	22500.00	2026-02-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
62	6	2025-12	25000.00	10.00	2500.00	0.00	22500.00	2026-01-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
63	6	2025-11	25000.00	10.00	2500.00	0.00	22500.00	2025-12-05	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
64	6	2025-10	25000.00	10.00	2500.00	0.00	22500.00	2025-11-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
65	6	2025-09	25000.00	10.00	2500.00	0.00	22500.00	2025-10-07	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
66	6	2025-08	25000.00	10.00	2500.00	0.00	22500.00	2025-09-05	pending	2026-06-16 07:32:14.297987	\N	0.0	0.0	0.00
\.


--
-- Data for Name: settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.settings (id, company_name, company_address, company_gstin, company_phone, company_email, company_signatory_name, company_signatory_role, working_hours_per_month, salary_months_per_year, tds_percent) FROM stdin;
1	Studio MH02 LLP	201, Prathamesh Apt, Mahant Road, Vile Parle East\nMumbai, Maharashtra 400507	27AEQFS5715Q1Z1	9769911588	INFO@STUDIOMH02.COM	Srujan Gadgil	Partner	160.00	13.00	10.00
\.


--
-- Data for Name: subtasks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.subtasks (id, task_id, title, description, duration_hours, status, created_by, created_at) FROM stdin;
1	24	Strutural Revision 4 Changes	\N	16.00	pending	1	2026-06-23 11:08:14.897101
2	24	Structural Rebaring B3	\N	80.00	pending	1	2026-06-23 11:08:52.783138
3	24	Sheets for Structural B3/ Footing	\N	8.00	pending	1	2026-06-23 11:09:41.86718
4	13	Sections for Structural B3	\N	8.00	pending	1	2026-06-23 11:14:08.031698
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tasks (id, title, description, date, priority, status, project_id, assigned_to, assigned_by, duration_hours, end_date) FROM stdin;
21	CYBER SQUARE PROJECT	\N	2026-07-13	medium	pending	13	3	1	4	2026-11-30
20	CYBER SQUARE PROJECT	\N	2026-07-13	medium	pending	13	2	1	4	2026-11-30
8	ADANI MOTILAL NAGAR - R1 M1 - MEP BIM MODELLING	Electrical Model for the project	2026-06-15	high	pending	19	3	1	8	2026-07-10
9	ADANI MOTILAL NAGAR - R1 M1 - MEP BIM MODELLING	Work on HVAC and Fire Fighting Model for the project. 	2026-06-15	high	pending	19	2	1	8	2026-07-10
7	ADANI MOTILAL NAGAR - R1 M1 - MEP BIM MODELLING	Handle Project	2026-06-15	high	pending	19	6	1	6	2026-07-10
24	CYBER SQUARE PROJECT	\N	2026-06-15	medium	pending	13	7	1	4	2026-11-30
13	CYBER SQUARE PROJECT	\N	2026-06-15	medium	pending	13	4	1	8	2026-06-21
2	Rocks & Logs Dry Cladding PTB	\N	2026-05-25	medium	completed	4	7	11	7	2026-05-30
4	Landscape Package	\N	2026-05-27	medium	pending	2	5	1	8	2026-06-04
5	IITB ASB 02	\N	2026-05-28	medium	pending	17	7	1	7	\N
10	Paradise CHS	\N	2026-06-15	medium	pending	14	8	1	6	2026-09-30
11	CYBER SQUARE PROJECT	\N	2026-06-15	medium	pending	13	5	1	4	2026-11-30
16	NMIAL Flooring - R&L	\N	2026-06-15	medium	pending	5	12	1	2	2026-07-31
17	Landscape Package	\N	2026-06-18	medium	pending	2	5	1	2	2026-06-25
18	NMIAL Flooring - R&L	\N	2026-06-18	medium	pending	5	5	1	2	2026-07-11
19	Rocks & Logs Dry Cladding PTB	\N	2026-06-26	medium	pending	4	5	1	4	2026-07-31
14	Paradise CHS	\N	2026-06-15	low	in-progress	14	12	1	3	2026-07-31
15	Rocks & Logs Dry Cladding PTB	\N	2026-06-15	low	in-progress	4	12	1	3	2026-07-31
23	CYBER SQUARE PROJECT	\N	2026-07-13	medium	pending	13	9	1	4	2026-11-30
6	ADANI MOTILAL NAGAR - R1 M1 - MEP BIM MODELLING	Work on Plumbing Model for the project. 	2026-06-15	high	pending	19	9	1	8	2026-07-10
26	SWAMINARAYAN MANDIR KHED	\N	2026-06-22	medium	pending	22	4	1	7	2026-06-23
29	CYBER SQUARE PROJECT (Split)	\N	2026-06-24	medium	pending	13	4	1	7	2026-11-30
28	SWAMINARAYAN MANDIR KHED	\N	2026-06-24	medium	pending	22	4	1	1	2026-11-30
33	MALPANI ARYABHATTA STONE SCOPE	\N	2026-06-22	medium	pending	21	1	1	4	2026-09-30
\.


--
-- Data for Name: team_members; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.team_members (id, team_id, user_id) FROM stdin;
1	1	6
2	1	9
3	2	6
4	2	3
5	2	1
6	2	9
7	2	2
\.


--
-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.teams (id, project_id, name, team_lead_id, created_at) FROM stdin;
1	14	Team 1	9	2026-05-28 09:11:37.183898+00
2	19	Team 1	9	2026-05-29 04:29:46.206989+00
\.


--
-- Data for Name: timesheets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.timesheets (id, employee_id, project_id, date, hours_logged, notes) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, name, designation, joining_date, end_date, salary_month, leaves_allowed, pan_number, aadhar_number, personal_mail, studio_email, photo_url, role, is_active, hashed_password, manager_id, salary_hour, documents_url, time_tracker_login, time_tracker_password, phone_number, emergency_contact_number, emergency_contact_relationship, gender, location, bank_name, bank_account_number, paid_leave_balance, leave_accrued_through) FROM stdin;
5	Nirmayee Govind Yetayekar	Employee	2025-08-16	\N	25000.00	6	BGKPY7976E	257758085572	ynirmayee@gmail.com	nirmayee.yetayekar@studiomh02.com	\N	employee	t	$2b$12$fqWfHixUxQ8KnBGSMdbxvuNu02Aov6Vdv62W6QlAI0XwI5uh27cLq	\N	\N	\N	\N	\N	9869114854	7738174477	\N	\N	\N	\N	\N	1.5	2026-06
4	Mallika Ashish Agrawal	Employee	2026-02-01	\N	30000.00	6	EGQPA8517N	656463871571	mallika1304agrawal@gmail.com	mallika.agrawal@studiomh02.com	\N	employee	t	$2b$12$V.QZ3V0D/EBSnhflRRfqEuXyKn..bnaEls.SwQmYay1qGfpQEsS.y	\N	\N	\N	\N	\N	9922534220	9819291920	\N	\N	\N	\N	\N	1.5	2026-06
3	Harsh Dhanraj Rode	Employee	2026-01-05	\N	25000.00	12	FLDPR6074L	504935004761	harshrodework@gmail.com	harsh.rode@studiomh02.com	\N	employee	t	$2b$12$I/CgELPJd4eZ36JAt01UuuIitFzioHgLfhCl.c0NG7FGZVIxra6Ei	\N	\N	\N	\N	\N	8451935030	9372522324	\N	\N	\N	\N	\N	1.5	2026-06
2	Abhishek Jaywant Pawar	Employee	2026-05-04	\N	30000.00	12	EPLPP5639L	753751564418	apawar842k@gmail.com	abhishek.pawar@studiomh02.com	/static/uploads/photos/2_03b76511.png	employee	t	$2b$12$GvlEvdRvX70rZmPgim5.wuqi/aH5HKb9qoUe.SfgjKIyn5CfkHvoK	\N	\N	\N	\N	\N	8975446840	8830657083		\N	\N	\N	\N	1.5	2026-06
1	Srujan Gadgil	Admin	2026-06-01	\N	600000.00	18	123123123123	1234123412341234	srujangadgil@gmail.com	srujan@studiomh02.com	\N	admin	t	$2b$12$OYXYdnz3YPUsCbOjOiHUkOv6QIFH44KeCt8LlyxgNrKu3An5kdUAy	\N	\N	[]	\N	\N	\N	\N	\N	\N	\N	\N	\N	1.5	2026-06
10	Smit Santosh Pawar	Employee	2025-12-08	2026-06-04	30000.00	12	BRSPP8961R	861299591916	smitpawar2701@gmail.com	smit.pawar@studiomh02.com	\N	employee	t	$2b$12$ChOW0CwhpFS/GBx7yudww.KfMVwGfhFQ/pkESDEegHZAjqKr462qi	\N	\N	\N	\N	\N	9082868331	9870102908	\N	\N	\N	\N	\N	1.5	2026-06
12	Ruchi Ganatra	Employee	2026-06-01	\N	30000.00	18	BNFPG1794Q	687382346950	ruchi.h.ganatra@gmail.com	ruchi.ganatra@studiomh02.com	\N	employee	t	$2b$12$j7945g4GRQj6ZsP2vveHeewRVTU/qrZkXhUS0DHJOndeERbZSlX6y	1	\N	[]	\N	\N	9619235354	9819151085	Parent	F	\N	\N	\N	1.5	2026-06
11	Shriya Srujan Gadgil	Accounts	2023-06-01	\N	30000.00	18	DDVPP6432A	358434610727	patwardhanshriya02@gmail.com	accounts@studiomh02.com	\N	admin	t	$2b$12$QshYvUMewGa8iUD8Aes8zeEaaL7Ln3QgPi8mcq2A93qz/O4B3IFw6	1	\N	[{"doc_type": "aadhar", "url": "/static/uploads/documents/11_aadhar_16244130.pdf", "filename": "shriya maam aadhar card.pdf"}, {"doc_type": "pan", "url": "/static/uploads/documents/11_pan_0898efdb.pdf", "filename": "shriya maam PAN card.pdf"}]	\N	\N	9403607098	9769911588	Husband	\N	\N	\N	\N	1.5	2026-06
9	Shubham Ratan Sonawane	Employee	2026-01-12	\N	25000.00	12	KLFPS2870N	303687790191	shubhamsonawane7292@gmail.com	shubham.sonawane@studiomh02.com	\N	employee	t	$2b$12$o8aZQJPxNMb1WpCyZ6JqeOdGoJZHPDxzkoNXZZyYHAYEThKNaOmn.	\N	\N	\N	\N	\N	7507675300	9890605384	\N	\N	\N	\N	\N	1.5	2026-06
8	Samartha Vilas Kompelli	Employee	2026-12-22	\N	30000.00	12	EIXPK4425G	207124490717	samarthakofficial@gmail.com	samartha.kompelli@studiomh02.com	\N	employee	t	$2b$12$9VcNFNYIFFzW5rRcAv03yegPCGgi7HYEESmsgBj/4RNMjMh0vWIoW	\N	\N	\N	\N	\N	8082751785	9619699915	Vilas Kompelli	\N	\N	\N	\N	1.5	2026-06
7	Sagarika Rajesh Ghumekar	Employee	2025-09-01	\N	35000.00	12	CJRPG9310H	926987791635	sagarikaghumekar@gmail.com	sagarika.ghumekar@studiomh02.com	\N	employee	t	$2b$12$6.9Trt5FLl0qvvODP4ANGupWTtwapyaNvUp/.EtAIYK0leFuq4Xza	1	\N	\N	\N	\N	8779657374	8108206420	\N	\N	\N	\N	\N	1.5	2026-06
6	Roshani Ramesh Rasal	Employee	2025-08-04	\N	25000.00	12	DBWPR3685G	393604684329	roshanirasal2604@gmail.com	roshani.rasal@studiomh02.com	\N	employee	t	$2b$12$aSstHmqckP3m4tPgaZffUuLiHJs6U/GnKozflEUAj3Urheib..AZ6	\N	\N	\N	\N	\N	9145717468	9552171742	\N	\N	\N	\N	\N	1.5	2026-06
\.


--
-- Data for Name: weekly_timesheet_entries; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.weekly_timesheet_entries (id, timesheet_id, project_id, hours, description, daily_hours) FROM stdin;
17	15	2	40.00	MLCP,CTC 	\N
18	15	4	8.00	CLASH REPORT 	\N
19	16	2	32.00	MLCP,CTC sheets 	\N
20	16	4	4.00	Clash report	\N
21	16	5	4.00	Clash report	\N
22	17	2	23.00	MLCP sheets	\N
23	17	5	3.00	Clash Report 	\N
24	17	14	6.00	Schedule 	\N
25	17	13	8.00	Model - Structural 	\N
26	18	14	52.00	Paradise Schedule for Rebar, Concrete quantity and Architecture quantity	\N
27	19	11	32.00	Added supports, created sheets 	\N
28	19	13	8.00	BEP , Modeling	\N
29	20	2	4.00	MLCP P3 	\N
30	20	13	36.00	Model	\N
31	21	20	12.00	Electrical layout	\N
32	21	11	10.00	Added supports and created MEPF sheets for 9-11 floor	\N
33	21	13	18.00	BEP , Modelling	\N
34	22	14	24.00	Created schedules, Duplicated floor for Tower A , 	\N
35	22	13	24.00	continued modelling	\N
36	23	13	40.00	Continued Modelling , attended meeting for BEP and made changes in BEP 	\N
37	24	14	53.00	Architectural & structural modelling + Rebarring & concrete schedules with architecture schedules	\N
38	25	14	26.00	Rebaring schedule 	\N
39	26	14	34.50	working on rebaring and model	\N
40	27	14	41.00	worked on paradise compilation of all data and  final quantities	\N
41	28	20	16.00	Site visit with sir & preparation of SWB layout	\N
42	28	14	24.00	Rebarring schedules	\N
43	29	14	36.00	Arch & structural modelling & corrections with additions in floors to architectural + structural + Timeliner update	\N
44	30	14	40.00	Rebarring + Arch + conc. schedule compilation alongwith sagarika + Completed tower C arch & structural models updates & Updated timeliner with site visit	\N
45	31	11	16.00	1st TO 10th floor change FAD branch routine and set jet fan location and clash detection slove SSA Comments 1st to 6th floor and changes FF sprinkler location and clash detection 	\N
46	32	19	12.00	Started Modelling for T6B	\N
47	32	14	38.00	Plumbing Modelling & Quantity for MEPF 	\N
48	32	18	2.00	Learning Python 	\N
49	33	19	36.00	Modelling for T6B	\N
50	33	18	2.00	Learning Python & AI for Revit	\N
51	34	13	56.00	Modelling	\N
52	35	11	24.00	MEPF sheet, added Mechanical Support 	\N
53	35	13	16.00	Modelling	\N
54	36	13	33.00	started Column Modelling	\N
55	36	11	7.00	Added Mechanical Support, Supports for Fire equipment	\N
56	37	13	40.00	Modelling	\N
57	38	13	32.00	Modelling	\N
58	39	14	16.00	podium p6 conduiting work & model placing cctv, FAPA, ELE	\N
59	39	19	28.00	HVAC  modeling work start  	\N
62	41	19	8.00	HVAC Model correction 	\N
63	41	14	8.00	p6 conduiting work done 	\N
64	41	14	24.00	p5 conduiting  start	\N
66	43	13	20.00	Foundation slab modelling correction, Sections	[0.0, 0.0, 4.0, 8.0, 8.0, 0.0, 0.0]
67	44	14	44.00	I worked & helped in obtaining the structure, arch & rebar quantities of Paradise CHS and als0o guided new comers to get the quantities. I also visited the site for checking the quantity discrepancies.	[8.0, 15.5, 4.0, 8.0, 8.5, 0.0, 0.0]
68	44	13	4.00	I tried learning dynamo so that it can be helpful for modelling rebars with some automation.	[0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 0.0]
69	45	13	24.00	seperating the structural slabs and tagging all elements in drawings	[8.0, 8.0, 8.0, 0.0, 0.0, 0.0, 0.0]
70	45	14	16.00	training 	[0.0, 0.0, 0.0, 8.0, 8.0, 0.0, 0.0]
71	46	14	40.00	I worked on correcting the formula error in every sheet & also  some rework in conc. quantities. I also worked on rebar quantities corrections. I then finalised conc. quantities & confirmed it with engineers by visiting site. Found out that there is major rework in column quantities of typical floors all towers	[8.0, 8.0, 8.0, 8.0, 8.0, 0.0, 0.0]
72	47	5	22.00	corrections for as built drawings	[8.0, 8.0, 6.0, 0.0, 0.0, 0.0, 0.0]
73	47	14	18.00	structural plan of podium 6, structural plan of typical floor and refuge floor of tower c	[0.0, 0.0, 2.0, 8.0, 8.0, 0.0, 0.0]
74	48	6	16.00	change modeling as per new cad and clash detection	[8.0, 8.0, 0.0, 0.0, 0.0, 0.0, 0.0]
75	48	19	24.00	plumbing	[0.0, 0.0, 8.0, 8.0, 8.0, 0.0, 0.0]
76	49	19	16.00	plumbing	[8.0, 8.0, 0.0, 0.0, 0.0, 0.0, 0.0]
77	49	6	24.00	change modeling as per cad and clash detection	[0.0, 0.0, 8.0, 8.0, 8.0, 0.0, 0.0]
78	50	13	16.00	column sheet, took handover from smit	[0.0, 0.0, 0.0, 8.0, 8.0, 0.0, 0.0]
79	50	14	26.00	quantities and nwd export	[9.0, 9.0, 8.0, 0.0, 0.0, 0.0, 0.0]
80	51	6	30.00	changes as per cad ground to 2rd floor and clash resolve start 3rd floor plumbing	[8.0, 4.0, 4.0, 8.0, 6.0, 0.0, 0.0]
81	51	19	12.00	T2B / T4D complate and publish	[0.0, 4.0, 4.0, 0.0, 4.0, 0.0, 0.0]
82	52	13	40.00	FOUNDATION SHEET, AND MODEL	[8.0, 8.0, 8.0, 8.0, 8.0, 0.0, 0.0]
83	53	13	40.00	SEGREGATED ALL FILES IN FOLDER, UPLOADED ALL BASEMENT 03 SHEETS IN ONE DRIVE, REVIEWED SECTION SHARED BY RENUKA, STARTED MODELING MEP	[8.0, 8.0, 8.0, 8.0, 8.0, 0.0, 0.0]
84	54	14	21.00	Plumbing podium -06	[9.0, 12.0, 0.0, 0.0, 0.0, 0.0, 0.0]
85	54	19	24.00	Project Setup and modelling	[0.0, 0.0, 8.0, 8.0, 8.0, 0.0, 0.0]
86	55	19	40.00	T4 clash detection	[8.0, 8.0, 8.0, 8.0, 8.0, 0.0, 0.0]
87	56	19	40.00	T2 and T4D Plumbing Modelling	[8.0, 8.0, 8.0, 8.0, 8.0, 0.0, 0.0]
\.


--
-- Data for Name: weekly_timesheets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.weekly_timesheets (id, employee_id, week_start, week_end, total_hours, status, description, rejection_reason) FROM stdin;
19	4	2026-05-04	2026-05-10	40.00	approved	1. 7-8 th MEPF plan sheet with sections \n2. Added Supports for HVAC\n3. Started making BEP 	\N
15	5	2026-05-04	2026-05-10	48.00	approved	MLCP Phase 3 sheet, ctc sheets/correction and Cladding clash report 	\N
23	4	2026-05-25	2026-05-31	40.00	approved	Continued Modelling  footing , Pcc , beams , attended meeting for BEP and made changes in BEP 	\N
20	5	2026-05-25	2026-05-31	40.00	approved	1. Drainage new sheet with few Section/detail\n2. Modeled the foundation and beams for Basement 3 and 2, generated foundation and section sheets for Basement 3.	\N
27	7	2026-05-25	2026-05-31	41.00	approved	worked on paradise compilation of all data and  final quantities	\N
30	8	2026-05-25	2026-05-31	40.00	approved	Compiled the quantity schedules for rebars + arch + structural quantities. Completed tower C structural & architectural models corrections Additional floors & door window remain to be done. Created door family from scratch & updated timeliner by visiting site 	\N
31	9	2026-05-25	2026-05-31	16.00	approved	SLOVE COMMENTS AND CLASH DETECTION	\N
17	5	2026-05-18	2026-05-24	40.00	approved	1.Lighting sheet and Drainage sheet\n2. Doing work on Sheet status \n3.Schedules for material of Tower C \n4.Foundation Modelling.	\N
18	7	2026-05-18	2026-05-24	52.00	approved	This week, I worked on the Paradise CHS submission, including preparation of rebar schedules, concrete quantity calculations, and architectural quantity extraction for submission purposes. I was primarily focused on compiling, coordinating, and updating the submission data as per the latest drawings and revisions received from the client side	\N
22	4	2026-05-18	2026-05-24	48.00	approved	created Schedules for Material , continued modelling for Cyber square ,  completed columns , started with footing	\N
24	8	2026-05-18	2026-05-24	53.00	approved	All the quantities submitted except P6 and tower C arch & structural models completed.	\N
16	5	2026-05-11	2026-05-17	40.00	approved	Mlcp phase 3 Irrigation,Lighting sheets and modelling.	\N
21	4	2026-05-11	2026-05-17	40.00	approved	1.made electrical layout for wada project \n2.Added supports and created MEPF sheets for 9-11 floor\n3. made BEP , Started modelling columns	\N
25	7	2026-05-11	2026-05-17	26.00	approved	worked on paradise chs. rebaring schedule 	\N
29	8	2026-05-11	2026-05-17	36.00	approved	I corrected & improved the architectural & structural models of tower C according to the changes in new plan & updated the timeliner but the data as usual was sent on last minute with some mistakes 	\N
26	7	2026-05-04	2026-05-10	34.50	approved	Worked on paradise chs rebaring as well as model	\N
28	8	2026-05-04	2026-05-10	40.00	approved	Rebarring schedules for paradise chs & site visit & SWB for Wada project	\N
38	10	2026-06-01	2026-06-07	32.00	approved	Footing, PCC, Beams.	\N
35	10	2026-05-11	2026-05-17	40.00	approved	MEPF sheet, mechanical support and Modelling	\N
34	10	2026-05-04	2026-05-10	56.00	approved	 structure Modelling (test)	\N
36	10	2026-05-18	2026-05-24	40.00	approved	Started Column Modelling, mech support, fire equipment support	\N
37	10	2026-05-25	2026-05-31	40.00	approved	modelling for footing, PCC, Beam and attended meeting for BEP	\N
39	2	2026-06-01	2026-06-07	44.00	approved	worked on paradise CHS p6 conduiting  \nWorked on HVAC  Started from making project parameter as per client req.	\N
32	3	2026-06-01	2026-06-07	52.00	approved	WIP for Motilal Nagar 	\N
41	2	2026-06-08	2026-06-14	40.00	approved	HVAC Model correction done as per strectural model\np5 conduit work start ELE, MODEL Placed { tower A,B,C } TOWER A, \nC ele. conduit ,cctv , FAPA DONE 	\N
33	3	2026-06-08	2026-06-14	38.00	approved	WIP Motilal nagar Project	\N
43	4	2026-06-08	2026-06-14	20.00	approved	Foundation slab modelling correction, Sections	\N
53	7	2026-06-15	2026-06-21	40.00	approved	SEGREGATED ALL FILES IN FOLDER, UPLOADED ALL BASEMENT 03 SHEETS IN ONE DRIVE, REVIEWED SECTION SHARED BY RENUKA, STARTED MODELING MEP	\N
51	9	2026-06-15	2026-06-21	42.00	approved	changes as per cad ground to 2rd floor and clash resolve start 3rd floor plumbing\nT2B / T4D complate and publish	\N
46	8	2026-06-08	2026-06-14	40.00	approved	Correction of conc. & rebar quantities. Finalising conc. quantities. Site visit. Rework on rebar quantities	\N
47	12	2026-06-08	2026-06-14	40.00	approved	Done corrections and updates for Navi Mumbai airport flooring drawings and paradise CHS. Performed review, modification and coordination of project elements to improve drawing accuracy and quality.	\N
49	9	2026-06-08	2026-06-14	40.00	approved	change modeling as per cad and clash detection\nplumbing\n	\N
52	7	2026-06-08	2026-06-14	40.00	approved	FOUNDATION SHEET, AND MODEL	\N
48	9	2026-06-01	2026-06-07	40.00	approved	change modeling as per new cad and clash detection\n\nplumbing in motilal nagar	\N
50	7	2026-06-01	2026-06-07	42.00	approved	column sheet, took handover from smit	\N
45	12	2026-06-01	2026-06-07	40.00	approved	Spent additional time on training and practicing on technical skills and completed structural slab, beam separation along with tagging all elements	\N
44	8	2026-06-01	2026-06-07	48.00	approved	Working on obtaining quantities, discrepancies were found in our formula as well as the work done by new comers as they were doing it for the first time. Site visit. Dynamo learning	\N
56	6	2026-06-15	2026-06-21	40.00	approved	Complete Modelling of T2 and T4 mepf modelling	\N
55	6	2026-06-08	2026-06-14	40.00	approved	completeMEPF modelling of T4	\N
54	6	2026-06-01	2026-06-07	45.00	approved	paradise plumbing drainage for P6 done and start motilal nagar MEPF modelling	\N
\.


--
-- Name: attendance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.attendance_id_seq', 1, false);


--
-- Name: bank_accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.bank_accounts_id_seq', 1, true);


--
-- Name: clients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.clients_id_seq', 16, true);


--
-- Name: estimate_employees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.estimate_employees_id_seq', 24, true);


--
-- Name: estimates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.estimates_id_seq', 6, true);


--
-- Name: expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.expenses_id_seq', 1, true);


--
-- Name: holidays_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.holidays_id_seq', 1, false);


--
-- Name: invoice_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.invoice_items_id_seq', 21, true);


--
-- Name: invoices_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.invoices_id_seq', 13, true);


--
-- Name: leave_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.leave_requests_id_seq', 8, true);


--
-- Name: project_assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.project_assignments_id_seq', 1, true);


--
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.projects_id_seq', 22, true);


--
-- Name: reimbursements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.reimbursements_id_seq', 6, true);


--
-- Name: salary_slips_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.salary_slips_id_seq', 66, true);


--
-- Name: subtasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.subtasks_id_seq', 4, true);


--
-- Name: tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tasks_id_seq', 33, true);


--
-- Name: team_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.team_members_id_seq', 7, true);


--
-- Name: teams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.teams_id_seq', 2, true);


--
-- Name: timesheets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.timesheets_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 12, true);


--
-- Name: weekly_timesheet_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.weekly_timesheet_entries_id_seq', 87, true);


--
-- Name: weekly_timesheets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.weekly_timesheets_id_seq', 56, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: attendance attendance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance
    ADD CONSTRAINT attendance_pkey PRIMARY KEY (id);


--
-- Name: bank_accounts bank_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bank_accounts
    ADD CONSTRAINT bank_accounts_pkey PRIMARY KEY (id);


--
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- Name: estimate_employees estimate_employees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estimate_employees
    ADD CONSTRAINT estimate_employees_pkey PRIMARY KEY (id);


--
-- Name: estimates estimates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estimates
    ADD CONSTRAINT estimates_pkey PRIMARY KEY (id);


--
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- Name: holidays holidays_date_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.holidays
    ADD CONSTRAINT holidays_date_key UNIQUE (date);


--
-- Name: holidays holidays_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.holidays
    ADD CONSTRAINT holidays_pkey PRIMARY KEY (id);


--
-- Name: invoice_items invoice_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice_items
    ADD CONSTRAINT invoice_items_pkey PRIMARY KEY (id);


--
-- Name: invoices invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pkey PRIMARY KEY (id);


--
-- Name: leave_requests leave_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_requests
    ADD CONSTRAINT leave_requests_pkey PRIMARY KEY (id);


--
-- Name: project_assignments project_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_assignments
    ADD CONSTRAINT project_assignments_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: projects projects_project_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_project_number_key UNIQUE (project_number);


--
-- Name: reimbursements reimbursements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursements
    ADD CONSTRAINT reimbursements_pkey PRIMARY KEY (id);


--
-- Name: salary_slips salary_slips_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salary_slips
    ADD CONSTRAINT salary_slips_pkey PRIMARY KEY (id);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- Name: subtasks subtasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subtasks
    ADD CONSTRAINT subtasks_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: team_members team_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_pkey PRIMARY KEY (id);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: timesheets timesheets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheets
    ADD CONSTRAINT timesheets_pkey PRIMARY KEY (id);


--
-- Name: salary_slips uq_salary_slip_employee_month; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salary_slips
    ADD CONSTRAINT uq_salary_slip_employee_month UNIQUE (employee_id, month);


--
-- Name: team_members uq_team_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT uq_team_user UNIQUE (team_id, user_id);


--
-- Name: users users_personal_mail_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_personal_mail_key UNIQUE (personal_mail);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_studio_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_studio_email_key UNIQUE (studio_email);


--
-- Name: weekly_timesheet_entries weekly_timesheet_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_timesheet_entries
    ADD CONSTRAINT weekly_timesheet_entries_pkey PRIMARY KEY (id);


--
-- Name: weekly_timesheets weekly_timesheets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_timesheets
    ADD CONSTRAINT weekly_timesheets_pkey PRIMARY KEY (id);


--
-- Name: ix_team_members_team_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_team_members_team_id ON public.team_members USING btree (team_id);


--
-- Name: ix_team_members_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_team_members_user_id ON public.team_members USING btree (user_id);


--
-- Name: ix_teams_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_teams_project_id ON public.teams USING btree (project_id);


--
-- Name: ix_weekly_timesheets_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_weekly_timesheets_id ON public.weekly_timesheets USING btree (id);


--
-- Name: attendance attendance_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attendance
    ADD CONSTRAINT attendance_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.users(id);


--
-- Name: estimate_employees estimate_employees_estimate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estimate_employees
    ADD CONSTRAINT estimate_employees_estimate_id_fkey FOREIGN KEY (estimate_id) REFERENCES public.estimates(id) ON DELETE CASCADE;


--
-- Name: estimates estimates_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estimates
    ADD CONSTRAINT estimates_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: expenses expenses_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_added_by_fkey FOREIGN KEY (added_by) REFERENCES public.users(id);


--
-- Name: invoice_items invoice_items_invoice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoice_items
    ADD CONSTRAINT invoice_items_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES public.invoices(id);


--
-- Name: invoices invoices_bank_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_bank_account_id_fkey FOREIGN KEY (bank_account_id) REFERENCES public.bank_accounts(id);


--
-- Name: invoices invoices_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id);


--
-- Name: invoices invoices_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: invoices invoices_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: leave_requests leave_requests_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_requests
    ADD CONSTRAINT leave_requests_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.users(id);


--
-- Name: project_assignments project_assignments_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_assignments
    ADD CONSTRAINT project_assignments_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_assignments project_assignments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_assignments
    ADD CONSTRAINT project_assignments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: projects projects_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id);


--
-- Name: reimbursements reimbursements_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reimbursements
    ADD CONSTRAINT reimbursements_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.users(id);


--
-- Name: salary_slips salary_slips_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salary_slips
    ADD CONSTRAINT salary_slips_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.users(id);


--
-- Name: subtasks subtasks_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subtasks
    ADD CONSTRAINT subtasks_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: subtasks subtasks_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subtasks
    ADD CONSTRAINT subtasks_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: tasks tasks_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- Name: tasks tasks_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id);


--
-- Name: tasks tasks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: team_members team_members_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id) ON DELETE CASCADE;


--
-- Name: team_members team_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: teams teams_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: teams teams_team_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_team_lead_id_fkey FOREIGN KEY (team_lead_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: timesheets timesheets_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheets
    ADD CONSTRAINT timesheets_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.users(id);


--
-- Name: timesheets timesheets_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheets
    ADD CONSTRAINT timesheets_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: users users_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_manager_id_fkey FOREIGN KEY (manager_id) REFERENCES public.users(id);


--
-- Name: weekly_timesheet_entries weekly_timesheet_entries_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_timesheet_entries
    ADD CONSTRAINT weekly_timesheet_entries_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: weekly_timesheet_entries weekly_timesheet_entries_timesheet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_timesheet_entries
    ADD CONSTRAINT weekly_timesheet_entries_timesheet_id_fkey FOREIGN KEY (timesheet_id) REFERENCES public.weekly_timesheets(id) ON DELETE CASCADE;


--
-- Name: weekly_timesheets weekly_timesheets_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_timesheets
    ADD CONSTRAINT weekly_timesheets_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict dxS8nbJ2rhubT4jrjMOiyCWmDjWTo2BcVhGvsZ0Hssujn9H7aNJZTIhZ48Cj8mg

