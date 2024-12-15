# Import necessary modules and packages
from flask import Blueprint, render_template, request, redirect, url_for, flash,current_app,g,session, jsonify
import os, shutil
import base64
import sqlite3
from werkzeug.utils import secure_filename
from home import get_db
from datetime import datetime, timedelta
import json
import pandas as pd
import logging
import filetype

admin_blueprint = Blueprint('admin', __name__)

logger = logging.getLogger('admin')

def validate_image_files(files):
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp']
    
    for file in files:
        kind = filetype.guess(file.stream)
        if not kind or kind.mime not in allowed_types:
            return False, f"Invalid file type for image '{file.filename}'. Allowed types are .jpg, .jpeg, .png, .gif, .bmp"
    
    return True, None

# Route for displaying all bookings to admin
@admin_blueprint.route('/admin/bookings', methods=['GET', 'POST'])
def bookings():
    if session.get('user_type') == 'admin':
        db, cursor = get_db()
        today = datetime.now()
        today_str = datetime.now().strftime('%d/%m/%Y')

        cursor.execute("SELECT * FROM booking ORDER BY date DESC")
        current_bookings = cursor.fetchall()
        logger.info(f"Admin {session.get('username')} viewed bookings.")
        return render_template('admin_booking.html', bookings=current_bookings)
    else:
        logger.info(f"User {session.get('username')} tried to access a restricted page")
        return render_template('not_authorised.html')

# Route for admin homepage
@admin_blueprint.route('/adminpage', methods=['GET', 'POST'])
def admin_home():
    if session.get('user_type') == 'admin':
        db, cursor = get_db()
        today = datetime.now().date()
        monday_date = today - timedelta(days=today.weekday())
        friday_date = monday_date + timedelta(days=11)
        today_str = today.strftime('%d/%m/%Y')
        friday_str = friday_date.strftime('%d/%m/%Y')
        cursor.execute("SELECT * FROM booking")
        bookings_display = cursor.fetchall()

        filtered_bookings = []

        for booking in bookings_display:
            booking_date = datetime.strptime(booking[3], '%d/%m/%Y').date()
            if today <= booking_date < friday_date and booking[7] == 'Booked':
                filtered_bookings.append(booking)
        bookings_display = filtered_bookings

        cursor.execute("SELECT * FROM booking")
        bookings = cursor.fetchall()

        df = pd.DataFrame(bookings, columns=['id', 'room_name', 'user', 'date', 'time', 'attendance', 'equipment', 'status'])

        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
        df['month'] = df['date'].dt.month

        bookings_per_month = df.groupby('month').size()
        bookings_per_month_dict = bookings_per_month.to_dict()

        rooms_distribution = df['room_name'].value_counts().to_dict()
        
        bookings_per_month = json.dumps(bookings_per_month_dict)
        rooms_distribution = json.dumps(rooms_distribution)
        logger.info(f"Admin {session.get('username')} viewed dashboard stats on {today_str}")

        return render_template('admin.html', bookings=bookings_display, bookings_per_month=bookings_per_month, rooms_distribution= rooms_distribution)
    else:
        logger.info(f"User {session.get('username')} tried to access a restricted page")
        return render_template('not_authorised.html')


# Route for viewing rooms by admin
@admin_blueprint.route('/admin/view_rooms', methods=['GET', 'POST'])
def view_rooms():
    if session.get('user_type') == 'admin':
        db, cursor = get_db()
        cursor.execute("SELECT * FROM rooms")
        rooms = cursor.fetchall()
        updated_rooms = []
        user_type = session.get('user_type')
        imagesFolder = 'static/images/'
        
        folder_dict = {}
        
        for folder_name in os.listdir(imagesFolder):
            folder_path = os.path.join(imagesFolder, folder_name)
            if os.path.isdir(folder_path):
                file_names = os.listdir(folder_path)
                folder_dict[folder_name] = file_names
        
        for room in rooms:
            image_blob = room[4]
            encoded_image = base64.b64encode(image_blob).decode('utf-8')
            updated_room = list(room) + [encoded_image]
            updated_rooms.append(updated_room)
        
        folder_dict_json = json.dumps(folder_dict)
        logger.info(f"Admin {session.get('username')} viewed rooms gallery")
        return render_template('gallery.html', rooms=updated_rooms, user_type=user_type, folder_dict=folder_dict_json)
    else:
        logger.info(f"User {session.get('username')} tried to access a restricted page")
        return render_template('not_authorised.html')

