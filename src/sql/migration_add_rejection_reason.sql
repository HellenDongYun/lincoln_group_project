USE activeloop;

-- Add rejection_reason column to Group_Join_Requests table
ALTER TABLE Group_Join_Requests
ADD COLUMN rejection_reason TEXT NULL AFTER reviewed_by;

-- Add new notification types for group join requests
ALTER TABLE Notifications
MODIFY COLUMN type ENUM('request_assigned','request_status_changed','request_comment','request_dropped','group_join_approved','group_join_rejected') NOT NULL;
