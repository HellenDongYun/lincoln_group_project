import csv
import io
from datetime import datetime, timedelta
from src.app.results.results_repository import ResultsRepository


class ResultsService:
    def __init__(self):
        self.results_repository = ResultsRepository()
    
    def get_events_with_results(self):
        """Get all events that have race results"""
        return self.results_repository.get_events_with_results()
    
    def get_all_events(self):
        """Get all events for the upload dropdown"""
        return self.results_repository.get_all_events()
    
    def get_event_details(self, event_id):
        """Get details for a specific event"""
        return self.results_repository.get_event_details(event_id)
    
    def get_event_results(self, event_id):
        """Get race results for a specific event"""
        return self.results_repository.get_event_results(event_id)
    
    def check_existing_results(self, event_id):
        """Check if event already has results"""
        return self.results_repository.check_existing_results(event_id)
    
    def get_event_result_summary(self, event_id):
        """Get summary of existing results for confirmation"""
        return self.results_repository.get_event_result_summary(event_id)
    
    def remove_event_results(self, event_id):
        """Remove all existing results for an event"""
        return self.results_repository.remove_event_results(event_id)
    
    def process_csv_results(self, event_id, csv_content, overwrite=False):
        """Process CSV file and save results to database with comprehensive validation"""
        try:
            # Check if event already has results
            existing_count = self.check_existing_results(event_id)
            
            if existing_count > 0 and not overwrite:
                return False, f"Event already has {existing_count} race results. Please confirm overwrite.", {
                    'processed': 0, 'errors': 0, 'events_affected': 1, 'total_rows': 0
                }
            
            # Parse CSV content first to validate format and collect statistics
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Validate headers
            required_headers = {'participant_id', 'start_time', 'end_time'}
            alternative_headers = {'email', 'start_time', 'end_time'}
            
            if not (required_headers.issubset(csv_reader.fieldnames) or 
                   alternative_headers.issubset(csv_reader.fieldnames)):
                missing = required_headers - set(csv_reader.fieldnames or [])
                alt_missing = alternative_headers - set(csv_reader.fieldnames or [])
                return False, f"Missing required headers. Need either {required_headers} or {alternative_headers}", {
                    'processed': 0, 'errors': 1, 'events_affected': 0, 'total_rows': 0
                }
            
            # First pass - validate all rows without saving anything (all-or-nothing approach)
            validation_errors = []
            unregistered_participants = []  # Track unregistered participants separately
            valid_rows = []
            total_rows = 0
            
            for row_num, row in enumerate(csv_reader, start=2):
                total_rows += 1
                row_errors = []
                participant_info = None
                
                try:
                    # Validate participant
                    participant_id = None
                    participant_email = None
                    
                    # Method 1: Try participant_id column
                    if 'participant_id' in row and row['participant_id'].strip():
                        try:
                            participant_id = int(row['participant_id'])
                            # Validate that this participant exists
                            participant_info = self.results_repository.get_participant_info(participant_id)
                            if not participant_info:
                                row_errors.append("invalid participant ID")
                        except ValueError:
                            row_errors.append("invalid participant ID format")
                    
                    # Method 2: Try email column if participant_id didn't work
                    elif 'email' in row and row['email'].strip():
                        participant_email = row['email'].strip()
                        participant_info = self.results_repository.get_participant_info_by_email(participant_email)
                        if not participant_info:
                            row_errors.append("participant email not found")
                        else:
                            participant_id = participant_info['id']
                    
                    else:
                        row_errors.append("missing participant ID or email")
                    
                    # Validate event registration if participant was found
                    if participant_id and not row_errors:
                        registered = self.results_repository.validate_participant_registered_for_event(event_id, participant_id)
                        if not registered:
                            # Add to unregistered list instead of errors for confirmation
                            unregistered_participants.append({
                                'row': row_num,
                                'participant_id': participant_id,
                                'name': f"{participant_info.get('first_name', '')} {participant_info.get('last_name', '')}".strip(),
                                'email': participant_info.get('email', participant_email or 'Unknown'),
                                'data': row
                            })
                            continue  # Skip time validation for unregistered participants
                    
                    # Validate required fields
                    start_time_str = row.get('start_time', '').strip()
                    end_time_str = row.get('end_time', '').strip()
                    
                    if not start_time_str:
                        row_errors.append("missing start_time")
                    if not end_time_str:
                        row_errors.append("missing end_time")
                    
                    # Validate time formats
                    start_time = None
                    end_time = None
                    
                    if start_time_str:
                        start_time = self._parse_time(start_time_str)
                        if not start_time:
                            row_errors.append("invalid start_time format")
                    
                    if end_time_str:
                        end_time = self._parse_time(end_time_str)
                        if not end_time:
                            row_errors.append("invalid end_time format")
                    
                    # Validate end_time >= start_time
                    if start_time and end_time and end_time <= start_time:
                        row_errors.append("end_time must be after start_time")
                    
                    # If no errors, add to valid rows
                    if not row_errors:
                        valid_rows.append({
                            'participant_id': participant_id,
                            'start_time': start_time,
                            'end_time': end_time
                        })
                    else:
                        validation_errors.extend([f"Row {row_num}: {error}" for error in row_errors])
                        
                except Exception as e:
                    validation_errors.append(f"Row {row_num}: {str(e)}")
            
            # Prepare detailed statistics and error information
            stats = {
                'processed': 0,
                'errors': len(validation_errors),
                'unregistered': len(unregistered_participants),
                'valid_rows': len(valid_rows),
                'events_affected': 1 if not validation_errors else 0,
                'total_rows': total_rows,
                'validation_errors': validation_errors,
                'unregistered_participants': unregistered_participants
            }
            
            # Check if we need confirmation for unregistered participants
            if unregistered_participants and not validation_errors:
                return False, "UNREGISTERED_CONFIRMATION", stats
            
            # All-or-nothing: if any validation errors, don't save anything
            if validation_errors:
                error_summary = f"Validation failed: {len(validation_errors)} row(s) have issues. No results were published."
                return False, error_summary, stats
            
            # If overwriting, remove existing results first
            if existing_count > 0 and overwrite:
                removed_count = self.remove_event_results(event_id)
            
            # Second pass - save all valid rows
            processed_count = 0
            save_errors = []
            
            for row_data in valid_rows:
                try:
                    success = self.results_repository.save_race_result(
                        event_id, 
                        row_data['participant_id'], 
                        row_data['start_time'], 
                        row_data['end_time']
                    )
                    if success:
                        processed_count += 1
                    else:
                        save_errors.append(f"Failed to save result for participant {row_data['participant_id']}")
                except Exception as e:
                    save_errors.append(f"Error saving participant {row_data['participant_id']}: {str(e)}")
            
            # Update final statistics
            stats['processed'] = processed_count
            
            if save_errors:
                error_message = f"Processed {processed_count} results with {len(save_errors)} save errors"
                return True, error_message, stats
            else:
                success_message = f"Successfully processed all {processed_count} results"
                return True, success_message, stats
                
        except Exception as e:
            return False, f"CSV processing error: {str(e)}", {
                'processed': 0, 'errors': 1, 'events_affected': 0, 'total_rows': 0,
                'validation_errors': [str(e)], 'unregistered_participants': []
            }
    
    def process_csv_results_with_unregistered(self, event_id, csv_content, overwrite=False, include_unregistered=False):
        """Process CSV with option to include unregistered participants"""
        try:
            # Check if event already has results
            existing_count = self.check_existing_results(event_id)
            
            if existing_count > 0 and not overwrite:
                return False, f"Event already has {existing_count} race results. Please confirm overwrite.", {
                    'processed': 0, 'errors': 0, 'events_affected': 1, 'total_rows': 0,
                    'validation_errors': [], 'unregistered_participants': []
                }
            
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Validate headers
            required_headers = {'participant_id', 'start_time', 'end_time'}
            alternative_headers = {'email', 'start_time', 'end_time'}
            
            if not (required_headers.issubset(csv_reader.fieldnames) or 
                   alternative_headers.issubset(csv_reader.fieldnames)):
                return False, f"Missing required headers. Need either {required_headers} or {alternative_headers}", {
                    'processed': 0, 'errors': 1, 'events_affected': 0, 'total_rows': 0,
                    'validation_errors': ['Invalid CSV headers'], 'unregistered_participants': []
                }
            
            # Process all rows
            validation_errors = []
            valid_rows = []
            skipped_unregistered = []
            total_rows = 0
            
            for row_num, row in enumerate(csv_reader, start=2):
                total_rows += 1
                row_errors = []
                participant_info = None
                
                try:
                    # Get participant info
                    participant_id = None
                    if 'participant_id' in row and row['participant_id'].strip():
                        try:
                            participant_id = int(row['participant_id'])
                            participant_info = self.results_repository.get_participant_info(participant_id)
                            if not participant_info:
                                row_errors.append("invalid participant ID")
                        except ValueError:
                            row_errors.append("invalid participant ID format")
                    elif 'email' in row and row['email'].strip():
                        participant_email = row['email'].strip()
                        participant_info = self.results_repository.get_participant_info_by_email(participant_email)
                        if not participant_info:
                            row_errors.append("participant email not found")
                        else:
                            participant_id = participant_info['id']
                    else:
                        row_errors.append("missing participant ID or email")
                    
                    # Check registration
                    if participant_id and not row_errors:
                        registered = self.results_repository.validate_participant_registered_for_event(event_id, participant_id)
                        if not registered and not include_unregistered:
                            skipped_unregistered.append({
                                'row': row_num,
                                'name': f"{participant_info.get('first_name', '')} {participant_info.get('last_name', '')}".strip(),
                                'email': participant_info.get('email', 'Unknown')
                            })
                            continue
                    
                    # Validate times (same as before)
                    start_time_str = row.get('start_time', '').strip()
                    end_time_str = row.get('end_time', '').strip()
                    
                    if not start_time_str:
                        row_errors.append("missing start_time")
                    if not end_time_str:
                        row_errors.append("missing end_time")
                    
                    start_time = None
                    end_time = None
                    
                    if start_time_str:
                        start_time = self._parse_time(start_time_str)
                        if not start_time:
                            row_errors.append("invalid start_time format")
                    
                    if end_time_str:
                        end_time = self._parse_time(end_time_str)
                        if not end_time:
                            row_errors.append("invalid end_time format")
                    
                    if start_time and end_time and end_time <= start_time:
                        row_errors.append("end_time must be after start_time")
                    
                    # Add to valid rows if no errors
                    if not row_errors:
                        valid_rows.append({
                            'participant_id': participant_id,
                            'start_time': start_time,
                            'end_time': end_time
                        })
                    else:
                        validation_errors.extend([f"Row {row_num}: {error}" for error in row_errors])
                        
                except Exception as e:
                    validation_errors.append(f"Row {row_num}: {str(e)}")
            
            # Statistics
            stats = {
                'processed': 0,
                'errors': len(validation_errors),
                'valid_rows': len(valid_rows),
                'skipped_unregistered': len(skipped_unregistered),
                'events_affected': 1 if not validation_errors else 0,
                'total_rows': total_rows,
                'validation_errors': validation_errors,
                'skipped_unregistered': skipped_unregistered
            }
            
            if validation_errors:
                return False, f"Validation failed: {len(validation_errors)} row(s) have issues.", stats
            
            # Save results
            if existing_count > 0 and overwrite:
                self.remove_event_results(event_id)
            
            processed_count = 0
            for row_data in valid_rows:
                try:
                    success = self.results_repository.save_race_result(
                        event_id, 
                        row_data['participant_id'], 
                        row_data['start_time'], 
                        row_data['end_time']
                    )
                    if success:
                        processed_count += 1
                except Exception as e:
                    validation_errors.append(f"Save error for participant {row_data['participant_id']}: {str(e)}")
            
            stats['processed'] = processed_count
            
            if skipped_unregistered:
                message = f"Successfully processed {processed_count} results. Skipped {len(skipped_unregistered)} unregistered participants."
            else:
                message = f"Successfully processed all {processed_count} results."
                
            return True, message, stats
                
        except Exception as e:
            return False, f"CSV processing error: {str(e)}", {
                'processed': 0, 'errors': 1, 'events_affected': 0, 'total_rows': 0,
                'validation_errors': [str(e)], 'skipped_unregistered': []
            }
    
    def _parse_time(self, time_str):
        """Parse time string in various formats"""
        time_formats = [
            '%H:%M:%S',      # 14:30:45
            '%H:%M',         # 14:30
            '%I:%M:%S %p',   # 2:30:45 PM
            '%I:%M %p',      # 2:30 PM
            '%Y-%m-%d %H:%M:%S',  # 2025-09-07 14:30:45
            '%d/%m/%Y %H:%M:%S',  # 07/09/2025 14:30:45
            '%d/%m/%Y %H:%M',     # 07/09/2025 14:30
        ]
        
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(time_str, fmt)
                # If only time (no date), assume today's date
                if fmt in ['%H:%M:%S', '%H:%M', '%I:%M:%S %p', '%I:%M %p']:
                    today = datetime.now().date()
                    parsed_time = datetime.combine(today, parsed_time.time())
                return parsed_time
            except ValueError:
                continue
        
        return None

    def record_completion_time(self, event_id, participant_id=None, participant_email=None, completion_time=None):
        """Record completion time for a participant using provided completion time"""
        try:
            # Lookup participant by email if ID not provided
            if not participant_id and participant_email:
                participant_info = self.results_repository.get_participant_info_by_email(participant_email)
                if not participant_info:
                    return False, f"Participant with email '{participant_email}' not found."
                participant_id = participant_info['id']
            else:
                # Validate participant exists by ID
                participant_info = self.results_repository.get_participant_info(participant_id)
                if not participant_info:
                    return False, "Invalid participant ID. Participant not found."

            # Validate participant is registered for the event
            is_registered = self.results_repository.validate_participant_registered_for_event(event_id, participant_id)
            if not is_registered:
                return False, f"Participant {participant_info['first_name']} {participant_info['last_name']} is not registered for this event."

            # Get event start time to use as start_time
            event_start_time = self.results_repository.get_event_start_time(event_id)
            if not event_start_time:
                return False, "Event not found or has no start time."

            # Parse completion time input
            if not completion_time:
                return False, "Completion time is required."

            try:
                # Parse time input (HH:MM:SS format) and combine with event date
                time_parts = completion_time.split(':')
                if len(time_parts) == 3:
                    hours, minutes, seconds = map(int, time_parts)
                elif len(time_parts) == 2:
                    hours, minutes = map(int, time_parts)
                    seconds = 0
                else:
                    return False, "Invalid time format. Use HH:MM:SS or HH:MM format."

                # Combine with event date to create full datetime
                event_date = event_start_time.date()
                from datetime import time
                completion_time_obj = datetime.combine(event_date, time(hours, minutes, seconds))

            except ValueError:
                return False, "Invalid time format. Please enter time as HH:MM:SS (e.g., 14:35:20)."

            # Validate that completion time is after event start time
            if completion_time_obj <= event_start_time:
                return False, "Completion time cannot be before the event start time."

            # Save the result
            success = self.results_repository.save_race_result(
                event_id, participant_id, event_start_time, completion_time_obj
            )

            if success:
                participant_name = f"{participant_info['first_name']} {participant_info['last_name']}"
                formatted_completion_time = completion_time_obj.strftime('%H:%M:%S')
                return True, f"Successfully recorded completion time {formatted_completion_time} for {participant_name}."
            else:
                return False, "Failed to save the completion time. Please try again."

        except Exception as e:
            return False, f"Error recording completion time: {str(e)}"

    def _parse_duration(self, duration_str):
        """Parse duration string in MM:SS or HH:MM:SS format and return timedelta"""
        try:
            parts = duration_str.split(':')
            if len(parts) == 2:
                # MM:SS format
                minutes, seconds = map(int, parts)
                return timedelta(minutes=minutes, seconds=seconds)
            elif len(parts) == 3:
                # HH:MM:SS format
                hours, minutes, seconds = map(int, parts)
                return timedelta(hours=hours, minutes=minutes, seconds=seconds)
            else:
                return None
        except ValueError:
            return None
