from flask import Flask
from src.app.auth.auth_service import auth_service
from connect import dbuser, dbpass, dbhost, dbname, dbport
from src.app.admin.admin_controller import admin_blueprint
from src.app.api.api_controller import api_blueprint
from src.app.app_controller import app_blueprint, auth_service
from src.app.volunteer.volunteer_controller import volunteer_blueprint
from src.app.results.results_controller import results_blueprint
from src.app.participant.participant_controller import participant_blueprint
from src.app.group.group_controller import group_blueprint



from src.app.common.db import db
from src.app.common.nav.nav_items import left_nav_items, right_nav_items
from src.app.common.nav.nav_link import nav_link

app = Flask(__name__)
app.secret_key = 'H9#*lr1Q_T,-2<6gR7:!'

# Initialise DB using LoginExample function
db.init_db(app, dbuser, dbpass, dbhost, dbname, dbport)

# Register Jinja functions
app.jinja_env.globals.update(nav_link=nav_link)



# Register Blueprints
app.register_blueprint(app_blueprint, url_prefix='/')
app.register_blueprint(api_blueprint, url_prefix='/api')
app.register_blueprint(admin_blueprint, url_prefix='/admins')
app.register_blueprint(volunteer_blueprint, url_prefix='/volunteers')
app.register_blueprint(results_blueprint, url_prefix='/results')
app.register_blueprint(participant_blueprint, url_prefix='/participants')
app.register_blueprint(group_blueprint, url_prefix='/groups')


@app.context_processor
def get_nav_items():
    user_id = auth_service.get_user_id()
    user_role = auth_service.get_global_role()
    return {
        "left_nav_items": left_nav_items(user_id, user_role),
        "right_nav_items": right_nav_items(user_id, user_role)
    }




