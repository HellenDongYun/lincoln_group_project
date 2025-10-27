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
-- support.tech@platform.org    Support123!

-- ------------------------------
INSERT INTO Users (email, password_hash, first_name, last_name, gender, age, town, global_role, status) VALUES
('super.admin@platform.org', '$2a$12$MJ1uykG7aegnqalX4IYmYOpuBsv3Z62g2eZyb6djTa4I0r7kQ8dV.', 'Super', 'Admin', 'male', 48, 'Christchurch', 'super_admin', 'active'),
('alice.wong@gmail.com', '$2b$12$6nK5TrF/e0ItqIj4gfvr8u3bRc0EnNBCDPrCb3RZ0N3WeMM66PnJ2', 'Alice', 'Wong', 'female', 29, 'Christchurch', 'participant', 'active'),
('bob.jones@outlook.com', '$2b$12$rXr.7YWS7v3UWdVt23djuu5OuSBOzPVVZ1f35xhbpDaLNsw8u9SwO', 'Bob', 'Jones', 'male', 34, 'Wellington', 'participant', 'active'),
('carol.smith@yahoo.com', '$2b$12$7CUP0m4wnmZQMowRwOXqmuWHvOYal/csTzfZ83ACu6ZasyxeAeqGe', 'Carol', 'Smith', 'female', 41, 'Auckland', 'participant', 'active'),
('dave.brown@xtra.co.nz', '$2b$12$K4cqIZQUes39Cl8kK9DP4eVOgP1qMEQNAFLVX/8odG8f6Meb8tnta', 'Dave', 'Brown', 'male', 22, 'Dunedin', 'participant', 'active'),
('emma.taylor@gmail.com', '$2b$12$KILmHs90ksFzgKx1ImkfC.GG81zhBwFzGLz0I8Uv26y6AQ8Jd1ebO', 'Emma', 'Taylor', 'female', 27, 'Hamilton', 'participant', 'active'),
('frank.wilson@runclub.org', '$2b$12$TD.dSSVR7fBDcmRJOc6oPeytAISuiCxznOXddgxz/LwwHWneRoxNa', 'Frank', 'Wilson', 'male', 36, 'Napier', 'participant', 'active'),
('grace.johnson@gmail.com', '$2b$12$5/yaUQR50jHJnbNsSCkKzOvDNVyb3cBz3r3wwewARSNe2f7Tp6bQm', 'Grace', 'Johnson', 'female', 31, 'Queenstown', 'participant', 'active'),
('harry.lee@outlook.com', '$2b$12$/bniUKEWogvboR37pK9o/e68HnNWdsdWAexplfXKaJrBYom3tf/Ii', 'Harry', 'Lee', 'male', 19, 'Nelson', 'participant', 'active'),
('irene.martin@yahoo.com', '$2b$12$T3Ei39UaHvUyBAKX2r/Nj.Jyw8Mwwmda6ePzoDUz9ybUAR/3vJ5kK', 'Irene', 'Martin', 'female', 46, 'Rotorua', 'participant', 'active'),
('jack.white@xtra.co.nz', '$2b$12$r7F.kNhiIXwgd8anMNHIWeGniwK5Yg2IkdhS80BzOP46KsNDf6Mri', 'Jack', 'White', 'male', 52, 'Palmerston North', 'participant', 'active'),
('violet.kumar@lincoln.ac.nz', '$2b$12$fZ4/aA9xbBKgvmwnyLK6tuOj.OruGE3VuKnfIq.mCy8z8VGOiGHqK', 'Violet', 'Kumar', 'female', 24, 'Auckland', 'participant', 'active'),
('vincent.anderson@gmail.com', '$2b$12$tB2NJ2ffcQsoGOpcPMQAm.W/ZZ9Jst1yGfD6QlWAzVpEh6Dj8f5Im', 'Vincent', 'Anderson', 'male', 33, 'Dunedin', 'participant', 'active'),
('vladimir.scott@runclub.org', '$2b$12$9SiyYX4tvwjX9sbFAb1Y7.mwFiyrG1eRlx/Ms7CrdKgdjnsfqyKbm', 'Vladimir', 'Scott', 'other', 28, 'Rotorua', 'participant', 'active'),
('valentina.green@gmail.com', '$2b$12$KyC5ouMLtuaSyqyOt5cnAuoveLpRAf/xul6cDJoUwDvGwDMcduzKm', 'Valentina', 'Green', 'female', 30, 'Palmerston North', 'participant', 'active'),
('support.tech@platform.org', '$2a$12$WTDdKSew1rXMuLtWi6vClOgmzI0U4l2Z5U4kl0tTfplKG.1Cm/.xG', 'Morgan', 'Reeves', 'other', 35, 'Christchurch', 'support_technician', 'active');


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
(2, 'Auckland Run', 'Local running events.', 'Auckland', 'public', 'pending', NULL),
(6, 'Auckland Fitness Collective', 'Local mixed-discipline fitness and running events.', 'Auckland', 'private', 'pending', NULL),
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
-- Achievements & Challenges
-- ------------------------------
INSERT INTO Achievements (id, name, description, points_reward) VALUES
(1, 'Getting Started', 'Complete your very first event.', 50),
(2, 'Weekend Warrior', 'Attend events on a Saturday and Sunday in the same weekend.', 75),
(3, 'Dedicated Participant', 'Complete 5 events in a single month.', 150),
(4, 'Community Helper', 'Complete your first volunteer task.', 100),
(5, 'Volunteer Veteran', 'Log a total of 10 volunteer hours.', 200),
(6, 'Jack of All Trades', 'Volunteer for three different types of tasks.', 150),
(7, 'Better Than Ever', 'Beat your own personal best time in an event.', 50),
(8, 'Top 10%', 'Finish in the top 10% of participants in a large event.', 100),
(9, 'Podium Finish', 'Finish in the top 3 of a competitive event.', 250),
(10, 'Explorer', 'Attend events in three different towns.', 100),
(11, 'Adventurer', 'Participate in three different types of events.', 150),
(12, 'Social Butterfly', 'Join three different Community Groups.', 0),
(13, 'Founders Trophy', 'Successfully create a new Community Group.', 300);

