from flask import url_for

from src.app.user.user import GlobalRole
from src.app.common.nav.encode import encode_id
from src.app.group.group_service import GroupService

def left_nav_items(user_id: int, user_role: GlobalRole):

    nav_items = []

    if user_role == GlobalRole.SUPER_ADMIN and user_id:
        encoded_admin_id = encode_id(user_id)
        nav_items.append({
            "label": "Admin Dashboard",
            "url": url_for('admin.admin_dashboard', encoded_admin_id=encoded_admin_id)
        })

    #Race Results for all users 
    nav_items.append({
        "label": "Race Results",
        "url": url_for('results.public_results')
    })
    
    #Events for all users 
    nav_items.append({
        "label": "Events",
        "url": url_for('app.get_events')
    })

    if not user_id:
        return nav_items
      
    if user_role == GlobalRole.PARTICIPANT:
        encoded_participant_id = encode_id(user_id)
        nav_items.append({
            "label": "My Dashboard",
            "url": url_for('participant.dashboard', encoded_participant_id=encoded_participant_id)
        })
        managed_groups = GroupService.get_user_managed_groups(user_id)
        if managed_groups:
            nav_items.append({
                "label": "Manager Dashboard",
                "url": url_for('groups.manager_dashboard', group_id=managed_groups[0]['id'])
            })
        nav_items.append({
            "label": "Find Groups & Events",
            "url": url_for('groups.participant_search')
        })
 
    # Groups navigation for all logged-in users
    if user_id:
        nav_items.append({
            "label": "Community Groups",
            "url": url_for('groups.index')
        })
    
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

    # if user_role == Role.PARTICIPANT:
    #     student = student_service.get_student_by_user_id(user_id)
    #     nav_items.extend([
    #         {
    #             "label": stringcase.pascalcase(student.full_name.split(" ")[0]),
    #             "url": url_for('student.get_student', encoded_student_id=student.encoded_student_id)
    #         }
    #     ])
    #
    # if user_role == Role.VOLUNTEER:
    #     employer = employer_service.get_employer_by_user_id(user_id)
    #     nav_items.extend([
    #         {"label": employer.company_name,
    #          "url": url_for('employer.get_employer', encoded_employer_id=employer.encoded_employer_id)}
    #     ])
    #
    # if user_role == Role.ADMIN:
    #     admin = admin_service.get_admin_by_admin_id(user_id)
    #     nav_items.extend([
    #         {
    #             "label": stringcase.pascalcase(admin.full_name.split(" ")[0]),
    #             "url": url_for('admin.get_admin', encoded_admin_id=admin.encoded_admin_id)
    #         }
    #         # {"label": "Settings", "url": url_for('admin.settings')}
    #     ])

    nav_items.append({"label": "Settings", "url": url_for("app.settings")})
    nav_items.append( {"label": "Log out",  "url": url_for("app.logout") })

    return nav_items
