--
-- PostgreSQL database dump
--

-- Dumped from database version 12.5
-- Dumped by pg_dump version 13.1

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

--
-- Name: task_instance_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.task_instance_status AS ENUM (
    'inactive',
    'running',
    'success',
    'fail'
);


ALTER TYPE public.task_instance_status OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: dbs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dbs (
    name text,
    connect_str text,
    secret text,
    driver text
);


ALTER TABLE public.dbs OWNER TO postgres;

--
-- Name: email_responses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.email_responses (
    id integer NOT NULL,
    name character varying,
    body text
);


ALTER TABLE public.email_responses OWNER TO postgres;

--
-- Name: email_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.email_responses_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.email_responses_id_seq OWNER TO postgres;

--
-- Name: email_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.email_responses_id_seq OWNED BY public.email_responses.id;


--
-- Name: task; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.task (
    id integer NOT NULL,
    job_type character varying NOT NULL,
    name character varying,
    executor_class character varying,
    execution_time character varying,
    active boolean,
    created_on timestamp without time zone,
    team character varying,
    team_contact character varying,
    description text,
    data_source character varying,
    timeout integer,
    queue_name character varying
);


ALTER TABLE public.task OWNER TO postgres;

--
-- Name: COLUMN task.job_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task.job_type IS 'Required: `access` (records request) or `deletion`';


--
-- Name: COLUMN task.name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task.name IS 'The name of the task as it will appear in the display list';


--
-- Name: COLUMN task.executor_class; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task.executor_class IS 'The name of the code class that will be executed by the scheduler; used to construct execution path';


--
-- Name: COLUMN task.execution_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task.execution_time IS 'Optional: A time of day (UTC) when the task can be sent to the queue - %H:%M:%S, e.g. 00:04:00';


--
-- Name: COLUMN task.active; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task.active IS 'Available to be executed by the runner?';


--
-- Name: COLUMN task.created_on; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task.created_on IS 'The date the task is created in the database';


--
-- Name: COLUMN task.team; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task.team IS 'The team within the Vox/NYM organization responsible for the data source that this task interacts with';


--
-- Name: COLUMN task.team_contact; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task.team_contact IS 'A specific responsible developer or community contact, email address or Slack channel';


--
-- Name: COLUMN task.description; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task.description IS 'A brief description of what this job does (may appear in the display list)';


--
-- Name: COLUMN task.data_source; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task.data_source IS 'Optional: The data source that this task interacts with';


--
-- Name: task_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.task_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.task_id_seq OWNER TO postgres;

--
-- Name: task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.task_id_seq OWNED BY public.task.id;


--
-- Name: task_instance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.task_instance (
    id integer NOT NULL,
    task_id integer,
    request_id integer,
    approved_by character varying NOT NULL,
    state character varying NOT NULL,
    message text,
    start_date timestamp without time zone,
    end_date timestamp without time zone,
    duration double precision,
    created_at timestamp without time zone,
    cost double precision
);


ALTER TABLE public.task_instance OWNER TO postgres;

--
-- Name: COLUMN task_instance.task_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task_instance.task_id IS 'Refers to `task` table';


--
-- Name: COLUMN task_instance.request_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task_instance.request_id IS 'Refers to `user_request` table';


--
-- Name: COLUMN task_instance.approved_by; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task_instance.approved_by IS 'Community team member who approves/runs the task';


--
-- Name: COLUMN task_instance.state; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task_instance.state IS 'Required: `inactive` (default), `running`, `success`, `fail`';


--
-- Name: COLUMN task_instance.message; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task_instance.message IS 'Optional error message if the task instance is in a failed state';


--
-- Name: COLUMN task_instance.start_date; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task_instance.start_date IS 'Date the task instance is executed';


--
-- Name: COLUMN task_instance.end_date; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task_instance.end_date IS 'Date the task instance is completed';


--
-- Name: COLUMN task_instance.duration; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.task_instance.duration IS 'Optional, duration of the task run';


--
-- Name: task_instance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.task_instance_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.task_instance_id_seq OWNER TO postgres;

--
-- Name: task_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.task_instance_id_seq OWNED BY public.task_instance.id;


--
-- Name: user_request; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_request (
    id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    email character varying NOT NULL,
    request_type character varying NOT NULL,
    request_meta jsonb,
    chorus_user_id character varying,
    chorus_username character varying,
    chorus_author boolean,
    chorus_community character varying,
    notes text,
    deadline_date timestamp without time zone,
    complete_date timestamp without time zone,
    request_date timestamp without time zone
);


ALTER TABLE public.user_request OWNER TO postgres;

--
-- Name: COLUMN user_request.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.created_at IS 'The date the initial request is received';


--
-- Name: COLUMN user_request.email; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.email IS 'Required: user email address, part of the request payload';