INSERT INTO Challenges (name, description, target_metric, target_value, timeframe_days, achievement_id_reward) VALUES
('Ice Breaker', 'Complete your very first event.', 'events_attended', 1, NULL, 1),
('Monthly Milestone', 'Complete 5 events within a single calendar month.', 'events_attended_monthly', 5, 30, 3),
('Helping Hand', 'Complete your first volunteer task.', 'volunteer_tasks', 1, NULL, 4),
('Volunteer Veteran', 'Log a total of 10 volunteer hours.', 'volunteer_hours', 10, NULL, 5),
('Versatile Volunteer', 'Volunteer for three different types of tasks.', 'volunteer_tasks_distinct', 3, NULL, 6),
('Event Explorer', 'Participate in 3 different event types.', 'event_types_distinct', 3, NULL, 11),
('Local Tourist', 'Attend events in three different towns.', 'locations_distinct', 3, NULL, 10),
('Social Butterfly', 'Become a member of three different Community Groups.', 'groups_joined', 3, NULL, 12),
('Group Founder', 'Successfully apply for and create a new Community Group.', 'groups_founded', 1, NULL, 13);

INSERT INTO User_Achievements (user_id, achievement_id, earned_at) VALUES
(2, 1, '2025-04-12 09:10:00'),
(2, 4, '2025-05-04 10:05:00'),
(3, 1, '2025-04-18 08:45:00'),
(3, 3, '2025-07-01 09:30:00'),
(4, 1, '2025-07-15 08:20:00'),
(4, 7, '2025-08-05 08:50:00'),
(5, 4, '2025-07-24 07:40:00'),
(5, 5, '2025-08-18 09:15:00'),
(6, 1, '2025-08-02 08:05:00'),
(7, 4, '2025-06-28 07:35:00');


-- ------------------------------
-- Group Challenges & Assignments
-- ------------------------------
INSERT INTO Group_Challenges (group_id, name, description, target_metric, target_value, timeframe_days, achievement_id, reward_badge_label, reward_trophy_label, verification_required, status, created_by, created_at, published_at) VALUES
(1, 'Darfield Spring Sprint', 'Complete three club events during the September push.', 'events_attended', 3, 30, 3, 'Darfield Pace Setter', NULL, FALSE, 'published', 2, '2025-08-28 08:00:00', '2025-09-01 08:00:00'),
(2, 'Harbour Elevation Challenge', 'Climb 1,500 metres cumulative elevation with the club this month.', 'elevation_gain_meters', 1500, 30, NULL, 'Harbour Climber Badge', NULL, TRUE, 'published', 3, '2025-08-25 09:30:00', '2025-09-05 07:00:00'),
(3, 'Trail Photo Hunt', 'Capture five unique landmarks during club-led trail adventures.', 'photos_submitted', 5, 45, NULL, 'Trail Storyteller Badge', 'Trail Explorer Trophy', TRUE, 'draft', 12, '2025-09-10 10:00:00', NULL);

