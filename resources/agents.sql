--
-- PostgreSQL database dump
--

-- Dumped from database version 12.5 (Ubuntu 12.5-0ubuntu0.20.04.1)
-- Dumped by pg_dump version 12.5 (Ubuntu 12.5-0ubuntu0.20.04.1)

-- Started on 2021-02-20 17:13:15 MSK

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
-- TOC entry 3010 (class 0 OID 16385)
-- Dependencies: 202
-- Data for Name: agents; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.agents (id, side, name) VALUES (1, 'ct', 'Special Agent Ava | FBI');
INSERT INTO public.agents (id, side, name) VALUES (2, 'ct', 'Lt. Commander Ricksaw | NSWC SEAL');
INSERT INTO public.agents (id, side, name) VALUES (3, 'ct', 'B Squadron Officer | SAS');
INSERT INTO public.agents (id, side, name) VALUES (4, 'ct', 'Operator | FBI SWAT');
INSERT INTO public.agents (id, side, name) VALUES (5, 'ct', 'Seal Team 6 Soldier | NSWC SEAL');
INSERT INTO public.agents (id, side, name) VALUES (6, 'ct', '''Two Times'' McCoy | USAF TACP');
INSERT INTO public.agents (id, side, name) VALUES (8, 'ct', '3rd Commando Company | KSK');
INSERT INTO public.agents (id, side, name) VALUES (9, 'ct', 'Buckshot | NSWC SEAL');
INSERT INTO public.agents (id, side, name) VALUES (10, 'ct', 'Markus Delrow | FBI HRT');
INSERT INTO public.agents (id, side, name) VALUES (11, 't', 'Enforcer | Phoenix');
INSERT INTO public.agents (id, side, name) VALUES (12, 't', 'Osiris | Elite Crew');
INSERT INTO public.agents (id, side, name) VALUES (13, 't', 'Dragomir | Sabre');
INSERT INTO public.agents (id, side, name) VALUES (14, 't', 'Maximus | Sabre');
INSERT INTO public.agents (id, side, name) VALUES (16, 't', 'Prof. Shahmat | Elite Crew');
INSERT INTO public.agents (id, side, name) VALUES (17, 't', 'Rezan The Ready | Sabre');
INSERT INTO public.agents (id, side, name) VALUES (18, 't', 'Blackwolf | Sabre');
INSERT INTO public.agents (id, side, name) VALUES (19, 't', 'The Elite Mr. Muhlik | Elite Crew');
INSERT INTO public.agents (id, side, name) VALUES (20, 't', '''The Doctor'' Romanov | Sabre');
INSERT INTO public.agents (id, side, name) VALUES (21, 't', 'Slingshot | Phoenix');
INSERT INTO public.agents (id, side, name) VALUES (22, 't', 'Soldier | Phoenix');
INSERT INTO public.agents (id, side, name) VALUES (7, 'ct', 'Michael Syfers  | FBI Sniper');
INSERT INTO public.agents (id, side, name) VALUES (15, 't', 'Ground Rebel  | Elite Crew');
INSERT INTO public.agents (id, side, name) VALUES (23, 't', 'Sir Bloody Loudmouth Darryl | The Professionals');
INSERT INTO public.agents (id, side, name) VALUES (24, 't', 'Sir Bloody Miami Darryl | The Professionals');
INSERT INTO public.agents (id, side, name) VALUES (25, 'ct', 'Cmdr. Mae ''Dead Cold'' Jamison | SWAT');
INSERT INTO public.agents (id, side, name) VALUES (26, 't', 'Sir Bloody Skullhead Darryl | The Professionals');
INSERT INTO public.agents (id, side, name) VALUES (27, 't', 'Sir Bloody Darryl Royale | The Professionals');
INSERT INTO public.agents (id, side, name) VALUES (28, 't', 'Sir Bloody Silent Darryl | The Professionals');
INSERT INTO public.agents (id, side, name) VALUES (29, 't', 'Number K | The Professionals');
INSERT INTO public.agents (id, side, name) VALUES (30, 't', 'Safecracker Voltzmann | The Professionals');
INSERT INTO public.agents (id, side, name) VALUES (31, 'ct', '1st Lieutenant Farlow | SWAT');
INSERT INTO public.agents (id, side, name) VALUES (32, 't', 'Rezan the Redshirt | Sabre');
INSERT INTO public.agents (id, side, name) VALUES (33, 'ct', '''Two Times'' McCoy | TACP Cavalry');
INSERT INTO public.agents (id, side, name) VALUES (34, 't', 'Getaway Sally | The Professionals');
INSERT INTO public.agents (id, side, name) VALUES (35, 't', 'Little Kev | The Professionals');
INSERT INTO public.agents (id, side, name) VALUES (36, 'ct', 'John ''Van Healen'' Kask | SWAT');
INSERT INTO public.agents (id, side, name) VALUES (37, 'ct', 'Sergeant Bombson | SWAT');
INSERT INTO public.agents (id, side, name) VALUES (38, 'ct', '''Blueberries'' Buckshot | NSWC SEAL');
INSERT INTO public.agents (id, side, name) VALUES (39, 'ct', 'Chem-Haz Specialist | SWAT');
INSERT INTO public.agents (id, side, name) VALUES (40, 'ct', 'Bio-Haz Specialist | SWAT');
INSERT INTO public.agents (id, side, name) VALUES (41, 't', 'Street Soldier | Phoenix');
INSERT INTO public.agents (id, side, name) VALUES (42, 't', 'Dragomir | Sabre Footsoldier');


--
-- TOC entry 3017 (class 0 OID 0)
-- Dependencies: 203
-- Name: agents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.agents_id_seq', 42, true);


-- Completed on 2021-02-20 17:13:15 MSK

--
-- PostgreSQL database dump complete
--

