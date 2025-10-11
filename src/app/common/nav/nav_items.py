from flask import url_for

from src.app.user.user import GlobalRole
from src.app.common.nav.encode import encode_id
def left_nav_items(user_id: int, user_role: GlobalRole):
    nav_items = []
     # if user not logged in 
    if not user_id:
        nav_items.append({
            "label": "Race Results",
            "url": url_for("results.public_results")
        })
        nav_items.append({
            "label": "Events",
            "url": url_for("app.get_events")
        })
        return nav_items
    # SUPER_ADMIN
    if user_role == GlobalRole.SUPER_ADMIN and user_id:
        encoded_admin_id = encode_id(user_id)
        nav_items.append({
            "label": "Admin Dashboard",
            "url": url_for('admin.admin_dashboard', encoded_admin_id=encoded_admin_id)
        })
        nav_items.append({
            "label": "Race Results",
            "url": url_for('results.public_results')
        })
        nav_items.append({
            "label": "Events",
            "url": url_for('app.get_events')
        })

    # PARTICIPANT
    elif user_role == GlobalRole.PARTICIPANT and user_id:
        encoded_participant_id = encode_id(user_id)
        nav_items.append({
            "label": "My Dashboard",
            "url": url_for('participant.dashboard', encoded_participant_id=encoded_participant_id)
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
      

    # if have other roles add more elif

    return nav_items

    """def left_nav_items():
    return [
        {"url": "/", "text": "Home"},
        {"url": "/events", "text": "Events"}
    ]

def right_nav_items():
    return [
        {"url": "/login", "text": "Login"},
        {"url": "/register", "text": "Register"}
    ]
    """
    
    """
    how to use in template
    <nav>
    <div class="left-nav">
        {% for item in left_nav_items %}
            {{ nav_link(item.url, item.text) }} <!-- e.g.: <a href="/events" class="nav-link">Events</a> -->
        {% endfor %}
    </div>
    <div class="right-nav">
        {% for item in right_nav_items %}
            {{ nav_link(item.url, item.text) }}
        {% endfor %}
    </div>
</nav>"""
def right_nav_items(user_id: int, user_role: GlobalRole):

    if not user_id:
        return []

    nav_items = []
    nav_items.append({"label": "Settings", "url": url_for("app.settings")})
    nav_items.append( {"label": "Log out",  "url": url_for("app.logout") })

    return nav_items
