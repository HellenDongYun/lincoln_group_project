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
  gender ENUM('male', 'female', 'other') DEFAULT NULL,
  age INT DEFAULT NULL,
  age_group VARCHAR(20)
    GENERATED ALWAYS AS (
      CASE
        WHEN age < 18 THEN 'Under 18'
        WHEN age BETWEEN 18 AND 29 THEN '18-29'
        WHEN age BETWEEN 30 AND 44 THEN '30-44'
        WHEN age >= 45 THEN '45+'
        ELSE 'Unknown'
      END
    ) STORED,
  town VARCHAR(100),
  global_role ENUM('super_admin','participant','support_technician') NOT NULL DEFAULT 'participant',
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
  group_role ENUM('manager','member') NOT NULL DEFAULT 'member',
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
  rejection_reason TEXT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  reviewed_at TIMESTAMP NULL,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (group_id) REFERENCES Community_Groups(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (reviewed_by) REFERENCES Users(id) ON DELETE SET NULL ON UPDATE CASCADE,
  UNIQUE KEY unique_user_group_pending (user_id, group_id, status)
);

-- Achievement system -------------------------------------------------------

CREATE TABLE Achievements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  description TEXT,
  points_reward INT NOT NULL DEFAULT 0
);

CREATE TABLE Challenges (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL UNIQUE,
  description TEXT,
  target_metric VARCHAR(100) NOT NULL,
  target_value INT NOT NULL,
  timeframe_days INT NULL,
  achievement_id_reward INT NOT NULL,
  FOREIGN KEY (achievement_id_reward) REFERENCES Achievements(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE User_Achievements (
  user_id INT NOT NULL,
  achievement_id INT NOT NULL,
  earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, achievement_id),
  FOREIGN KEY (user_id) REFERENCES Users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (achievement_id) REFERENCES Achievements(id)
    ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_challenges_reward ON Challenges(achievement_id_reward);
CREATE INDEX idx_user_achievements_earned ON User_Achievements(earned_at);
ALTER TABLE Group_Applications
ADD COLUMN application_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;


-- Audit trail for user status changes (deactivations/reactivations)
CREATE TABLE User_Status_Audit (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  new_status ENUM('active','inactive') NOT NULL,
  reason TEXT NULL,
  changed_by INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (changed_by) REFERENCES Users(id) ON DELETE SET NULL ON UPDATE CASCADE
);


-- Support Requests for Helpdesk System------ujyh7
CREATE TABLE Support_Requests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  issue_type ENUM('technical','account','event','group','volunteer','bug','other') NOT NULL,
  subject VARCHAR(200) NOT NULL,
  description TEXT NOT NULL,
  screenshot_path VARCHAR(500) NULL,
  status ENUM('new','open','stalled','resolved','cancelled') NOT NULL DEFAULT 'new',
  priority ENUM('low','medium','high') NOT NULL DEFAULT 'medium',
  assigned_to INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (assigned_to) REFERENCES Users(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Support Request Comments for communication between users and support staff
CREATE TABLE Support_Request_Comments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  request_id INT NOT NULL,
  user_id INT NOT NULL,
  comment TEXT NOT NULL,
  is_staff_reply BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (request_id) REFERENCES Support_Requests(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Status Change Audit Log for Support Requests
CREATE TABLE Support_Request_Status_Changes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  request_id INT NOT NULL,
  changed_by INT NOT NULL,
  old_status ENUM('new','open','stalled','resolved','cancelled') NOT NULL,
  new_status ENUM('new','open','stalled','resolved','cancelled') NOT NULL,
  comment_id INT NULL,
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (request_id) REFERENCES Support_Requests(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (changed_by) REFERENCES Users(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (comment_id) REFERENCES Support_Request_Comments(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Notifications for support request updates
CREATE TABLE Notifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  type ENUM('request_assigned','request_status_changed','request_comment','request_dropped','group_join_approved','group_join_rejected') NOT NULL,
  reference_id INT NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE ON UPDATE CASCADE
);
