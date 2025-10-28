# COMP639_Project_2_Amber

Access here https://teamamberproject2.pythonanywhere.com/

hosting on PythonAnywhere https://www.pythonanywhere.com/user/TeamAmberProject2


## Test User Accounts
- Super Admin: super.admin@platform.org, Password: Super123!
- Support tech: support.tech@platform.org , Password: Support123!
- Participant 1 (manager Darfield): alice.wong@gmail.com, Password: Alice123!
- Participant 2 (manager Harbour Runners): bob.jones@outlook.com , Password: Bob123!
- Participant 3: carol.smith@yahoo.com , Password: Carol123!
- Participant 4: dave.brown@xtra.co.nz , Password: Dave123!
- Participant 5: emma.taylor@gmail.com , Password: Emma123!




## Technical Stack

Our team built this using:
- **Python/Flask** - Web framework
- **MySQL** - Database (hosted on PythonAnywhere)
- **Bootstrap 5** - For responsive UI
- **bcrypt** - Password security

## Deployment Guide for System Administrators

The steps below walk through deploying ActiveLoop on **PythonAnywhere** account. 

### 1. Prepare the PythonAnywhere account
- Sign in at https://www.pythonanywhere.com/ and create a new web app (Manual configuration).
- Choose **Python 3.11** (or the latest supported) when prompted for the virtualenv runtime.
- On the **Databases** tab, create a new MySQL database. PythonAnywhere provisions a database named `<username>$activeloop` with credentials you define.

Record the following values—they are required later:
- Database host: `<username>.mysql.pythonanywhere-services.com`
- Database name: `<username>$activeloop`
- Database user: `<username>` (or another you create)
- Database password: (set during database creation)

### 2. Upload the application code
PythonAnywhere offers two options:
1. **Git clone:**
	 - Open a Bash console from the Dashboard.
	 - Navigate to your project directory, for example:
		 ```bash
		 mkdir -p ~/activeloop && cd ~/activeloop
		 git clone https://github.com/TeamAmberProject2/activeloop.git .
		 ```
2. **Direct file upload:** Use the Files tab to upload the compressed project, then extract it inside your home directory.

### 3. Create the virtual environment
- in the Bash console:
	```bash
	cd ~/activeloop
	python3.11 -m venv ~/.virtualenvs/activeloop
	source ~/.virtualenvs/activeloop/bin/activate
	pip install --upgrade pip wheel
	pip install -r requirements.txt
	```
- Back in the Web tab, point the web app to this virtual environment (`/home/<username>/.virtualenvs/activeloop`).

### 4. Configure database credentials
- Duplicate `connect.py` so you keep a template for local development:
	```bash
	cp connect.py connect.local.py
	```
- Edit `connect.py` to reflect the PythonAnywhere MySQL endpoint (use `nano` or the online editor):
	```python
	dbuser = '<username>'
	dbpass = '<database_password>'
	dbhost = '<username>.mysql.pythonanywhere-services.com'
	dbport = 3306
	dbname = '<username>$activeloop'
	```

### 5. Initialise the database schema
- Open a MySQL console from the Databases tab or via Bash:
	```bash
	mysql -u <username> -h <username>.mysql.pythonanywhere-services.com -p
	```
- At the MySQL prompt, select the new database and load the scripts:
	```sql
	USE `<username>$activeloop`;
	SOURCE /home/<username>/activeloop/src/sql/create_database.sql;
	SOURCE /home/<username>/activeloop/src/sql/populate_database.sql;
	```
- Exit the MySQL shell. The seed scripts provision sample data including the test accounts listed earlier.

### 6. Reload and verify
- Click **Reload** on the Web tab.
- Visit `https://<username>.pythonanywhere.com/` and log in as `super.admin@platform.org` (password `Super123!`).
- Navigate to `/results/upload` and `/results/record` to confirm that group managers can manage results for their own events.


## Project Screenshots

Borba, J. (n.d.). *Woman exercising indoors* [Photograph]. Unsplash. https://unsplash.com/photos/woman-exercising-indoors-lrQPTQs7nQQ

van de Broek, C. (n.d.). *Man and woman riding road bikes near shore* [Photograph]. Unsplash. https://unsplash.com/photos/man-and-woman-riding-road-bikes-at-the-road-near-shore-OFyh9TpMyM8

Busing, H. (n.d.). *Person in red sweater holding baby’s hand* [Photograph]. Unsplash. https://unsplash.com/photos/person-in-red-sweater-holding-babys-hand-Zyx1bK9mqmA

Hladynets, V. (n.d.). *Man in white crew-neck shirt wearing black-framed eyeglasses* [Photograph]. Unsplash. https://unsplash.com/photos/man-in-white-crew-neck-shirt-wearing-black-framed-eyeglasses-_RcTaCHHMI0

Dam, M. (n.d.). *Close-up photography of woman smiling* [Photograph]. Unsplash. https://unsplash.com/photos/closeup-photography-of-woman-smiling-mEZ3PoFGs_k

Vallet, G. (n.d.). *Man in black shorts running on road during daytime* [Photograph]. Unsplash. https://unsplash.com/photos/man-in-black-t-shirt-and-black-shorts-running-on-road-during-daytime-J154nEkpzlQ

Vega, K. (n.d.). *Silhouette of woman doing yoga* [Photograph]. Unsplash. https://unsplash.com/photos/silhouette-photography-of-woman-doing-yoga-F2qh3yjz6Jk

Spiske, M. (n.d.). *Person walking on a rock in the woods* [Photograph]. Unsplash. https://unsplash.com/photos/a-person-walking-on-a-rock-in-the-woods-R5mkpdyqzY8

Weaver, L. (n.d.). *Woman in black activewear lying on studio floor* [Photograph]. Unsplash. https://unsplash.com/photos/woman-in-black-tank-top-and-black-leggings-lying-on-black-floor-u76Gd0hP5w4


