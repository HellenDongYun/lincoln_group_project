USE activeloop;

-- Add 'cancelled' to Support_Requests status ENUM
ALTER TABLE Support_Requests
MODIFY COLUMN status ENUM('new','open','stalled','resolved','cancelled') NOT NULL DEFAULT 'new';

-- Add 'cancelled' to Support_Request_Status_Changes old_status ENUM
ALTER TABLE Support_Request_Status_Changes
MODIFY COLUMN old_status ENUM('new','open','stalled','resolved','cancelled') NOT NULL;

-- Add 'cancelled' to Support_Request_Status_Changes new_status ENUM
ALTER TABLE Support_Request_Status_Changes
MODIFY COLUMN new_status ENUM('new','open','stalled','resolved','cancelled') NOT NULL;