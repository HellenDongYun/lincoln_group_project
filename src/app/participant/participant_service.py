import datetime
from src.app.participant.participant_repository import ParticipantRepository
from collections import defaultdict
from datetime import timedelta

class ParticipantService:
    def __init__(self):
        self.participant_repository = ParticipantRepository()
    
    def get_upcoming_events(self, participant_id):
        """Get all upcoming events that the participant is not already registered for"""
        return self.participant_repository.get_upcoming_events(participant_id)
    
    def get_my_registrations(self, participant_id):
        """Get events that the participant is registered for"""
        return self.participant_repository.get_my_registrations(participant_id)
    
    def get_my_race_results(self, participant_id):
        """Get participant's past race results"""
        return self.participant_repository.get_my_race_results(participant_id)
    
    def register_for_event(self, participant_id, event_id):
        """Register participant for an event"""
        return self.participant_repository.register_for_event(participant_id, event_id)
    
    def cancel_registration(self, participant_id, event_id):
        """Cancel participant registration for an event"""
        return self.participant_repository.cancel_registration(participant_id, event_id)


    def get_participant_applications(
        self, status="all", page=1, per_page=5, participant_id=None
    ):
        """Get participant applications details"""
        return self.participant_repository.show_application(
            status=status,
            page=page,
            per_page=per_page,
            participant_id=participant_id,
        )


    def submit_create_group_application(
        self, participant_id, name, town, visibility, description
    ):
        """Get participant applications details"""
        if not name or not town or not visibility:
            raise ValueError("Group name, location, and visibility are required.")

        if visibility not in ["public", "private"]:
            raise ValueError("Invalid visibility option.")

        return self.participant_repository.create_group_application(
            participant_id, name, description, town, visibility
        )

    def get_application_by_id(self, participant_id, application_id):
        return self.participant_repository.get_application_by_id(
            participant_id, application_id
        )

    def update_group_application(
        self, participant_id, application_id, name, town, visibility, description
    ):
        return self.participant_repository.update_group_application(
            participant_id, application_id, name, town, visibility, description
        )
    
    
    def get_rewards_dashboard(self, participant_id):
        """Return achievements, challenges, and summary metrics for a participant."""
        achievements = self.participant_repository.get_achievements_for_user(participant_id)
        challenges = self.participant_repository.get_challenges_for_user(participant_id)

        total_achievements = len(achievements)
        earned_count = sum(1 for achievement in achievements if achievement.get("earned"))
        total_points = sum(
            achievement.get("points_reward", 0)
            for achievement in achievements
            if achievement.get("earned")
        )
        progress = round((earned_count / total_achievements) * 100, 1) if total_achievements else 0

        total_challenges = len(challenges)
        completed_challenges = sum(1 for challenge in challenges if challenge.get("earned"))
        active_challenges = total_challenges - completed_challenges

        return {
            "achievements": achievements,
            "challenges": challenges,
            "summary": {
                "total_points": total_points,
                "total_achievements": total_achievements,
                "earned_count": earned_count,
                "progress_percent": progress,
                "completed_challenges": completed_challenges,
                "active_challenges": active_challenges,
                "total_challenges": total_challenges,
            },
        }

    def delete_group_application(self, participant_id, application_id):
        return self.participant_repository.delete_group_application(
            participant_id, application_id
        )
    def delete_group_application(self,participant_id, application_id):
        return self.participant_repository.delete_group_application(participant_id, application_id, )
    
    def get_all_eventresults_for_participant(self,participant_id):
        return self.participant_repository.get_all_eventresults_for_participant(participant_id ) 
    
    
    def get_participant_result_for_event (self, participant_id, event_id,search_name=None):
        return self.participant_repository.get_participant_result_for_event(participant_id, event_id,search_name)
    
    def get_participant_result_for_event_statistics(self,event_id,):
        return self.participant_repository.get_participant_result_for_event_statistics(event_id)
    def get_event_participant_durations(self, event_id,gender=None, age_group=None):
        return self.participant_repository.get_event_participant_durations(event_id,gender=gender, age_group=age_group)
       
    
    
    def get_all_events_for_participant(self, participant_id):
        return self.participant_repository.get_all_events_for_participant(participant_id)
    def get_event_details_for_participant(self, participant_id, event_id):
        return self.participant_repository.get_event_details_for_participant(participant_id,event_id)
    def get_event_summary_split(self, participant_id):
        events = self.participant_repository.get_personal_event_analysis_for_participant(participant_id)
        if not events:
            return {"event": [], "result": {}, "meta": {}}

        durations = [e["total_seconds"] for e in events if e["total_seconds"] is not None]

        # results
        best_time = min(durations)
        worst_time = max(durations)
        avg_time = sum(durations) / len(durations)

        best_event = next(e for e in events if e["total_seconds"] == best_time)
        worst_event = next(e for e in events if e["total_seconds"] == worst_time)

        result = {
            "average": {
            "value": self._format_seconds(avg_time),
            "event_name": None,
            "event_type": "Average",
            "user_rank": None,
            "event_date": None
            },
            "fastest": {
                "value": self._format_seconds(best_time),
                "event_name": best_event["event_name"],
                "event_type": best_event["event_type"],
                "user_rank": best_event["user_rank"],
                "event_date": best_event["event_date"].strftime('%d/%m/%Y')
            },
            "slowest": {
                "value": self._format_seconds(worst_time),
                "event_name": worst_event["event_name"],
                "event_type": worst_event["event_type"],
                "user_rank": worst_event["user_rank"],
                "event_date": worst_event["event_date"].strftime('%d/%m/%Y')
            }
        }

        # trend
        recent_time = events[0]["total_seconds"]
        previous_time = events[1]["total_seconds"] if len(events) > 1 else None

        if previous_time is not None:
            delta = recent_time - previous_time
            trend = "increase" if delta < 0 else "decrease"
            change = abs(delta)
        else:
            trend = "remain the same"
            change = 0

        #finishing rate
        valid_events = [e for e in events if e["total_seconds"] is not None]
        completion_rate = len(valid_events) / len(events) * 100

        meta = {
            "total_events": len(events),
            "latest_rank": events[0]["user_rank"],
            "latest_event_name": events[0]["event_name"],
            "trend": trend,
            "change": self._format_seconds(change),
            "completion_rate": round(completion_rate, 1)
        }

        return {
            "event": events,
            "result": result,
            "meta": meta
        }

    def _format_seconds(self, seconds):
        return str(datetime.timedelta(seconds=int(seconds)))
    def format_seconds(self,seconds):
        if seconds is None:
            return None
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02}:{minutes:02}:{secs:02}"
    def get_user_group_membership_results(self, participant_id):
        rows = self.participant_repository.get_user_group_membership_results(participant_id)

        grouped = {}
        for row in rows:
            group_id = row["group_id"]

            # initialize group info
            if group_id not in grouped:
                grouped[group_id] = {
                    "group_id": group_id,
                    "group_name": row["group_name"],
                    "group_description": row.get("group_description"),
                    "events": []
                }

            # add event info（include top3）
            grouped[group_id]["events"].append({
                "event_id": row["event_id"],
                "event_name": row["event_name"],
                "event_type": row["event_type"],
                "town": row["town"],
                "event_date": row["event_date"],
                "max_participants": row["max_participants"],
                "total_participants": row["total_participants"],

                # current user result
                "user_start_time": row["user_start_time"],
                "user_end_time": row["user_end_time"],
                "user_total_seconds": row["user_total_seconds"],
                "user_total_time_str": self.format_seconds(row["user_total_seconds"]),
                "user_rank": row["user_rank"],

                # 🏆 top 3 info
                "first_user_name": row["first_user_name"],
                "first_user_time": row["first_user_time"],
                "first_user_time_str": self.format_seconds(row["first_user_time"]),
                "second_user_name": row["second_user_name"],
                "second_user_time": row["second_user_time"],
                "second_user_time_str": self.format_seconds(row["second_user_time"]),
                "third_user_name": row["third_user_name"],
                "third_user_time": row["third_user_time"],
                "third_user_time_str": self.format_seconds(row["third_user_time"])
            })

        
        return grouped
    
    
    def get_event_top3_grouped(self,event_id, group_by="gender"):
        rows = self.participant_repository.get_top3_by_group(event_id, group_by)
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["group_label"]].append({
                "name": row["full_name"],
                "duration": str(timedelta(seconds=row["total_seconds"]))
            })

        result = {}
        for label, participants in grouped.items():
            result[label] = {
                "group_size": len(participants),
                "top3": [
                    {**p, "rank": i + 1}
                    for i, p in enumerate(participants[:3])
                ]
            }
        return result
    
    def get_user_event_chart_data(self,user_id, event_type=None):
        rows = self.participant_repository.get_user_event_durations(user_id, event_type)

        chart_data = {
            "labels": [],
            "durations": []
        }

        for row in rows:
            chart_data["labels"].append(row["datetime"].strftime("%d/%m/%Y"))
            chart_data["durations"].append(row["total_seconds"]) 

        return chart_data