# Route for adding rooms by admin
@admin_blueprint.route('/admin/add_rooms', methods=['GET', 'POST'])
def add_rooms():
    if session.get('user_type') == 'admin':
        db, cursor = get_db()
        room_name = request.form['room_name']
        building = request.form['building']
        occupancy = request.form['occupancy']
        available = request.form.get('available', 'No')
        if available == 'on':
            available = 'Yes'
        video_conferencing = request.form.get('video_conferencing', 'No')
        if video_conferencing == 'on':
            video_conferencing = 'Yes'
        image_file = request.files['images']
        image_data = image_file.read()

        valid, error_message = validate_image_files([image_file])
        if not valid:
            room_add = 'false'
            logger.error(error_message)
            return redirect(url_for('admin.view_rooms', room_add=room_add))

        slideshow_images = request.files.getlist('slideshow_images')

        valid, error_message = validate_image_files(slideshow_images)
        if not valid:
            room_add = 'false'
            logger.error(error_message)
            return redirect(url_for('admin.view_rooms', room_add=room_add))

        UPLOAD_FOLDER = 'static/images/'+str(room_name)

        try:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            for slideshow_image in slideshow_images:
                    slideshow_image_filename = secure_filename(slideshow_image.filename)
                    slideshow_image.save(os.path.join(UPLOAD_FOLDER, slideshow_image_filename))
            cursor.execute("""
                INSERT INTO rooms (Name,Building, Seats, Images, Available, Video_Conferencing)
                VALUES (?, ?, ?, ?,?,?)
            """, (room_name, building, occupancy, sqlite3.Binary(image_data), available, video_conferencing))
            db.commit()
            logger.info(f"Admin {session.get('username')} added room '{room_name}'")
            room_add = 'true'
            return render_template('gallery.html', room_add=room_add)
        
        except Exception as e:
            room_add  = 'false'
            logger.error(f"Admin {session.get('user_name')} failed to add room '{room_name}': {str(e)}")
            return redirect(url_for('admin.view_rooms',room_add = room_add))
    else:
        logger.info(f"User {session.get('username')} tried to access a restricted page")
        return render_template('not_authorised.html')

# Route for deleting rooms by admin    
@admin_blueprint.route('/admin/delete_room', methods=['GET', 'POST'])
def delete_room():
    try:
        room_name = request.args.get('room_name')
        delete_folder = 'static/images/'+str(room_name)
        db, cursor = get_db()
        cursor.execute("DELETE FROM rooms WHERE Name=?", (room_name,))
        db.commit()
        shutil.rmtree(delete_folder)
        logger.info(f"Admin {session.get('username')} deleted room '{room_name}'")
        return 'Room deleted successfully!'
    except Exception as e:
        logger.error(f"Admin {session.get('username')} failed to delete room '{room_name}': {str(e)}")
        return 'Unable to delete room'
    
@admin_blueprint.route('/admin/update_room', methods=['GET', 'POST'])
def update_room():
    try:
        room_name = request.form.get('roomName')
        new_room_value = room_name
        building = request.form.get('building')
        occupancy = request.form.get('occupancy')
        availability = request.form.get('availability')
        video_conferencing = request.form.get('videoConferencing')

        main_image = request.files.get('displayImage')

        if main_image and main_image.filename != '':
            image_data = main_image.read()
            valid, error_message = validate_image_files([main_image])
            if not valid:
                logger.error(error_message)
                return render_template('message.html', message='Could not update the room')
        else:
            image_data = None

        db, cursor = get_db()
        if image_data is None:
            cursor.execute("UPDATE rooms SET Building = ?, Seats = ?, Available = ?, Video_Conferencing = ? WHERE Name = ?", 
                           (building, occupancy, availability, video_conferencing, room_name))
            db.commit()
        else:
            cursor.execute("UPDATE rooms SET Building = ?, Seats = ?, Images = ?, Available = ?, Video_Conferencing = ? WHERE Name = ?", 
                           (building, occupancy, sqlite3.Binary(image_data), availability, video_conferencing, room_name))
            db.commit()

        logger.info(f"Admin {session.get('username')} updated room '{room_name}'")
        return render_template('message.html', message='Room updated successfully!')

    except Exception as e:
        logger.error(f"Admin {session.get('username')} failed to update room '{room_name}': {str(e)}")
        return render_template('message.html', message='Could not update the room')


