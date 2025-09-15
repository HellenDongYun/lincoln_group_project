from collections import namedtuple
from flask import Flask
from flask_bcrypt import Bcrypt

UserAccount = namedtuple('UserAccount', [
    'email',
    'password',
    'first_name',
    'last_name',
    'town',
    'role'
])

app = Flask(__name__)
flask_bcrypt = Bcrypt(app)

users = [
    # Participants
    UserAccount('alice.wong@gmail.com', 'Alice123!', 'Alice', 'Wong', 'Christchurch', 'participant'),
    UserAccount('bob.jones@outlook.com', 'Bob123!', 'Bob', 'Jones', 'Wellington', 'participant'),
    UserAccount('carol.smith@yahoo.com', 'Carol123!', 'Carol', 'Smith', 'Auckland', 'participant'),
    UserAccount('dave.brown@xtra.co.nz', 'Dave123!', 'Dave', 'Brown', 'Dunedin', 'participant'),
    UserAccount('emma.taylor@gmail.com', 'Emma123!', 'Emma', 'Taylor', 'Hamilton', 'participant'),
    UserAccount('frank.wilson@runclub.org', 'Frank123!', 'Frank', 'Wilson', 'Napier', 'participant'),
    UserAccount('grace.johnson@gmail.com', 'Grace123!', 'Grace', 'Johnson', 'Queenstown', 'participant'),
    UserAccount('harry.lee@outlook.com', 'Harry123!', 'Harry', 'Lee', 'Nelson', 'participant'),
    UserAccount('irene.martin@yahoo.com', 'Irene123!', 'Irene', 'Martin', 'Rotorua', 'participant'),
    UserAccount('jack.white@xtra.co.nz', 'Jack123!', 'Jack', 'White', 'Palmerston North', 'participant'),

    # Volunteers
    UserAccount('vanna.patel@gmail.com', 'Vanna123!', 'Vanna', 'Patel', 'Christchurch', 'volunteer'),
    UserAccount('victor.singh@outlook.com', 'Victor123!', 'Victor', 'Singh', 'Wellington', 'volunteer'),
    UserAccount('violet.kumar@lincoln.ac.nz', 'Violet123!', 'Violet', 'Kumar', 'Auckland', 'volunteer'),
    UserAccount('vincent.anderson@gmail.com', 'Vincent123!', 'Vincent', 'Anderson', 'Dunedin', 'volunteer'),
    UserAccount('valerie.thomas@yahoo.com', 'Valerie123!', 'Valerie', 'Thomas', 'Hamilton', 'volunteer'),
    UserAccount('vivian.nguyen@outlook.com', 'Vivian123!', 'Vivian', 'Nguyen', 'Napier', 'volunteer'),
    UserAccount('vernon.harris@xtra.co.nz', 'Vernon123!', 'Vernon', 'Harris', 'Queenstown', 'volunteer'),
    UserAccount('vanessa.moore@gmail.com', 'Vanessa123!', 'Vanessa', 'Moore', 'Nelson', 'volunteer'),
    UserAccount('vladimir.scott@runclub.org', 'Vladimir123!', 'Vladimir', 'Scott', 'Rotorua', 'volunteer'),
    UserAccount('valentina.green@gmail.com', 'Valentina123!', 'Valentina', 'Green', 'Palmerston North', 'volunteer'),

    # Admins
    UserAccount('nick.singh@lincoln.ac.nz', 'Admin123!', 'Nick', 'Singh', 'Christchurch', 'admin'),
    UserAccount('frank.smith@airnz.co.nz', 'Admin123!', 'Frank', 'Smith', 'Auckland', 'admin'),
]

print("SQL INSERT statements for Users table\n")

for user in users:
    password_hash = flask_bcrypt.generate_password_hash(user.password).decode()

    insert = f"""
    INSERT INTO Users (email, password_hash, first_name, last_name, town, role)
    VALUES ('{user.email}', '{password_hash}', '{user.first_name}', '{user.last_name}', '{user.town}', '{user.role}');
    """.strip()

    print(insert)
