-- Migration script to add 'support_technician' role to existing Users table
-- This script should be run on existing databases to update the global_role ENUM

USE activeloop;

-- Alter the Users table to add 'support_technician' to the global_role ENUM
ALTER TABLE Users
MODIFY COLUMN global_role ENUM('super_admin', 'participant', 'support_technician') NOT NULL DEFAULT 'participant';
