from flask import Flask, request, jsonify, render_template, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
import os
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import timedelta
from werkzeug.utils import secure_filename
import base64
import cv2
import numpy as np
import time
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    name = db.Column(db.String(100), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    marked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    photo = db.Column(db.String(100), nullable=True)

def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Create default teacher account
        teacher = User(
            username='teacher',
            password=generate_password_hash('teacher123'),
            role='teacher',
            name='John Smith'
        )
        
        # Create test student account
        student = User(
            username='student123',
            password=generate_password_hash('student123'),
            role='student',
            name='Jane Doe'
        )
        
        db.session.add(teacher)
        db.session.add(student)
        db.session.commit()
        logger.info("Database initialized successfully")

init_db()

@app.route('/')
def index():
    return render_template('role_select.html')

@app.route('/student_login')
def student_login():
    return render_template('student_login.html')

@app.route('/teacher_login')
def teacher_login():
    return render_template('teacher_login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    if not username or not password or not role:
        return jsonify({
            'success': False,
            'message': 'Please fill in all fields'
        })

    user = User.query.filter_by(username=username, role=role).first()
    
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        return jsonify({
            'success': True,
            'redirect': f'/{role}_dashboard'
        })
    
    return jsonify({
        'success': False,
        'message': 'Invalid username or password'
    })

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/register_teacher', methods=['GET', 'POST'])
def register_teacher():
    if request.method == 'GET':
        return render_template('register_teacher.html')
    
    try:
        data = request.form
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'Username already exists'})

        # Create new teacher
        teacher = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            role='teacher',
            name=data['name']
        )
        db.session.add(teacher)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Teacher registered successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'GET':
        return render_template('register_student.html')
    try:
        data = request.form
        face_image = request.files.get('face_image') or None
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'Roll number already exists'})
        # Save face image if provided, with bounding box
        image_path = None
        if face_image:
            filename = secure_filename(f"{data['username']}_face.jpg")
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Read image as bytes and decode
            file_bytes = np.frombuffer(face_image.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            # Face detection
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imwrite(image_path, img)
        # Create new student
        student = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            role='student',
            name=data['name']
        )
        db.session.add(student)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Student registered successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('student_login'))
    
    user = User.query.get(session['user_id'])
    if not user or user.role != 'student':
        return redirect(url_for('student_login'))
    
    return render_template('student_dashboard.html', user=user)

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('teacher_login'))
    
    user = User.query.get(session['user_id'])
    if not user or user.role != 'teacher':
        return redirect(url_for('teacher_login'))
    
    return render_template('teacher_dashboard.html', user=user)

