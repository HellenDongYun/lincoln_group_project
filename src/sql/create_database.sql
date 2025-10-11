-- SQL script to create the activeloop database schema
DROP DATABASE IF EXISTS activeloop;
CREATE DATABASE activeloop;
USE activeloop;

-- Core Users & Roles
-- Global roles simplified to: super_admin, participant
-- (group-level manager/volunteer responsibilities handled via membership tables)
CREATE TABLE Users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  town VARCHAR(100),
  global_role ENUM('super_admin','participant') NOT NULL DEFAULT 'participant',
  status ENUM('active','inactive') NOT NULL DEFAULT 'active'
);

-- visibility: public groups discoverable to visitors; private groups hidden except to members/admins

CREATE TABLE Community_Groups (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL UNIQUE,
  description TEXT,
  town VARCHAR(100),
  visibility ENUM('public','private') NOT NULL DEFAULT 'public',
  status ENUM('active','inactive','pending') NOT NULL DEFAULT 'active',
  created_by INT NOT NULL,
  FOREIGN KEY (created_by) REFERENCES Users(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Applications to create new groups submitted by participants; reviewed by super admin
CREATE TABLE Group_Applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  applicant_id INT NOT NULL,
  proposed_name VARCHAR(150) NOT NULL,
  proposed_description TEXT,
  proposed_town VARCHAR(100),
  visibility ENUM('public','private') NOT NULL DEFAULT 'public',
  status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  decision_by INT NULL,
  FOREIGN KEY (applicant_id) REFERENCES Users(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (decision_by) REFERENCES Users(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Memberships linking users to groups; role reflects group-level responsibility
CREATE TABLE Group_Memberships (
  group_id INT NOT NULL,
  user_id INT NOT NULL,
  group_role ENUM('manager','volunteer','member') NOT NULL DEFAULT 'member',
  member_status ENUM('active','inactive') NOT NULL DEFAULT 'active',
  PRIMARY KEY (group_id, user_id),
  FOREIGN KEY (group_id) REFERENCES Community_Groups(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_group_memberships_user ON Group_Memberships(user_id);
CREATE INDEX idx_groups_visibility ON Community_Groups(visibility);
CREATE INDEX idx_groups_town ON Community_Groups(town);


-- Events (now owned by a group)
CREATE TABLE Events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  group_id INT NOT NULL,
  datetime DATETIME NOT NULL,
  town VARCHAR(100) NOT NULL,
  name VARCHAR(100) NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  description TEXT,
  max_participants INT NOT NULL,
  visibility ENUM('public','private') NOT NULL DEFAULT 'public',
  created_by INT NOT NULL,
  FOREIGN KEY (group_id) REFERENCES Community_Groups(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (created_by) REFERENCES Users(id) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE INDEX idx_events_group ON Events(group_id);
CREATE INDEX idx_events_datetime ON Events(datetime);
CREATE INDEX idx_events_town ON Events(town);


-- Volunteer Tasks (formerly volunteer roles; global catalogue)
CREATE TABLE Volunteer_Tasks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE,
  description VARCHAR(255)
);

-- Planned task capacity per event
CREATE TABLE Event_Task_Vacancies (
  event_id INT NOT NULL,
  task_id INT NOT NULL,
  spots INT NOT NULL,
  PRIMARY KEY (event_id, task_id),
  FOREIGN KEY (event_id) REFERENCES Events(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (task_id) REFERENCES Volunteer_Tasks(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Task assignments (any participant who is a member of the event's group)
CREATE TABLE Event_Task_Assignments (
  event_id INT NOT NULL,
  task_id INT NOT NULL,
  user_id INT NOT NULL,
  PRIMARY KEY (event_id, task_id, user_id),
  FOREIGN KEY (event_id) REFERENCES Events(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (task_id) REFERENCES Volunteer_Tasks(id) ON DELETE RESTRICT ON UPDATE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Participant registrations (attendees) independent of volunteer tasks
CREATE TABLE Event_Participants (
  event_id INT NOT NULL,
  user_id INT NOT NULL,
  status ENUM('registered','cancelled') NOT NULL DEFAULT 'registered',
  PRIMARY KEY (event_id, user_id),
  FOREIGN KEY (event_id) REFERENCES Events(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Performance results (optional for timed events)
CREATE TABLE Event_Results (
  event_id INT NOT NULL,
  user_id INT NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  total_seconds INT GENERATED ALWAYS AS (TIMESTAMPDIFF(SECOND, start_time, end_time)) STORED,
  PRIMARY KEY (event_id, user_id),
  CHECK (end_time >= start_time),
  FOREIGN KEY (event_id) REFERENCES Events(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Group Join Requests for private group access
CREATE TABLE Group_Join_Requests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  group_id INT NOT NULL,
  message TEXT,
  status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  reviewed_by INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  reviewed_at TIMESTAMP NULL,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (group_id) REFERENCES Community_Groups(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (reviewed_by) REFERENCES Users(id) ON DELETE SET NULL ON UPDATE CASCADE,
  UNIQUE KEY unique_user_group_pending (user_id, group_id, status)
);
ALTER TABLE Group_Applications
ADD COLUMN application_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE Users
ADD COLUMN gender ENUM('male', 'female', 'other') DEFAULT NULL AFTER last_name,
ADD COLUMN age INT DEFAULT NULL AFTER gender,
ADD COLUMN age_group VARCHAR(20)
GENERATED ALWAYS AS (
    CASE
        WHEN age < 18 THEN 'Under 18'
        WHEN age BETWEEN 18 AND 29 THEN '18-29'
        WHEN age BETWEEN 30 AND 44 THEN '30-44'
        WHEN age >= 45 THEN '45+'
        ELSE 'Unknown'
    END
) STORED;