# Route for deleting a user by admin  
@admin_blueprint.route('/delete_user', methods=['GET', 'POST'])
def delete_user():
    try:
        userID = request.form.get('userid')
        user_type = request.form.get('user_type')
        db, cursor = get_db()
        if user_type == 'user':
            cursor.execute("""
                    UPDATE user
                    SET status = 'Inactive'
                    WHERE userID = ?
                """, (userID,))
            db.commit()

        elif user_type == 'admin':
            cursor.execute("""
                    UPDATE admin
                    SET status = 'Inactive'
                    WHERE adminID = ?
                """, (userID,))
            db.commit()

        logger.info(f"Admin {session.get('username')} deleted user with ID '{userID}' of type '{user_type}'")
        return render_template('message.html', message='User deleted successfully!')
    except Exception as e:
        logger.error(f"Admin {session.get('username')} failed to delete user with ID '{userID}': {str(e)}")
        return render_template('message.html', message="Couldn't delete the user")

    

# Route for updating a user by admin
@admin_blueprint.route('/admin/update_user', methods=['GET', 'POST'])
def update_user():
    try:
        user_id = request.json.get('userId')
        name = request.json.get('name')
        email = request.json.get('email')
        status = request.json.get('status')
        usertype = request.json.get('userType')
        db, cursor = get_db()
        if usertype == 'user':
            cursor.execute("""
                    UPDATE {}
                    SET Name = ?, email = ?, status = ?
                    WHERE userID = ?
                """.format(usertype), (name, email, status, user_id,))
            db.commit()
        elif usertype == 'admin':
            cursor.execute("""
                    UPDATE {}
                    SET name = ?, email = ?, status = ?
                    WHERE adminID = ?
                """.format(usertype), (name, email, status, user_id,))
            db.commit()
        logger.info(f"Admin {session.get('username')} updated user {user_id}'s details")
        return render_template('message.html', message='User updated successfully!')
    except Exception as e:
        logger.error(f"Admin {session.get('username')} failed to update user with ID '{user_id}': {str(e)}")
        return render_template('message.html', message="Couldn't update the user")


# Route for changing a user to admin by admin
@admin_blueprint.route('/change_to_admin', methods=['GET', 'POST'])
def change_to_admin():
    userID = request.form.get('userid')
    db, cursor = get_db()
    cursor.execute("""
            UPDATE user
            SET status = 'Moved to Admin'
            WHERE userID = ?
        """, (userID,))
    db.commit()
    
    user_query = "SELECT * FROM user WHERE userID = ?"
    user_data = db.execute(user_query, (userID,)).fetchone()

    insert_admin_query = "INSERT INTO admin (email, password, name, status) VALUES (?, ?, ?,?)"
    db.execute(insert_admin_query, ( user_data[5], user_data[1],user_data[4],'Active'))
    db.commit()
    logger.info(f"Admin {session.get('username')} changed user '{userID}' to admin")

    return 'User moved to admin!'



# Route for viewing users by admin
@admin_blueprint.route('/admin/view_users', methods=['GET', 'POST'])
def view_users():
    db, cursor = get_db()
    cursor.execute("SELECT userID,name, email, status  FROM user")
    users = cursor.fetchall()

    cursor.execute("SELECT adminID,name, email, status  FROM admin")
    admins = cursor.fetchall()
    logger.info(f"Admin {session.get('username')} viewed users")
    return render_template('users.html', users=users, admins=admins)

# Route for updating a booking by admin
@admin_blueprint.route('/admin/update_booking', methods=['GET', 'POST'])
def update_booking():
    db, cursor = get_db()
    data = request.json
    booking_id = data.get('bookingId')
    name = data.get('name') 
    user = data.get('user')
    date = data.get('date')
    time = data.get('time')
    attendance = data.get('attendance')
    equipment = data.get('equipment')
    status = data.get('status')

    try:
        cursor.execute("""
            UPDATE booking
            SET room_name = ?, userID = ?, date = ?, time = ?, attendance = ?, equipment = ?, status = ?
            WHERE bookingID = ?
        """, (name, user, date, time, attendance, equipment, status, booking_id))
        db.commit()
        logger.info(f"Admin {session.get('username')} updated booking '{booking_id}'")
        return 'Updated booking'

    except Exception as e:
        logger.error(f"Admin {session.get('username')} failed to update booking '{booking_id}': {str(e)}")
        current_app.logger.info('Couldnt update booking')
