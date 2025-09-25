USE activeloop;

-- ------------------------------
-- Users (1 super admin + participants)
-- super.admin@platform.org	Super123!
-- alice.wong@gmail.com	Alice123!
-- bob.jones@outlook.com	Bob123!
-- carol.smith@yahoo.com	Carol123!
-- dave.brown@xtra.co.nz	Dave123!
-- emma.taylor@gmail.com	Emma123!
-- frank.wilson@runclub.org	Frank123!
-- grace.johnson@gmail.com	Grace123!
-- harry.lee@outlook.com	Harry123!
-- irene.martin@yahoo.com	Irene123!
-- jack.white@xtra.co.nz	Jack123!
-- violet.kumar@lincoln.ac.nz	Violet123!
-- vincent.anderson@gmail.com	Vincent123!
-- vladimir.scott@runclub.org	Vladimir123!
-- valentina.green@gmail.com	Valentina123!

-- ------------------------------
INSERT INTO Users (email, password_hash, first_name, last_name, town, global_role, status) VALUES
('super.admin@platform.org', '$2a$12$MJ1uykG7aegnqalX4IYmYOpuBsv3Z62g2eZyb6djTa4I0r7kQ8dV.', 'Super', 'Admin', 'Christchurch', 'super_admin', 'active'),
('alice.wong@gmail.com', '$2b$12$6nK5TrF/e0ItqIj4gfvr8u3bRc0EnNBCDPrCb3RZ0N3WeMM66PnJ2', 'Alice', 'Wong', 'Christchurch', 'participant', 'active'),
('bob.jones@outlook.com', '$2b$12$rXr.7YWS7v3UWdVt23djuu5OuSBOzPVVZ1f35xhbpDaLNsw8u9SwO', 'Bob', 'Jones', 'Wellington', 'participant', 'active'),
('carol.smith@yahoo.com', '$2b$12$7CUP0m4wnmZQMowRwOXqmuWHvOYal/csTzfZ83ACu6ZasyxeAeqGe', 'Carol', 'Smith', 'Auckland', 'participant', 'active'),
('dave.brown@xtra.co.nz', '$2b$12$K4cqIZQUes39Cl8kK9DP4eVOgP1qMEQNAFLVX/8odG8f6Meb8tnta', 'Dave', 'Brown', 'Dunedin', 'participant', 'active'),
('emma.taylor@gmail.com', '$2b$12$KILmHs90ksFzgKx1ImkfC.GG81zhBwFzGLz0I8Uv26y6AQ8Jd1ebO', 'Emma', 'Taylor', 'Hamilton', 'participant', 'active'),
('frank.wilson@runclub.org', '$2b$12$TD.dSSVR7fBDcmRJOc6oPeytAISuiCxznOXddgxz/LwwHWneRoxNa', 'Frank', 'Wilson', 'Napier', 'participant', 'active'),
('grace.johnson@gmail.com', '$2b$12$5/yaUQR50jHJnbNsSCkKzOvDNVyb3cBz3r3wwewARSNe2f7Tp6bQm', 'Grace', 'Johnson', 'Queenstown', 'participant', 'active'),
('harry.lee@outlook.com', '$2b$12$/bniUKEWogvboR37pK9o/e68HnNWdsdWAexplfXKaJrBYom3tf/Ii', 'Harry', 'Lee', 'Nelson', 'participant', 'active'),
('irene.martin@yahoo.com', '$2b$12$T3Ei39UaHvUyBAKX2r/Nj.Jyw8Mwwmda6ePzoDUz9ybUAR/3vJ5kK', 'Irene', 'Martin', 'Rotorua', 'participant', 'active'),
('jack.white@xtra.co.nz', '$2b$12$r7F.kNhiIXwgd8anMNHIWeGniwK5Yg2IkdhS80BzOP46KsNDf6Mri', 'Jack', 'White', 'Palmerston North', 'participant', 'active'),
('violet.kumar@lincoln.ac.nz', '$2b$12$fZ4/aA9xbBKgvmwnyLK6tuOj.OruGE3VuKnfIq.mCy8z8VGOiGHqK', 'Violet', 'Kumar', 'Auckland', 'participant', 'active'),
('vincent.anderson@gmail.com', '$2b$12$tB2NJ2ffcQsoGOpcPMQAm.W/ZZ9Jst1yGfD6QlWAzVpEh6Dj8f5Im', 'Vincent', 'Anderson', 'Dunedin', 'participant', 'active'),
('vladimir.scott@runclub.org', '$2b$12$9SiyYX4tvwjX9sbFAb1Y7.mwFiyrG1eRlx/Ms7CrdKgdjnsfqyKbm', 'Vladimir', 'Scott', 'Rotorua', 'participant', 'active'),
('valentina.green@gmail.com', '$2b$12$KyC5ouMLtuaSyqyOt5cnAuoveLpRAf/xul6cDJoUwDvGwDMcduzKm', 'Valentina', 'Green', 'Palmerston North', 'participant', 'active');


