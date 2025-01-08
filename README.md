# Flask Room Booking Application [(Render Link)](https://room-booking-tool.onrender.com)
The application is a room booking tool, which can be used by employees and stakeholders to simplify booking and room management. The program includes a secure login system and two distinct user roles: 

- **Regular** :These users have the ability to browse available rooms, make reservations, view their existing bookings, and update them if needed.
- **Admin** : These super users have complete control over the application. Once the user is successfully logged in, they are shown a dashboard which includes the upcoming bookings in the next two weeks and visualisations showing the busiest months and most common rooms. Admins can perform all Create, Read, Update and Delete (CRUD) operations on users, rooms and bookings. 


## Requirements

- Python 3.9
- Filetype
- Flask
- Gunicorn
- Pandas
- Pytest
- SQLite
- Werkzeug

## Installation Guide to Run Locally (Mac)

1. **Clone the Repository**  
   ```bash
   git clone <repository_url>
   cd <repository_folder>
2. **Create and Activate a Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
3. **Install Dependencies**
    ```bash
    pip3 install -r requirements.txt
4. **Export Flask Application**
    ```bash
    export FLASK_APP=main.py
5. **Run the Flask Application**
    ```bash
    flask run

## Installation Guide to Run Locally (Windows)

1. **Clone the Repository**  
   ```cmd
   git clone <repository_url>
   cd <repository_folder>
   ```
2. **Create and Activate a Virtual Environment**  
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```
3. **Install Dependencies**  
   ```cmd
   pip install -r requirements.txt
   ```
4. **Set Flask Application**  
   ```cmd
   set FLASK_APP=main.py
   ```
5. **Run the Flask Application**  
   ```cmd
   flask run
   ```

## User Credentials

### Regular Users
| Username            | Password  | Security Question                | Security Answer |
|---------------------|-----------|-----------------------------------|-----------------|
| user1@email.com     | User1pw!  | What is your favourite food?     | Pizza           |
| user2@email.com     | User2pw!  | What is your favourite food?     | Pizza           |
| user3@email.com     | User3pw!  | What is your favourite food?     | Pizza           |

### Admin Users
| Username            | Password  |
|---------------------|-----------|
| admin1@email.com    | 1         |


    