--
-- Name: COLUMN user_request.request_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.request_type IS 'Required: GDPR or CCPA (with additional types TBD) - this will be a distinct field in the request payload';


--
-- Name: COLUMN user_request.request_meta; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.request_meta IS 'JSON representation of the request payload until we get a better idea of the shape of the data';


--
-- Name: COLUMN user_request.chorus_user_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.chorus_user_id IS 'Optional addl user data needed to complete most requests, populated by a secondary task';


--
-- Name: COLUMN user_request.chorus_username; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.chorus_username IS 'Optional addl user data needed to complete most requests, populated by a secondary task';


--
-- Name: COLUMN user_request.chorus_author; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.chorus_author IS 'Optional addl data needed to complete most requests, populated by a secondary task';


--
-- Name: COLUMN user_request.chorus_community; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.chorus_community IS 'Optional addl data needed to complete most requests, populated by a secondary task';


--
-- Name: COLUMN user_request.notes; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.notes IS 'Comments from the Community team';


--
-- Name: COLUMN user_request.deadline_date; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.deadline_date IS 'The date by which the request must be completed (usually 30 or 45 days from the confirmation_date)';


--
-- Name: COLUMN user_request.complete_date; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_request.complete_date IS 'The date on which the request is completed (all tasks have been executed successfully and the user notified)';


--
-- Name: user_request_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_request_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_request_id_seq OWNER TO postgres;

--
-- Name: user_request_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_request_id_seq OWNED BY public.user_request.id;


--
-- Name: email_responses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_responses ALTER COLUMN id SET DEFAULT nextval('public.email_responses_id_seq'::regclass);


--
-- Name: task id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task ALTER COLUMN id SET DEFAULT nextval('public.task_id_seq'::regclass);


--
-- Name: task_instance id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_instance ALTER COLUMN id SET DEFAULT nextval('public.task_instance_id_seq'::regclass);


--
-- Name: user_request id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_request ALTER COLUMN id SET DEFAULT nextval('public.user_request_id_seq'::regclass);

--
-- Data for Name: email_responses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.email_responses (id, name, body) FROM stdin;
1	Fallback data privacy autoreply	Thank you for getting in touch. Please review the message below for details on next steps for your request.
2	Data deletion requests	Please note that all data deletion requests must be submitted via our contact form.
3	Chorus account deletion and data records requests	\nIf you are requesting access to your data records, or to have your Chorus account deleted, please reply to this email and confirm your request in the next 7 days.\n\nIf we do not receive confirmation, we will consider your request unverified and you will need to submit a new request.\n\nOnce you confirm, your request will be shared with the appropriate teams for review and processing across all Vox Media properties within 45 days of your initial message and notify you as we have updates.
4	All other requests	All other requests will be reviewed and responded to as soon as we’re able.
5	Account deletion autoreply	Hi there,\n\nIf you’re requesting that your Chorus account be deleted, please reply to this email and confirm your request.\n\nOnce your data is deleted, you will no longer be able to access your Chorus account or profile, and any content associated with the account will be deleted. This deletion applies to all Vox Media properties and is permanent and irreversible.
6	Data deletion autoreply	Hi there,\n\nIf you’re requesting your data be deleted, please reply to this email and confirm your request.\n\nOnce your data is deleted, you will no longer be able to access or use any previously held accounts or profiles, or the information held therein. This deletion applies to all Vox Media properties and is permanent and irreversible.
7	Records request autoreply	Hi there,\n\nIf you’re requesting your personal info, please reply to this email and confirm your request in the next 7 days.\n\nIf we do not receive confirmation, we will consider your request unverified and you will need to submit a new request.\n\nOnce you confirm, your request will be shared with the appropriate teams for review and processing. We will provide you with a machine readable data record from all Vox Media properties within 45 days of your initial message and notify you as we have updates.
8	Request confirmed	Thank you for confirming your request. Your request has been shared with the appropriate teams for review and processing. We will notify you as we have updates.
9	Customer request confirmed	Thanks for sending this over. This request has been shared with the appropriate teams for review and processing. We will notify you as we have updates.
10	Cannot process request - data deletion	Hi there,\n\nOur team has reviewed your request and has not found any information connected to the email address you’ve contacted from.\n\nAs such, we are not able to find any personally identifiable information to delete.\n\nIf you believe that this conclusion is an error, you are welcome to contact us from another email address you believe may be in our records. If you know that you have a Chorus account, we encourage you to add or update the email address on your account—we have details on how to do that on our help center.
11	Cannot process request - Chorus account deletion	Hi there,\n\nOur team has reviewed your request and did not find a Chorus account connected to the email address you’ve contacted from. As such, we are not able to delete your account.\n\nIf you believe that this conclusion is an error, you are welcome to contact us from another email address you believe may be in our records. If you know that you have a Chorus account, we encourage you to add or update the email address on your account—we have details on how to do that on our help center.
12	Cannot process request - data record	Hi there,\n\nOur team has reviewed your request and has not found any information connected to the email address you’ve contacted from.\n\nAs such, we have no data to provide you with.\n\nIf you believe that this conclusion is an error, you are welcome to contact us from another email address you believe may be in our records. If you know that you have a Chorus account, we encourage you to add or update the email address on your account—we have details on how to do that on our help center.
13	Cannot process request—Customer	Hi there,\n\nWe didn’t find any Chorus data associated with this user, so this request is complete from the Chorus side of things.
14	Data deletion complete	Hi there,\n\nThanks for your patience while our team has been reviewing your request. We have completed processing your request and deleted all records associated with this email address.
15	Customer data deletion complete	Hi there,\n\nWe’ve deleted all Chorus-related data associated with this user, so this request is complete on our end now.
16	Chorus account deletion complete	Hi there,\n\nThanks for your patience while our team has been reviewing your request. We have completed processing your request and deleted the Chorus account associated with this email address.
17	Customer Chorus account deletion complete	Hi there,\n\nWe’ve deleted the Chorus account for this user, so this request is complete on our end now.
18	Data record request complete	Hi there,\n\nThanks for your patience while our team has been reviewing your request. We have completed processing your request and have attached a file with all records associated with this email address.
19	Customer data record request complete	Hi there,\n\nWe’ve completed processing this request and have attached a file with all Chorus records associated with this email address.
\.