-- ------------------------------
-- Seed Groups 
-- ------------------------------
INSERT INTO Community_Groups (name, description, town, visibility, status, created_by) VALUES
('Darfield Forest Cycling Group', 'Weekly forest and gravel rides around Darfield area.', 'Christchurch', 'public', 'active', 1),
('Harbour Runners Wellington', 'Inclusive running group focusing on 5k to half-marathon training.', 'Wellington', 'public', 'active', 1),
('Auckland Trail Explorers', 'Trail running & hiking exploration in Auckland region.', 'Auckland', 'public', 'active', 1),
('Rotorua Adventure Club', 'Mixed cycling and trail events in the Redwoods.', 'Rotorua', 'private', 'active', 1);

-- ------------------------------
-- Group Memberships (Managers & Members)
-- ------------------------------
-- 1 = Darfield, 2 = Harbour Runners, 3 = Auckland Trail, 4 = Rotorua Adventure
-- Group Managers (user_id): 2=Alice, 3=Bob, 12=Violet, 10=Irene
INSERT INTO Group_Memberships (group_id, user_id, group_role, member_status) VALUES
(1, 2, 'manager', 'active'), -- Alice (2) manager Darfield
(1, 3, 'member', 'active'), -- Bob (3) member Darfield
(1, 4, 'member', 'active'), -- Carol (4) member Darfield
(1, 11, 'member', 'active'), -- Jack (11) member Darfield
(1, 5, 'member', 'active'), -- Dave (5) member Darfield 

(2, 3, 'manager', 'active'), -- Bob (3) manager Harbour Runners
(2, 2, 'member', 'active'), -- Alice (2) member Harbour Runners
(2, 5, 'member', 'active'), -- Dave (5) member Harbour Runners
(2, 7, 'member', 'active'), -- Frank (7) member Harbour Runners 

(3, 12, 'manager', 'active'), -- Violet (12) manager Auckland Trail Explorers
(3, 4, 'member', 'active'), -- Carol (4) member Trail Explorers
(3, 6, 'member', 'active'), -- Emma (6) member Trail Explorers
(3, 15, 'member', 'active'), -- Valentina (15) member Trail Explorers 

(4, 10, 'manager', 'active'), -- Irene (10) manager Rotorua Adventure
(4, 14, 'member', 'active'), -- Vladimir (14) member Rotorua Adventure
(4, 9, 'member', 'active'); -- Harry (9) member Rotorua Adventure 


-- ------------------------------
-- Group Applications 
-- ------------------------------
INSERT INTO Group_Applications (applicant_id, proposed_name, proposed_description, proposed_town, visibility, status, decision_by)
VALUES
(5, 'Hamilton Fitness Collective', 'Local mixed-discipline fitness and running events.', 'Hamilton', 'public', 'pending', NULL),
(7, 'Napier Coastal Walkers', 'Social coastal walking group.', 'Napier', 'public', 'approved', 1),
(8, 'Queenstown Mountain Riders', 'Mountain terrain cycling crew.', 'Queenstown', 'private', 'rejected', 1);


-- ------------------------------
-- Volunteer Tasks catalogue 
-- ------------------------------
INSERT INTO Volunteer_Tasks (name, description) VALUES
('Event Coordinator', 'Oversees the entire event, ensures safety, resolves issues'),
('Registration Assistant', 'Welcomes and checks in participants'),
('Course Marshal', 'Guides participants along the course'),
('Timekeeper', 'Records finish/start times'),
('Results Recorder', 'Enters participant timing data'),
('Route Setup Crew', 'Sets up course signage and markers'),
('Pack-down Crew', 'Clears course and stores equipment'),
('Tail Walker/Cyclist', 'Ensures last participant safely returns'),
('Photographer', 'Captures event media'),
('First Timers Host', 'Welcomes and briefs new participants'),
('Safety & First Aid', 'Provides basic first aid support'),
('Volunteer Coordinator', 'Coordinates and briefs volunteers'),
('Bike Marshal', 'Monitors cycling route safety');


