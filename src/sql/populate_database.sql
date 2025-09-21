USE activeloop;

-- Users (1 super admin + participants)
-- Password hashes retained from previous dataset (bcrypt)
INSERT INTO Users (email, password_hash, first_name, last_name, town, global_role, status) VALUES
 ('super.admin@platform.org', '$2b$12$0t991Pmax1ydXeTmE7Wzk.1tkWITRycnUNgQ/VlmYGFv1jSVkA9CK', 'Super', 'Admin', 'Christchurch', 'super_admin', 'active'),
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

-- IDs assumed sequential starting at 1
-- 1 = Super Admin, 2..16 participants

-- Seed Groups
INSERT INTO Community_Groups (name, description, town, visibility, join_type, status, created_by) VALUES
 ('Darfield Forest Cycling Group', 'Weekly forest and gravel rides around Darfield area.', 'Christchurch', 'public', 'open', 'active', 1),
 ('Harbour Runners Wellington', 'Inclusive running group focusing on 5k to half-marathon training.', 'Wellington', 'public', 'open', 'active', 1),
 ('Auckland Trail Explorers', 'Trail running & hiking exploration in Auckland region.', 'Auckland', 'public', 'closed', 'active', 1),
 ('Rotorua Adventure Club', 'Mixed cycling and trail events in the Redwoods.', 'Rotorua', 'private', 'closed', 'active', 1);

-- Group Memberships 
-- Make Violet manager of Auckland Trail Explorers, Bob manager of Harbour Runners, Alice manager of Darfield Cycling, Irene manager of Rotorua Adventure (private)
INSERT INTO Group_Memberships (group_id, user_id, group_role) VALUES
 (1, 2, 'manager'),  -- Alice manager Darfield
 (1, 3, 'member'),  -- Bob member Darfield
 (1, 4, 'member'),  -- Carol member Darfield
 (1, 11, 'member'), -- Jack member Darfield
 (2, 3, 'manager'),  -- Bob manager Harbour Runners
 (2, 2, 'member'),   -- Alice member Harbour Runners
 (2, 5, 'member'),   -- Dave member Harbour Runners
 (3, 12, 'manager'), -- Violet manager Auckland Trail Explorers
 (3, 4, 'member'),   -- Carol member Trail Explorers
 (3, 6, 'member'),   -- Emma member Trail Explorers
 (4, 10, 'manager'), -- Irene manager Rotorua Adventure
 (4, 14, 'member');  -- Vladimir member Rotorua Adventure


-- Group Applications (pending + approved sample)
INSERT INTO Group_Applications (applicant_id, proposed_name, proposed_description, proposed_town, visibility, join_type, status, decision_by)
VALUES
 (5, 'Hamilton Fitness Collective', 'Local mixed-discipline fitness and running events.', 'Hamilton', 'public', 'open', 'pending', NULL),
 (7, 'Napier Coastal Walkers', 'Social coastal walking group.', 'Napier', 'public', 'open', 'approved', 1),
 (8, 'Queenstown Mountain Riders', 'Mountain terrain cycling crew.', 'Queenstown', 'private', 'closed', 'rejected', 1);


-- Volunteer Tasks catalogue
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


-- Events (link to groups) - 7 upcoming, 3 past to allow results
-- Use manager or super admin as created_by
INSERT INTO Events (group_id, datetime, town, name, event_type, description, max_participants, visibility, created_by) VALUES
 (1, '2025-09-15 07:30:00', 'Christchurch', 'Avon River Fun Run', '5km Run', 'A scenic 5km loop along the Avon River for all ages.', 50, 'public', 2),
 (2, '2025-09-15 08:00:00', 'Wellington', 'Harbour Walk Challenge', '10km Walk', 'Coastal 10km walk with harbour views.', 80, 'public', 3),
 (3, '2025-09-21 07:00:00', 'Auckland', 'City Park Trail Intro', 'Trail 5km', 'Introductory trail around city park tracks.', 60, 'public', 12),
 (1, '2025-09-28 07:30:00', 'Dunedin', 'Otago Peninsula Ride', 'Cycling 20km', 'Friendly 20km cycle around peninsula.', 120, 'public', 2),
 (2, '2025-10-05 09:00:00', 'Hamilton', 'Lake Run Festival', '10km Run', 'Flat 10km circuit around Lake Rotoroa.', 150, 'public', 3),
 (3, '2025-10-12 08:30:00', 'Napier', 'Hawke’s Bay Sunrise Walk', '5km Walk', 'Early morning coastal walk.', 90, 'public', 12),
 (4, '2025-10-19 07:45:00', 'Rotorua', 'Redwoods Forest Ride', 'Trail Ride 15km', 'Ride through Whakarewarewa Forest.', 70, 'private', 10),
 -- Past events
 (2, '2025-06-15 08:00:00', 'Wellington', 'Capital City Marathon', '10km Run', 'Annual Wellington 10km run.', 200, 'public', 3),
 (3, '2025-07-20 07:30:00', 'Auckland', 'Auckland Harbour Bridge Fun Run', '5km Run', 'Iconic bridge run.', 250, 'public', 12),
 (1, '2025-08-10 08:30:00', 'Christchurch', 'Garden City Cycling Challenge', 'Cycling 15km', 'Scenic 15km cycle event.', 180, 'public', 2);