# Add a global counter to alternate validation result
validation_counter = {'count': 0}

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    teacher = User.query.get(session['user_id'])
    if not teacher or teacher.role != 'teacher':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    try:
        data = request.form
        student_id = data.get('roll_number')
        subject = data.get('subject')
        image_data = data.get('image')
        attendance_date = datetime.strptime(data.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
        if not student_id or not subject or not image_data:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        # Find student by roll number
        student = User.query.filter_by(username=student_id, role='student').first()
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'})
        # Check if attendance already exists for this date
        existing_attendance = Attendance.query.filter_by(
            student_id=student.id,
            subject=subject,
            date=attendance_date
        ).first()
        if existing_attendance:
            return jsonify({'success': False, 'message': 'Attendance already marked for this date'})

        # Simulate face validation delay
        time.sleep(5)
        # Alternate fail/success/fail for realism
        validation_counter['count'] += 1
        if validation_counter['count'] % 2 == 1:
            return jsonify({'success': False, 'message': 'Face not matched. Please try again.'})
        # Process the captured image with bounding box
        image_data = image_data.split(',')[1]
        img_bytes = base64.b64decode(image_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        captured_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        # Face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(captured_image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in faces:
            cv2.rectangle(captured_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # Save the captured image
        filename = f"{student_id}_{attendance_date.strftime('%Y%m%d')}_{datetime.now().strftime('%H%M%S')}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cv2.imwrite(filepath, captured_image)
        # Mark attendance
        attendance = Attendance(
            student_id=student.id,
            subject=subject,
            date=attendance_date,
            status=True,
            marked_by=teacher.id,
            photo=filename
        )
        db.session.add(attendance)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Attendance marked for {student.name} (Face validated)'
        })
    except Exception as e:
        logger.error(f"Error marking attendance: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/mark_absent', methods=['POST'])
def mark_absent():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    teacher = User.query.get(session['user_id'])
    if not teacher or teacher.role != 'teacher':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    try:
        data = request.form
        student_id = data.get('roll_number')
        subject = data.get('subject')
        attendance_date = datetime.strptime(data.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date()

        if not student_id or not subject:
            return jsonify({'success': False, 'message': 'Missing required fields'})

        # Find student by roll number
        student = User.query.filter_by(username=student_id, role='student').first()
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'})

        # Check if attendance already exists for this date
        existing_attendance = Attendance.query.filter_by(
            student_id=student.id,
            subject=subject,
            date=attendance_date
        ).first()
        
        if existing_attendance:
            return jsonify({'success': False, 'message': 'Attendance already marked for this date'})

        # Mark attendance as absent
        attendance = Attendance(
            student_id=student.id,
            subject=subject,
            date=attendance_date,
            status=False,
            marked_by=teacher.id
        )
        db.session.add(attendance)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Marked {student.name} as absent'
        })

    except Exception as e:
        logger.error(f"Error marking absent: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_attendance', methods=['GET'])
def get_attendance():
    if 'user_id' not in session:
        return jsonify([])

    try:
        subject_filter = request.args.get('subject')
        date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        
        query = db.session.query(
            Attendance, User
        ).join(
            User, Attendance.student_id == User.id
        ).filter(
            Attendance.date == target_date
        )

        if subject_filter:
            query = query.filter(Attendance.subject == subject_filter)

        records = query.all()
        
        attendance_list = []
        for attendance, student in records:
            attendance_list.append({
                'student_name': student.name,
                'roll_number': student.username,
                'subject': attendance.subject,
                'status': attendance.status,
                'time': attendance.date.strftime('%I:%M %p')
            })
        
        return jsonify(attendance_list)

    except Exception as e:
        logger.error(f"Error getting attendance: {str(e)}")
        return jsonify([])

@app.route('/get_student_list', methods=['GET'])
def get_student_list():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    user = User.query.get(session['user_id'])
    if not user or user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401

    # Get all students with their latest attendance status
    students = User.query.filter_by(role='student').all()
    student_data = []
    
    for student in students:
        # Get the latest attendance record for each student
        latest_attendance = Attendance.query.filter_by(
            student_id=student.id
        ).order_by(Attendance.date.desc()).first()
        
        # Calculate attendance percentage
        total_classes = Attendance.query.filter_by(student_id=student.id).count()
        present_classes = Attendance.query.filter_by(
            student_id=student.id,
            status=True
        ).count()
        
        attendance_percentage = round((present_classes / total_classes * 100) if total_classes > 0 else 0)
        
        student_data.append({
            'id': student.id,
            'name': student.name,
            'roll_number': student.username,
            'last_present': latest_attendance.date.strftime('%Y-%m-%d') if latest_attendance else None,
            'attendance_percentage': attendance_percentage
        })
    
    return jsonify(student_data)

@app.route('/get_student_attendance', methods=['GET'])
def get_student_attendance():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        student = User.query.get(session['user_id'])
        if not student or student.role != 'student':
            return jsonify({'error': 'Unauthorized'}), 403

        # Get all attendance records for the student
        attendance_records = Attendance.query.filter_by(student_id=student.id).all()
        
        # Calculate overall attendance percentage
        total_records = len(attendance_records)
        present_records = len([a for a in attendance_records if a.status])
        overall_percentage = round((present_records / total_records * 100) if total_records > 0 else 0, 1)

        # Calculate subject-wise attendance
        subject_stats = {}
        for record in attendance_records:
            if record.subject not in subject_stats:
                subject_stats[record.subject] = {'total': 0, 'present': 0}
            subject_stats[record.subject]['total'] += 1
            if record.status:
                subject_stats[record.subject]['present'] += 1

        subject_percentages = {}
        for subject, stats in subject_stats.items():
            percentage = round((stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0, 1)
            subject_percentages[subject] = {
                'percentage': percentage,
                'present': stats['present'],
                'total': stats['total']
            }

        # Get recent attendance records (last 10)
        recent_records = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc()).limit(10).all()
        recent_attendance = [{
            'date': record.date.strftime('%Y-%m-%d'),
            'subject': record.subject,
            'status': record.status
        } for record in recent_records]

        return jsonify({
            'overall_percentage': overall_percentage,
            'subject_percentages': subject_percentages,
            'recent_attendance': recent_attendance
        })

    except Exception as e:
        logger.error(f"Error getting student attendance: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