-- ------------------------------
-- Events 
-- ------------------------------
INSERT INTO Events (group_id, datetime, town, name, event_type, description, max_participants, visibility, created_by) VALUES
(1, '2025-09-15 07:30:00', 'Christchurch', 'Avon River Fun Run', '5km Run', 'A scenic 5km loop along the Avon River for all ages.', 50, 'public', 2), -- 1: UPCOMING (Sept 15)
(2, '2025-09-15 08:00:00', 'Wellington', 'Harbour Walk Challenge', '10km Walk', 'Coastal 10km walk with harbour views.', 80, 'public', 3), -- 2: UPCOMING (Sept 15)
(3, '2025-09-21 07:00:00', 'Auckland', 'City Park Trail Intro', 'Trail 5km', 'Introductory trail around city park tracks.', 60, 'public', 12), -- 3: UPCOMING (Sept 21)
(1, '2025-09-28 07:30:00', 'Dunedin', 'Otago Peninsula Ride', 'Cycling 20km', 'Friendly 20km cycle around peninsula.', 120, 'public', 2), -- 4: UPCOMING
(2, '2025-10-05 09:00:00', 'Hamilton', 'Lake Run Festival', '10km Run', 'Flat 10km circuit around Lake Rotoroa.', 150, 'public', 3), -- 5: UPCOMING
(3, '2025-10-12 08:30:00', 'Napier', 'Hawke’s Bay Sunrise Walk', '5km Walk', 'Early morning coastal walk.', 90, 'public', 12), -- 6: UPCOMING
(4, '2025-10-19 07:45:00', 'Rotorua', 'Redwoods Forest Ride', 'Trail Ride 15km', 'Ride through Whakarewarewa Forest.', 70, 'private', 10), -- 7: UPCOMING
(2, '2025-06-15 08:00:00', 'Wellington', 'Capital City Marathon', '10km Run', 'Annual Wellington 10km run.', 200, 'public', 3), -- 8: PAST
(3, '2025-07-20 07:30:00', 'Auckland', 'Auckland Harbour Bridge Fun Run', '5km Run', 'Iconic bridge run.', 250, 'public', 12), -- 9: PAST
(1, '2025-08-10 08:30:00', 'Christchurch', 'Garden City Cycling Challenge', 'Cycling 15km', 'Scenic 15km cycle event.', 180, 'public', 2); -- 10: PAST


-- ------------------------------
-- Event Task Vacancies 
-- ------------------------------
INSERT INTO Event_Task_Vacancies (event_id, task_id, spots) VALUES
(1, 1, 1), (1, 3, 3), (1, 6, 2), (1, 7, 2), 
(2, 2, 3), (2, 3, 5), (2, 8, 1), (2, 10, 2), 
(3, 1, 1), (3, 2, 2), (3, 9, 1), (3, 12, 1), 
(8, 1, 1), (8, 2, 3), (8, 3, 4), (8, 4, 2), (8, 5, 2), (8, 11, 2),
(9, 1, 1), (9, 2, 2), (9, 6, 2), (9, 8, 1), (9, 9, 1), (9, 10, 2), (9, 12, 1),
(10, 1, 1), (10, 2, 2), (10, 13, 2), (10, 6, 1), (10, 7, 1), (10, 4, 1);


-- ------------------------------
-- Event Task Assignments (Volunteers)
-- ------------------------------
INSERT INTO Event_Task_Assignments (event_id, task_id, user_id) VALUES
-- Assignments for UPCOMING Event 1 (Avon River Fun Run)
(1, 1, 2), -- Alice (2) Event Coordinator
(1, 3, 5), -- Dave (5) Course Marshal

-- Assignments for UPCOMING Event 2 (Harbour Walk Challenge)
(2, 2, 7),-- Frank (7) Registration Assistant
(2, 3, 2), -- Alice (2) Course Marshal (Member of Group 2)

-- Assignments for UPCOMING Event 3 (City Park Trail Intro)
(3, 1, 12), -- Violet (12) Event Coordinator
(3, 9, 6), -- Emma (6) Photographer