-- Event Participants 
INSERT INTO Event_Participants (event_id, user_id, status) VALUES
 (1, 2, 'registered'), (1, 3, 'registered'), (1, 4, 'registered'), (1, 5, 'registered'),
 (2, 3, 'registered'), (2, 2, 'registered'), (2, 5, 'registered'),
 (8, 2, 'registered'), (8, 3, 'registered'), (8, 4, 'registered'), (8, 5, 'registered'), (8, 6, 'registered'),
 (9, 3, 'registered'), (9, 4, 'registered'), (9, 9, 'registered'), (9, 10, 'registered'), (9, 11, 'registered'),
 (10, 2, 'registered'), (10, 5, 'registered'), (10, 6, 'registered'), (10, 12, 'registered');

-- Event Task Vacancies
INSERT INTO Event_Task_Vacancies (event_id, task_id, spots) VALUES
 (8, 1, 1), (8, 2, 3), (8, 3, 4), (8, 4, 2), (8, 5, 2), (8, 11, 2),
 (9, 1, 1), (9, 2, 2), (9, 6, 2), (9, 8, 1), (9, 9, 1), (9, 10, 2), (9, 12, 1),
 (10, 1, 1), (10, 2, 2), (10, 13, 2), (10, 6, 1), (10, 7, 1), (10, 4, 1);


-- Event Task Assignments for past events 
INSERT INTO Event_Task_Assignments (event_id, task_id, user_id) VALUES
 (8, 1, 2),  -- Alice as Event Coordinator
 (8, 2, 3),  -- Bob Registration
 (8, 3, 4),  -- Carol Marshal
 (8, 4, 5),  -- Dave Timekeeper
 (8, 5, 6),  -- Emma Results
 (8, 11, 7), -- Frank Safety
 (9, 1, 12), -- Violet Coordinator
 (9, 2, 13), -- Vincent Registration
 (9, 6, 14), -- Vladimir Setup
 (9, 8, 11), -- Jack Tail Walker
 (9, 9, 10), -- Irene Photographer
 (9, 10, 9), -- Harry First Timers Host
 (9, 12, 8), -- Grace Volunteer Coordinator
 (10, 1, 2), -- Alice Coordinator
 (10, 2, 13), -- Vincent Registration
 (10, 13, 14), -- Vladimir Bike Marshal
 (10, 6, 12), -- Violet Setup
 (10, 7, 11), -- Jack Pack-down
 (10, 4, 5);  -- Dave Timekeeper


-- Event Results for past events (8,9,10)
INSERT INTO Event_Results (event_id, user_id, start_time, end_time) VALUES
 (8, 2, '2025-06-15 08:00:00', '2025-06-15 08:52:30'),
 (8, 3, '2025-06-15 08:00:00', '2025-06-15 08:47:15'),
 (8, 4, '2025-06-15 08:00:00', '2025-06-15 08:55:45'),
 (8, 5, '2025-06-15 08:00:00', '2025-06-15 08:43:20'),
 (8, 6, '2025-06-15 08:00:00', '2025-06-15 08:58:10'),
 (8, 7, '2025-06-15 08:00:00', '2025-06-15 08:49:55'),
 (9, 3, '2025-07-20 07:30:00', '2025-07-20 08:05:30'),
 (9, 4, '2025-07-20 07:30:00', '2025-07-20 08:02:15'),
 (9, 9, '2025-07-20 07:30:00', '2025-07-20 08:01:45'),
 (9, 10, '2025-07-20 07:30:00', '2025-07-20 08:08:20'),
 (9, 11, '2025-07-20 07:30:00', '2025-07-20 08:03:55'),
 (9, 12, '2025-07-20 07:30:00', '2025-07-20 08:07:10'),
 (10, 2, '2025-08-10 08:30:00', '2025-08-10 09:12:45'),
 (10, 5, '2025-08-10 08:30:00', '2025-08-10 09:08:30'),
 (10, 6, '2025-08-10 08:30:00', '2025-08-10 09:15:20'),
 (10, 7, '2025-08-10 08:30:00', '2025-08-10 09:10:15'),
 (10, 12, '2025-08-10 08:30:00', '2025-08-10 09:06:55'),
 (10, 13, '2025-08-10 08:30:00', '2025-08-10 09:18:40');