INSERT INTO Group_Challenge_Assignments (challenge_id, user_id, status, progress, completed_at, verified_by, verified_at, badge_awarded_at, trophy_awarded_at) VALUES
(1, 2, 'completed', 3, '2025-09-18 08:30:00', 2, '2025-09-18 09:00:00', '2025-09-18 09:05:00', NULL),
(1, 3, 'completed', 3, '2025-09-19 07:55:00', 2, '2025-09-19 08:20:00', '2025-09-19 08:30:00', NULL),
(1, 4, 'active', 2, NULL, NULL, NULL, NULL, NULL),
(2, 3, 'completed', 1500, '2025-09-24 18:45:00', 3, '2025-09-24 19:10:00', '2025-09-24 19:15:00', NULL),
(2, 2, 'active', 950, NULL, NULL, NULL, NULL, NULL),
(2, 5, 'active', 600, NULL, NULL, NULL, NULL, NULL),
(3, 12, 'active', 1, NULL, NULL, NULL, NULL, NULL),
(3, 4, 'active', 0, NULL, NULL, NULL, NULL, NULL),
(3, 6, 'active', 0, NULL, NULL, NULL, NULL, NULL);

INSERT INTO User_Reward_Items (user_id, challenge_id, item_type, label, awarded_at) VALUES
(2, 1, 'badge', 'Darfield Pace Setter', '2025-09-18 09:05:00'),
(3, 1, 'badge', 'Darfield Pace Setter', '2025-09-19 08:30:00'),
(3, 2, 'badge', 'Harbour Climber Badge', '2025-09-24 19:15:00');


-- ------------------------------
-- Events
-- ------------------------------
INSERT INTO Events (group_id, datetime, town, name, event_type, description, max_participants, visibility, created_by) VALUES
(1, '2025-11-15 07:30:00', 'Christchurch', 'Avon River Fun Run', '5km Run', 'A scenic 5km loop along the Avon River for all ages.', 50, 'public', 2), -- 1: UPCOMING (Sept 15)
(2, '2025-11-15 08:00:00', 'Wellington', 'Harbour Walk Challenge', '10km Walk', 'Coastal 10km walk with harbour views.', 80, 'public', 3), -- 2: UPCOMING (Sept 15)
(3, '2025-11-21 07:00:00', 'Auckland', 'City Park Trail Intro', 'Trail 5km', 'Introductory trail around city park tracks.', 60, 'public', 12), -- 3: UPCOMING (Sept 21)
(1, '2025-12-28 07:30:00', 'Dunedin', 'Otago Peninsula Ride', 'Cycling 20km', 'Friendly 20km cycle around peninsula.', 120, 'public', 2), -- 4: UPCOMING
(2, '2025-11-05 09:00:00', 'Hamilton', 'Lake Run Festival', '10km Run', 'Flat 10km circuit around Lake Rotoroa.', 150, 'public', 3), -- 5: UPCOMING
(3, '2025-11-12 08:30:00', 'Napier', 'Hawke’s Bay Sunrise Walk', '5km Walk', 'Early morning coastal walk.', 90, 'public', 12), -- 6: UPCOMING
(4, '2025-11-19 07:45:00', 'Rotorua', 'Redwoods Forest Ride', 'Trail Ride 15km', 'Ride through Whakarewarewa Forest.', 70, 'private', 10), -- 7: UPCOMING
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
-- Assignments for UPCOMING Event 1 Avon River Fun Run
(1, 1, 2), -- Alice (2) Event Coordinator
(1, 3, 5), -- Dave (5) Course Marshal

-- Assignments for UPCOMING Event 2 Harbour Walk Challenge
(2, 2, 7),-- Frank (7) Registration Assistant
(2, 3, 2), -- Alice (2) Course Marshal -Member of Group 2

-- Assignments for UPCOMING Event 3 City Park Trail Intro
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


-- ------------------------------
-- Support Requests & Conversations
-- ------------------------------
INSERT INTO Support_Requests (user_id, issue_type, subject, description, screenshot_path, status, priority, assigned_to, created_at, updated_at) VALUES
(2, 'technical', 'Cannot upload run result screenshot', 'I receive a 500 error when trying to upload my run proof for Avon River Fun Run.', '/uploads/support/avon-run-upload-error.png', 'new', 'high', NULL, '2025-09-07 08:45:00', '2025-09-07 08:45:00'),
(3, 'event', 'Harbour Walk volunteer roster missing task', 'The Course Marshal slot I usually cover is not available for the October Harbour Walk event.', NULL, 'open', 'medium', 16, '2025-09-05 11:20:00', '2025-09-06 09:05:00'),
(4, 'group', 'Need help approving private group requests', 'Our Auckland Trail Explorers group has pending join requests but I cannot see the approve button.', '/uploads/support/group-approval.png', 'open', 'high', 16, '2025-09-04 18:10:00', '2025-09-08 10:25:00'),
(5, 'account', 'Reset password email never arrives', 'Tried resetting my password twice and no email shows up.', NULL, 'stalled', 'medium', 16, '2025-08-29 07:55:00', '2025-09-03 13:10:00'),
(6, 'bug', 'Results table shows duplicate rows', 'My results dashboard duplicates the Hawke’s Bay Sunrise Walk finishing time.', NULL, 'resolved', 'low', 16, '2025-08-20 09:30:00', '2025-08-22 16:15:00'),
(9, 'volunteer', 'Unable to claim Timekeeper spot', 'I click claim for Timekeeper on event ID 5 and nothing happens.', NULL, 'new', 'medium', NULL, '2025-09-09 14:05:00', '2025-09-09 14:05:00');

