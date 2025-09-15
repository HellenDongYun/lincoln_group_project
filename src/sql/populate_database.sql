USE activeloop;

INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('alice.wong@gmail.com', '$2b$12$6nK5TrF/e0ItqIj4gfvr8u3bRc0EnNBCDPrCb3RZ0N3WeMM66PnJ2', 'Alice', 'Wong', 'Christchurch', 'participant', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('bob.jones@outlook.com', '$2b$12$rXr.7YWS7v3UWdVt23djuu5OuSBOzPVVZ1f35xhbpDaLNsw8u9SwO', 'Bob', 'Jones', 'Wellington', 'participant', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('carol.smith@yahoo.com', '$2b$12$7CUP0m4wnmZQMowRwOXqmuWHvOYal/csTzfZ83ACu6ZasyxeAeqGe', 'Carol', 'Smith', 'Auckland', 'participant', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('dave.brown@xtra.co.nz', '$2b$12$K4cqIZQUes39Cl8kK9DP4eVOgP1qMEQNAFLVX/8odG8f6Meb8tnta', 'Dave', 'Brown', 'Dunedin', 'participant', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('emma.taylor@gmail.com', '$2b$12$KILmHs90ksFzgKx1ImkfC.GG81zhBwFzGLz0I8Uv26y6AQ8Jd1ebO', 'Emma', 'Taylor', 'Hamilton', 'participant', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('frank.wilson@runclub.org', '$2b$12$TD.dSSVR7fBDcmRJOc6oPeytAISuiCxznOXddgxz/LwwHWneRoxNa', 'Frank', 'Wilson', 'Napier', 'participant', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('grace.johnson@gmail.com', '$2b$12$5/yaUQR50jHJnbNsSCkKzOvDNVyb3cBz3r3wwewARSNe2f7Tp6bQm', 'Grace', 'Johnson', 'Queenstown', 'participant', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('harry.lee@outlook.com', '$2b$12$/bniUKEWogvboR37pK9o/e68HnNWdsdWAexplfXKaJrBYom3tf/Ii', 'Harry', 'Lee', 'Nelson', 'participant', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('irene.martin@yahoo.com', '$2b$12$T3Ei39UaHvUyBAKX2r/Nj.Jyw8Mwwmda6ePzoDUz9ybUAR/3vJ5kK', 'Irene', 'Martin', 'Rotorua', 'participant', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('jack.white@xtra.co.nz', '$2b$12$r7F.kNhiIXwgd8anMNHIWeGniwK5Yg2IkdhS80BzOP46KsNDf6Mri', 'Jack', 'White', 'Palmerston North', 'participant', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('vanna.patel@gmail.com', '$2b$12$/r32jZiFQ67qycL/1xMrm.zDXgFlUNg4PCtVuVEBiB/r2ym2Tz9Wq', 'Vanna', 'Patel', 'Christchurch', 'volunteer', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('victor.singh@outlook.com', '$2b$12$AsxuuNX6ePY0W3.a9EnVZO2b.zUU.LxphQsVnf7lmLbtsGcJtPqMe', 'Victor', 'Singh', 'Wellington', 'volunteer', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('violet.kumar@lincoln.ac.nz', '$2b$12$fZ4/aA9xbBKgvmwnyLK6tuOj.OruGE3VuKnfIq.mCy8z8VGOiGHqK', 'Violet', 'Kumar', 'Auckland', 'volunteer', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('vincent.anderson@gmail.com', '$2b$12$tB2NJ2ffcQsoGOpcPMQAm.W/ZZ9Jst1yGfD6QlWAzVpEh6Dj8f5Im', 'Vincent', 'Anderson', 'Dunedin', 'volunteer', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('vladimir.scott@runclub.org', '$2b$12$9SiyYX4tvwjX9sbFAb1Y7.mwFiyrG1eRlx/Ms7CrdKgdjnsfqyKbm', 'Vladimir', 'Scott', 'Rotorua', 'volunteer', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('valentina.green@gmail.com', '$2b$12$KyC5ouMLtuaSyqyOt5cnAuoveLpRAf/xul6cDJoUwDvGwDMcduzKm', 'Valentina', 'Green', 'Palmerston North', 'volunteer', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('nick.singh@lincoln.ac.nz', '$2b$12$qepn.sqstQwCeFMmlSQpCeY9Fmd7Qo8cFnwMHlxYZKcf13Pawrvim', 'Nick', 'Singh', 'Christchurch', 'admin', 'active');
INSERT INTO Users (email, password_hash, first_name, last_name, town, role, status)
VALUES ('frank.smith@airnz.co.nz', '$2b$12$0t991Pmax1ydXeTmE7Wzk.1tkWITRycnUNgQ/VlmYGFv1jSVkA9CK', 'Frank', 'Smith', 'Auckland', 'admin', 'active');


-- Insert 10 Upcoming Events (IDs will be 1-10) 
-- First 2 Events on same date for testing

INSERT INTO Events (datetime, town, name, event_type, description, max_participants) VALUES
    ('2025-09-15 07:30:00', 'Christchurch', 'Avon River Fun Run', '5km Run', 'A scenic 5km loop along the Avon River for all ages.', 8),
    ('2025-09-15 08:00:00', 'Wellington', 'Harbour Walk Challenge', '10km Walk', 'A coastal 10km walk around the harbour with great views.', 10),
    ('2025-09-21 07:00:00', 'Auckland', 'City Park Run', '5km Run', 'Weekly community park run through Auckland Domain.', 10),
    ('2025-09-28 07:30:00', 'Dunedin', 'Otago Peninsula Ride', 'Cycling 20km', 'A friendly 20km cycle event around the peninsula roads.', 20),
    ('2025-10-05 09:00:00', 'Hamilton', 'Lake Run Festival', '10km Run', 'A flat 10km circuit around Lake Rotoroa.', 25),
    ('2025-10-12 08:30:00', 'Napier', 'Hawke’s Bay Sunrise Walk', '5km Walk', 'An early morning 5km walk by the waterfront.', 18),
    ('2025-10-19 07:45:00', 'Queenstown', 'Remarkables Fun Run', '5km Run', 'Run with views of the Remarkables mountain range.', 20),
    ('2025-10-26 08:15:00', 'Nelson', 'Tahunanui Beach Jog', 'Beach Run 5km', 'A sandy 5km jog along Tahunanui Beach.', 16),
    ('2025-11-02 07:30:00', 'Rotorua', 'Redwoods Forest Trail', 'Trail Run 8km', 'An 8km trail event through Whakarewarewa Forest.', 14),
    ('2025-11-09 08:00:00', 'Palmerston North', 'Manawatu River Walk', 'Community Walk 6km', 'A relaxed 6km riverside walk suitable for families.', 20);

 -- Insert 3 Past Events
INSERT INTO Events (datetime, town, name, event_type, description, max_participants) VALUES
    ('2025-06-15 08:00:00', 'Wellington', 'Capital City Marathon', '10km Run', 'Annual Wellington 10km run through the city center and waterfront.', 20),
    ('2025-07-20 07:30:00', 'Auckland', 'Auckland Harbour Bridge Fun Run', '5km Run', 'Iconic 5km run across Auckland Harbour Bridge with stunning views.', 20),
    ('2025-08-10 08:30:00', 'Christchurch', 'Garden City Cycling Challenge', 'Cycling 15km', 'Scenic 15km cycle through Christchurch parks and gardens.', 30);


INSERT INTO Volunteer_Roles (name, description) VALUES
    ('Event Coordinator', 'Oversees the entire event, ensures safety, resolves on-site issues.'),
    ('Registration Assistant', 'Welcomes participants, checks them in, helps with new registrations.'),
    ('Course Marshal', 'Guides participants along the course, encourages, reports incidents.'),
    ('Timekeeper', 'Records finish times using manual or basic timing tools.'),
    ('Results Recorder', 'Enters and uploads participant times and attendance after the event.'),
    ('Route Setup Crew', 'Sets up signage, cones, and markers along the course before the event.'),
    ('Pack-down Crew', 'Dismantles and stores equipment after the event.'),
    ('Tail Walker/Cyclist', 'Travels behind the last participant to ensure everyone returns safely.'),
    ('Photographer/Social Media Volunteer', 'Captures photos and helps create online content.'),
    ('First Timers’ Host', 'Greets and orients new participants, explains the course, answers questions.'),
    ('Safety & First Aid Support', 'Provides basic first aid support and responds to minor injuries.'),
    ('Volunteer Coordinator', 'Confirms volunteers, assigns roles, briefs and supports them.'),
    ('Bike Marshal', 'Guides cyclists at key points, manages spacing, ensures route safety.');

-- Participants for Avon River Fun Run (Event ID will be 1)
INSERT INTO Participants (event_id, participant_id, status) VALUES
    (1, 1, 'registered'),  -- Alice Wong
    (1, 2, 'registered'),  -- Bob Jones
    (1, 3, 'registered'),  -- Carol Smith
    (1, 4, 'registered'),  -- Dave Brown
    (1, 5, 'registered'),  -- Emma Taylor
    (1, 6, 'registered'),  -- Frank Wilson
    (1, 7, 'registered');  -- Grace Johnson


-- Participants for Wellington Capital City Marathon (Event ID will be 11)
INSERT INTO Participants (event_id, participant_id, status) VALUES
    (11, 1, 'registered'),  -- Alice Wong
    (11, 2, 'registered'),  -- Bob Jones
    (11, 3, 'registered'),  -- Carol Smith
    (11, 4, 'registered'),  -- Dave Brown
    (11, 5, 'registered'),  -- Emma Taylor
    (11, 6, 'registered'),  -- Frank Wilson
    (11, 7, 'registered');  -- Grace Johnson

-- Participants for Auckland Harbour Bridge Fun Run (Event ID will be 12)
INSERT INTO Participants (event_id, participant_id, status) VALUES
    (12, 2, 'registered'),  -- Bob Jones
    (12, 3, 'registered'),  -- Carol Smith
    (12, 8, 'registered'),  -- Harry Lee
    (12, 9, 'registered'),  -- Irene Martin
    (12, 10, 'registered'), -- Jack White
    (12, 11, 'registered'); -- Vanna Patel (volunteer participating)

-- Participants for Christchurch Garden City Cycling Challenge (Event ID will be 13)
INSERT INTO Participants (event_id, participant_id, status) VALUES
    (13, 1, 'registered'),  -- Alice Wong
    (13, 4, 'registered'),  -- Dave Brown
    (13, 5, 'registered'),  -- Emma Taylor
    (13, 6, 'registered'),  -- Frank Wilson
    (13, 12, 'registered'), -- Victor Singh (volunteer participating)
    (13, 13, 'registered'); -- Violet Kumar (volunteer participating)

-- Volunteer assignments for Wellington Capital City Marathon (Event ID 11)
INSERT INTO Event_Volunteers (event_id, role_id, volunteer_id) VALUES
    (11, 1, 11),  -- Vanna Patel as Event Coordinator
    (11, 2, 12),  -- Victor Singh as Registration Assistant
    (11, 3, 13),  -- Violet Kumar as Course Marshal
    (11, 4, 14),  -- Vincent Anderson as Timekeeper
    (11, 5, 15),  -- Vladimir Scott as Results Recorder
    (11, 11, 16); -- Valentina Green as Safety & First Aid Support

-- Volunteer assignments for Auckland Harbour Bridge Fun Run (Event ID 12)
INSERT INTO Event_Volunteers (event_id, role_id, volunteer_id) VALUES
    (12, 1, 12),  -- Victor Singh as Event Coordinator
    (12, 2, 13),  -- Violet Kumar as Registration Assistant
    (12, 6, 14),  -- Vincent Anderson as Route Setup Crew
    (12, 8, 15),  -- Vladimir Scott as Tail Walker/Cyclist
    (12, 9, 16),  -- Valentina Green as Photographer/Social Media Volunteer
    (12, 10, 17), -- Nick Singh as First Timers' Host
    (12, 12, 18); -- Frank Smith as Volunteer Coordinator

-- Volunteer assignments for Christchurch Garden City Cycling Challenge (Event ID 13)
INSERT INTO Event_Volunteers (event_id, role_id, volunteer_id) VALUES
    (13, 1, 13),  -- Violet Kumar as Event Coordinator
    (13, 2, 14),  -- Vincent Anderson as Registration Assistant
    (13, 13, 15), -- Vladimir Scott as Bike Marshal
    (13, 6, 16),  -- Valentina Green as Route Setup Crew
    (13, 7, 17),  -- Nick Singh as Pack-down Crew
    (13, 4, 18);  -- Frank Smith as Timekeeper

-- Race Results for Wellington Capital City Marathon (Event ID 11) - 10km Run
INSERT INTO Race_Results (event_id, participant_id, start_time, end_time) VALUES
    (11, 1, '2025-06-15 08:00:00', '2025-06-15 08:52:30'), -- Alice Wong - 52:30
    (11, 2, '2025-06-15 08:00:00', '2025-06-15 08:47:15'), -- Bob Jones - 47:15
    (11, 3, '2025-06-15 08:00:00', '2025-06-15 08:55:45'), -- Carol Smith - 55:45
    (11, 4, '2025-06-15 08:00:00', '2025-06-15 08:43:20'), -- Dave Brown - 43:20
    (11, 5, '2025-06-15 08:00:00', '2025-06-15 08:58:10'), -- Emma Taylor - 58:10
    (11, 6, '2025-06-15 08:00:00', '2025-06-15 08:49:55'), -- Frank Wilson - 49:55
    (11, 7, '2025-06-15 08:00:00', '2025-06-15 08:51:40'); -- Grace Johnson - 51:40

-- Race Results for Auckland Harbour Bridge Fun Run (Event ID 12) - 5km Run
INSERT INTO Race_Results (event_id, participant_id, start_time, end_time) VALUES
    (12, 2, '2025-07-20 07:30:00', '2025-07-20 08:05:30'), -- Bob Jones - 35:30
    (12, 3, '2025-07-20 07:30:00', '2025-07-20 08:02:15'), -- Carol Smith - 32:15
    (12, 8, '2025-07-20 07:30:00', '2025-07-20 08:01:45'), -- Harry Lee - 31:45
    (12, 9, '2025-07-20 07:30:00', '2025-07-20 08:08:20'), -- Irene Martin - 38:20
    (12, 10, '2025-07-20 07:30:00', '2025-07-20 08:03:55'), -- Jack White - 33:55
    (12, 11, '2025-07-20 07:30:00', '2025-07-20 08:07:10'); -- Vanna Patel - 37:10

-- Race Results for Christchurch Garden City Cycling Challenge (Event ID 13) - 15km Cycling
INSERT INTO Race_Results (event_id, participant_id, start_time, end_time) VALUES
    (13, 1, '2025-08-10 08:30:00', '2025-08-10 09:12:45'), -- Alice Wong - 42:45
    (13, 4, '2025-08-10 08:30:00', '2025-08-10 09:08:30'), -- Dave Brown - 38:30
    (13, 5, '2025-08-10 08:30:00', '2025-08-10 09:15:20'), -- Emma Taylor - 45:20
    (13, 6, '2025-08-10 08:30:00', '2025-08-10 09:10:15'), -- Frank Wilson - 40:15
    (13, 12, '2025-08-10 08:30:00', '2025-08-10 09:06:55'), -- Victor Singh - 36:55
    (13, 13, '2025-08-10 08:30:00', '2025-08-10 09:18:40'); -- Violet Kumar - 48:40

-- Add some vacancy records for these past events (showing what volunteer spots were available)
INSERT INTO Vacancies (event_id, role_id, spots) VALUES
    -- Wellington Capital City Marathon vacancies
    (11, 1, 1), (11, 2, 2), (11, 3, 3), (11, 4, 1), (11, 5, 1), (11, 11, 2),
    -- Auckland Harbour Bridge Fun Run vacancies  
    (12, 1, 1), (12, 2, 2), (12, 6, 2), (12, 8, 1), (12, 9, 1), (12, 10, 2), (12, 12, 1),
    -- Christchurch Garden City Cycling Challenge vacancies
    (13, 1, 1), (13, 2, 1), (13, 13, 2), (13, 6, 1), (13, 7, 1), (13, 4, 1);