-- Assignments for PAST events 
(8, 1, 2), (8, 2, 3), (8, 3, 4), (8, 4, 5), (8, 5, 6), (8, 11, 7),
(9, 1, 12), (9, 2, 13), (9, 6, 14), (9, 8, 11), (9, 9, 10), (9, 10, 9), (9, 12, 8),
(10, 1, 2), (10, 2, 13), (10, 13, 14), (10, 6, 12), (10, 7, 11), (10, 4, 5);


-- ------------------------------
-- Event Participants (Attendees)
-- ------------------------------
INSERT INTO Event_Participants (event_id, user_id, status) VALUES
-- Event 1 (Avon River Fun Run - Group 1 members + others)
(1, 2, 'registered'), (1, 3, 'registered'), (1, 4, 'registered'), (1, 5, 'registered'), (1, 11, 'registered'), (1, 13, 'registered'),

-- Event 2 (Harbour Walk Challenge - Group 2 members + others)
(2, 3, 'registered'), (2, 2, 'registered'), (2, 5, 'registered'), (2, 7, 'registered'), (2, 6, 'registered'), (2, 15, 'registered'),

-- Event 3 (City Park Trail Intro - Group 3 members + others)
(3, 12, 'registered'), (3, 4, 'registered'), (3, 6, 'registered'), (3, 15, 'registered'), (3, 8, 'registered'), (3, 9, 'registered'),

-- Event 4 (Otago Peninsula Ride - Group 1 members + others)
(4, 2, 'registered'), (4, 11, 'registered'), (4, 13, 'registered'),

-- Event 5 (Lake Run Festival - Group 2 members + others)
(5, 3, 'registered'), (5, 7, 'registered'), (5, 5, 'registered'),

-- Event 6 (Hawke’s Bay Sunrise Walk - Group 3 members + others)
(6, 12, 'registered'), (6, 4, 'registered'), (6, 6, 'registered'),

-- Event 7 (Redwoods Forest Ride - Group 4 members)
(7, 10, 'registered'), (7, 14, 'registered'), (7, 9, 'registered'),

-- Registrations for PAST events (retained)
(8, 2, 'registered'), (8, 3, 'registered'), (8, 4, 'registered'), (8, 5, 'registered'), (8, 6, 'registered'),
(9, 3, 'registered'), (9, 4, 'registered'), (9, 9, 'registered'), (9, 10, 'registered'), (9, 11, 'registered'),
(10, 2, 'registered'), (10, 5, 'registered'), (10, 6, 'registered'), (10, 12, 'registered');


-- ------------------------------
-- Event Results
-- ------------------------------
INSERT INTO Event_Results (event_id, user_id, start_time, end_time) VALUES
(8, 2, '2025-06-15 08:00:00', '2025-06-15 08:52:30'), (8, 3, '2025-06-15 08:00:00', '2025-06-15 08:47:15'),
(8, 4, '2025-06-15 08:00:00', '2025-06-15 08:55:45'), (8, 5, '2025-06-15 08:00:00', '2025-06-15 08:43:20'),
(8, 6, '2025-06-15 08:00:00', '2025-06-15 08:58:10'), (8, 7, '2025-06-15 08:00:00', '2025-06-15 08:49:55'),
(9, 3, '2025-07-20 07:30:00', '2025-07-20 08:05:30'), (9, 4, '2025-07-20 07:30:00', '2025-07-20 08:02:15'),
(9, 9, '2025-07-20 07:30:00', '2025-07-20 08:01:45'), (9, 10, '2025-07-20 07:30:00', '2025-07-20 08:08:20'),
(9, 11, '2025-07-20 07:30:00', '2025-07-20 08:03:55'), (9, 12, '2025-07-20 07:30:00', '2025-07-20 08:07:10'),
(10, 2, '2025-08-10 08:30:00', '2025-08-10 09:12:45'), (10, 5, '2025-08-10 08:30:00', '2025-08-10 09:08:30'),
(10, 6, '2025-08-10 08:30:00', '2025-08-10 09:15:20'), (10, 7, '2025-08-10 08:30:00', '2025-08-10 09:10:15'),
(10, 12, '2025-08-10 08:30:00', '2025-08-10 09:06:55'), (10, 13, '2025-08-10 08:30:00', '2025-08-10 09:18:40');