INSERT INTO Support_Request_Comments (request_id, user_id, comment, is_staff_reply, created_at) VALUES
(1, 2, 'Here is the exact time the error occurs: right after selecting the file.', FALSE, '2025-09-07 08:46:00'),
(2, 3, 'Hi team, is there a way to reopen that marshal slot?', FALSE, '2025-09-05 11:22:00'),
(2, 16, 'Thanks Bob, I have re-enabled the Course Marshal task for October. Please reload.', TRUE, '2025-09-06 09:05:00'),
(3, 4, 'Two runners are waiting on approval so hoping to get this sorted.', FALSE, '2025-09-04 18:12:00'),
(3, 16, 'Issue traced to missing manager flag. Patch deployed; can you try again?', TRUE, '2025-09-08 10:20:00'),
(4, 16, 'We see mail logs showing a bounce. Confirming with provider now.', TRUE, '2025-09-01 09:15:00'),
(5, 6, 'Duplicate row only appears after refreshing the page.', FALSE, '2025-08-20 09:35:00'),
(5, 16, 'Bug fixed in results service; verify the dashboard when convenient.', TRUE, '2025-08-22 16:10:00');

-- ------------------------------
-- Support Request Status Changes (Audit Log)
-- ------------------------------
INSERT INTO Support_Request_Status_Changes (request_id, changed_by, old_status, new_status, comment_id, changed_at) VALUES
-- Request 2: Morgan took the request (new → open)
(2, 16, 'new', 'open', NULL, '2025-09-05 11:20:30'),
-- Request 3: Morgan took the request (new → open)
(3, 16, 'new', 'open', NULL, '2025-09-04 18:11:00'),
-- Request 4: Morgan took the request (new → open)
(4, 16, 'new', 'open', NULL, '2025-08-29 08:00:00'),
-- Request 4: Morgan changed to stalled (open → stalled)
(4, 16, 'open', 'stalled', NULL, '2025-09-03 13:10:00'),
-- Request 5: Morgan took the request (new → open)
(5, 16, 'new', 'open', NULL, '2025-08-20 09:36:00'),
-- Request 5: Morgan resolved with comment (open → resolved) - references comment_id 6
(5, 16, 'open', 'resolved', 6, '2025-08-22 16:15:00');

-- ------------------------------
-- Notifications
-- ------------------------------
INSERT INTO Notifications (user_id, type, reference_id, message, is_read, created_at) VALUES
-- Notification to Bob (3) when request 2 was taken by Morgan
(3, 'request_assigned', 2, 'Your support request #2 has been taken by Morgan Reeves', TRUE, '2025-09-05 11:20:30'),
-- Notification to Bob (3) when request 2 status changed to open
(3, 'request_status_changed', 2, 'Your support request #2 status changed to Open', TRUE, '2025-09-05 11:20:30'),
-- Notification to Carol (4) when request 3 was taken
(4, 'request_assigned', 3, 'Your support request #3 has been taken by Morgan Reeves', TRUE, '2025-09-04 18:11:00'),
-- Notification to Carol (4) when request 3 status changed to open
(4, 'request_status_changed', 3, 'Your support request #3 status changed to Open', TRUE, '2025-09-04 18:11:00'),
-- Notification to Dave (5) when request 4 was taken
(5, 'request_assigned', 4, 'Your support request #4 has been taken by Morgan Reeves', TRUE, '2025-08-29 08:00:00'),
-- Notification to Dave (5) when request 4 changed to stalled
(5, 'request_status_changed', 4, 'Your support request #4 status changed to Stalled', FALSE, '2025-09-03 13:10:00'),
-- Notification to Emma (6) when request 5 was taken
(6, 'request_assigned', 5, 'Your support request #5 has been taken by Morgan Reeves', TRUE, '2025-08-20 09:36:00'),
-- Notification to Emma (6) when request 5 was resolved
(6, 'request_status_changed', 5, 'Your support request #5 status changed to Resolved', FALSE, '2025-08-22 16:15:00'),
-- Notification to Morgan (16) for new comment on request 2
(16, 'request_comment', 2, 'Bob Jones added a comment to request #2', TRUE, '2025-09-05 11:22:00'),
-- Notification to Morgan (16) for new comment on request 3
(16, 'request_comment', 3, 'Carol Smith added a comment to request #3', TRUE, '2025-09-04 18:12:00');
