DROP DATABASE IF EXISTS activeloop;
CREATE DATABASE activeloop;

USE activeloop;

-- Users
CREATE TABLE Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    town VARCHAR(100),
    role ENUM('participant','volunteer','admin') NOT NULL DEFAULT 'participant',
    status ENUM('active','inactive') NOT NULL DEFAULT 'active'
);

-- Events
CREATE TABLE Events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    datetime DATETIME NOT NULL,
    town VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    description TEXT,
    max_participants INT NOT NULL
);

-- Volunteer_Roles
CREATE TABLE Volunteer_Roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255)
);

-- Vacancies
CREATE TABLE Vacancies (
    event_id INT NOT NULL,
    role_id INT NOT NULL,
    spots INT NOT NULL,
    PRIMARY KEY (event_id, role_id),
    FOREIGN KEY (event_id) REFERENCES Events(id)
       ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (role_id) REFERENCES Volunteer_Roles(id)
       ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Event_Volunteers
CREATE TABLE Event_Volunteers (
    event_id INT NOT NULL,
    role_id INT NOT NULL,
    volunteer_id INT NOT NULL,
    PRIMARY KEY (event_id, role_id, volunteer_id),
    FOREIGN KEY (event_id) REFERENCES Events(id)
      ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (role_id) REFERENCES Volunteer_Roles(id)
      ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (volunteer_id) REFERENCES Users(id)
      ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Participants
CREATE TABLE Participants (
    event_id INT NOT NULL,
    participant_id INT NOT NULL,
    status ENUM('registered','cancelled') NOT NULL DEFAULT 'registered',
    PRIMARY KEY (event_id, participant_id),
    FOREIGN KEY (event_id) REFERENCES Events(id)
      ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES Users(id)
      ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Race_Results
CREATE TABLE Race_Results (
    event_id INT NOT NULL,
    participant_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    total_seconds INT GENERATED ALWAYS AS (TIMESTAMPDIFF(SECOND, start_time, end_time)) STORED,
    PRIMARY KEY (event_id, participant_id),
    CHECK (end_time >= start_time),
    FOREIGN KEY (event_id) REFERENCES Events(id)
     ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES Users(id)
     ON DELETE RESTRICT ON UPDATE CASCADE
);
