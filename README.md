# COMP639_Project_2_Amber





## Test User Accounts

Demo deployment link available upon request.
Demo accounts are available for testing purposes. Credentials can be provided upon request.

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

### 4. run the web

- python run.py

## Project Screenshots

Borba, J. (n.d.). _Woman exercising indoors_ [Photograph]. Unsplash. https://unsplash.com/photos/woman-exercising-indoors-lrQPTQs7nQQ

van de Broek, C. (n.d.). _Man and woman riding road bikes near shore_ [Photograph]. Unsplash. https://unsplash.com/photos/man-and-woman-riding-road-bikes-at-the-road-near-shore-OFyh9TpMyM8

Busing, H. (n.d.). _Person in red sweater holding baby’s hand_ [Photograph]. Unsplash. https://unsplash.com/photos/person-in-red-sweater-holding-babys-hand-Zyx1bK9mqmA

Hladynets, V. (n.d.). _Man in white crew-neck shirt wearing black-framed eyeglasses_ [Photograph]. Unsplash. https://unsplash.com/photos/man-in-white-crew-neck-shirt-wearing-black-framed-eyeglasses-_RcTaCHHMI0

Dam, M. (n.d.). _Close-up photography of woman smiling_ [Photograph]. Unsplash. https://unsplash.com/photos/closeup-photography-of-woman-smiling-mEZ3PoFGs_k

Vallet, G. (n.d.). _Man in black shorts running on road during daytime_ [Photograph]. Unsplash. https://unsplash.com/photos/man-in-black-t-shirt-and-black-shorts-running-on-road-during-daytime-J154nEkpzlQ

Vega, K. (n.d.). _Silhouette of woman doing yoga_ [Photograph]. Unsplash. https://unsplash.com/photos/silhouette-photography-of-woman-doing-yoga-F2qh3yjz6Jk

Spiske, M. (n.d.). _Person walking on a rock in the woods_ [Photograph]. Unsplash. https://unsplash.com/photos/a-person-walking-on-a-rock-in-the-woods-R5mkpdyqzY8

Weaver, L. (n.d.). _Woman in black activewear lying on studio floor_ [Photograph]. Unsplash. https://unsplash.com/photos/woman-in-black-tank-top-and-black-leggings-lying-on-black-floor-u76Gd0hP5w4