--
-- Data for Name: task; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.task (id, job_type, name, executor_class, execution_time, active, created_on, team, team_contact, description, data_source, timeout, queue_name) FROM stdin;
12	delete	Chorus Entries User Deletion	EntriesNullTask	\N	t	2020-11-19 16:49:10	Data Engineering	Barbara Shaurette	Nullify  the `user_id` value without deleting the entry row; from the chorus_db.entries import in Maestro/vox-data-lake	\N	240	\N
13	delete	Twitter Owner Nullify	OwnerNullTask	\N	t	2020-12-09 00:43:35	Data Engineering	Barbara Shaurette	Nullify the `owner_id` value without deleting the row; from the chorus_db.tweets import in Maestro/vox-data-lake	\N	120	\N
4	delete	GA UI Deletion	GADeletionTask	\N	t	\N	\N	Barbara Shaurette	Deletion of Chorus ID from the GA UI	\N	900	\N
3	delete	Phonograph Delete	PhonographDeleteTask	\N	t	2020-10-13 00:00:00	Data Engineering	Barbara Shaurette	This task deletes user information from Phonograph tables stored in BigQuery	https://console.cloud.google.com/bigquery?project=voxmedia-phonograph&p=voxmedia-phonograph&d=phonograph_events_prod	10000	\N
1	delete	Test Task Delete	TestTask	\N	f	2020-09-21 16:13:31	Data Engineering	Barbara Shaurette	Returns a count of words on a page	\N	\N	\N
10	extract	Test Task Extract	TestAccessTask	\N	f	2020-11-06 22:26:20			edited	\N	120	\N
14	delete	Test Task Scheduled Delete	TestTaskScheduled	00:04:00	f	2021-02-24 16:49:10	\N	\N	Returns a count of words on a page	\N	\N	\N
2	extract	Phonograph Extract	PhonographExtractTask	\N	t	2020-09-21 16:13:31	Data Engineering	Barbara Shaurette	This task retrieves user information from Phonograph tables stored in BigQuery	chorus db	12000	\N
\.


--
-- Name: email_responses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.email_responses_id_seq', 19, true);


--
-- Name: task_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.task_id_seq', 14, true);


--
-- Name: task_instance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.task_instance_id_seq', 595, true);


--
-- Name: user_request_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_request_id_seq', 349, true);


--
-- Name: email_responses responses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_responses
    ADD CONSTRAINT responses_pkey PRIMARY KEY (id);


--
-- Name: task_instance task_instance_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_instance
    ADD CONSTRAINT task_instance_pkey PRIMARY KEY (id);


--
-- Name: task task_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (id);


--
-- Name: task unique_name; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT unique_name UNIQUE (name);


--
-- Name: user_request unique_request; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_request
    ADD CONSTRAINT unique_request UNIQUE (email, request_type);


--
-- Name: task_instance unique_task_request; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_instance
    ADD CONSTRAINT unique_task_request UNIQUE (task_id, request_id);


--
-- Name: user_request user_request_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_request
    ADD CONSTRAINT user_request_pkey PRIMARY KEY (id);


--
-- Name: unique_executor_class; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX unique_executor_class ON public.task USING btree (executor_class);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM rdsadmin;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

