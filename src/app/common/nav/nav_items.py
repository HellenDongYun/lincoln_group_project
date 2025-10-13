from flask import url_for

from src.app.common.nav.encode import encode_id
from src.app.group.group_service import GroupService
from src.app.user.user import GlobalRole


def left_nav_items(user_id: int, user_role: GlobalRole):
    """Build the primary navigation links for the current user."""
    nav_items = []

    if not user_id:
        nav_items.append(
            {"label": "Race Results", "url": url_for("results.public_results")}
        )
        nav_items.append({"label": "Events", "url": url_for("app.get_events")})
        return nav_items

    if user_role == GlobalRole.SUPER_ADMIN:
        encoded_admin_id = encode_id(user_id)
        nav_items.append(
            {
                "label": "Admin Dashboard",
                "url": url_for(
                    "admin.admin_dashboard", encoded_admin_id=encoded_admin_id
                ),
            }
        )
        nav_items.append({"label": "Race Results", "url": url_for("results.public_results")})
        nav_items.append(
            {"label": "Record Completion Time", "url": url_for("results.record_time")}
        )
        nav_items.append({"label": "Events", "url": url_for("app.get_events")})

    elif user_role == GlobalRole.PARTICIPANT:
        encoded_participant_id = encode_id(user_id)
        nav_items.append(
            {
                "label": "My Dashboard",
                "url": url_for(
                    "participant.dashboard",
                    encoded_participant_id=encoded_participant_id,
                ),
            }
        )
        nav_items.append(
            {
                "label": "Rewards",
                "url": url_for(
                    "participant.rewards",
                    encoded_participant_id=encoded_participant_id,
                ),
            }
        )

        managed_groups = GroupService.get_user_managed_groups(user_id)
        if managed_groups:
            nav_items.append(
                {
                    "label": "Manager Dashboard",
                    "url": url_for(
                        "groups.manager_dashboard",
                        group_id=managed_groups[0]["id"],
                    ),
                }
            )

        nav_items.append(
            {"label": "Find Groups & Events", "url": url_for("groups.participant_search")}
        )

        if GroupService.user_has_group_memberships(user_id):
            nav_items.append(
                {
                    "label": "Record Completion Time",
                    "url": url_for("results.record_time"),
                }
            )
            nav_items.append({
                "label": "Manager Dashboard",
                "url": url_for('groups.manager_dashboard', group_id=managed_groups[0]['id'])
            })
            nav_items.append({
                "label": "Support Queue",
                "url": url_for('support.support_queue')
            })
        nav_items.append({
            "label": "Find Groups & Events",
            "url": url_for('groups.participant_search')
        })
        nav_items.append({
            "label": "My Applications",
            "url": url_for('participant.myapplications', encoded_participant_id=encoded_participant_id)
        })
        nav_items.append({
            "label": "Results",
            "url": url_for('participant.myresults', encoded_participant_id=encoded_participant_id)
        })
      

        nav_items.append({
            "label": "Help & Support",
            "url": url_for('support.my_requests')
        })

    # SUPPORT_TECHNICIAN
    elif user_role == GlobalRole.SUPPORT_TECHNICIAN and user_id:
        nav_items.append({
            "label": "Support Queue",
            "url": url_for('support.support_queue')
        })
        nav_items.append({
            "label": "Events",
            "url": url_for('app.get_events')
        })
        nav_items.append({
            "label": "Help & Support",
            "url": url_for('support.my_requests')
        })

        nav_items.append(
            {
                "label": "My Applications",
                "url": url_for(
                    "participant.myapplications",
                    encoded_participant_id=encoded_participant_id,
                ),
            }
        )

    return nav_items


def right_nav_items(user_id: int, user_role: GlobalRole):
    """Build the secondary navigation (account) links for the current user."""
    if not user_id:
        return []

    return [
        {"label": "Settings", "url": url_for("app.settings")},
        {"label": "Log out", "url": url_for("app.logout")},
    ]
