
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_login import UserMixin, login_user, logout_user, login_manager, LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json

# MY db connection
local_server = True
app = Flask(__name__)
app.secret_key = '12345'

# this is for getting unique user access
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# app.config['SQLALCHEMY_DATABASE_URL']='mysql://username:password@localhost/databas_table_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/studentdbms'
db = SQLAlchemy(app)

# here we will create db models that is tables
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))

class Department(db.Model):
    cid = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.String(100))

class Trig(db.Model):
    tid = db.Column(db.Integer, primary_key=True)
    rollno = db.Column(db.String(100))
    action = db.Column(db.String(100))
    timestamp = db.Column(db.String(100))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))

class Attendence(db.Model):
    aid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rollno = db.Column(db.String(20), primary_key=True)
    attendance = db.Column(db.Integer)



class Count(db.Model):
    dept = db.Column(db.String(50), primary_key=True)
    sem = db.Column(db.Integer, primary_key=True)
    student_count = db.Column(db.Integer, nullable=True)

class Student(db.Model):
    rollno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sname = db.Column(db.String(50))
    sem = db.Column(db.Integer)
    gender = db.Column(db.String(50))
    branch = db.Column(db.String(50))
    email = db.Column(db.String(50))
    number = db.Column(db.String(12))
    address = db.Column(db.String(100))


@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/studentdetails')
def studentdetails():
    query = Student.query.all() 
    return render_template('studentdetails.html', query=query)

@app.route('/triggers')
def triggers():
    query = Trig.query.all()
    return render_template('triggers.html', query=query)

@app.route('/department', methods=['POST', 'GET'])
def department():
    if request.method == "POST":
        dept = request.form.get('dept')
        query = Department.query.filter_by(branch=dept).first()
        if query:
            flash("Department Already Exist", "warning")
            return redirect('/department')
        dep = Department(branch=dept)
        db.session.add(dep)
        db.session.commit()
        flash("Department Added", "success")
    return render_template('department.html')

@app.route('/addattendance', methods=['POST', 'GET'])
def addattendance():
    query = Student.query.all()
    if request.method == "POST":
        rollno = request.form.get('rollno')
        attend = int(request.form.get('attend'))
        print(attend, rollno)
        attendance_entry = Attendence(rollno=rollno, attendance=attend)
        db.session.add(attendance_entry)
        db.session.commit()

        # Update the average attendance for the student
        avg_attendance = db.session.query(func.avg(Attendence.attendance)).filter(Attendence.rollno == rollno).scalar()
        # Update the average_attendance field for the corresponding student
        student = Student.query.filter_by(rollno=rollno).first()
        student.average_attendance = avg_attendance
        db.session.commit()

        flash("Attendance added", "warning")
        
    return render_template('attendance.html', query=query)

# @app.route('/search', methods=['POST', 'GET'])
# def search():
#     if request.method == "POST":
#         rollno = request.form.get('roll')
#         bio = Student.query.filter_by(rollno=rollno).first()
#         attend = Attendence.query.filter_by(rollno=rollno).first()
#         # Pass the actual attendance value instead of the roll number
#         return render_template('search.html', bio=bio, attend=attend.attendance if attend else None)

#     return render_template('search.html')
@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == "POST":
        rollno = request.form.get('roll')
        bio = Student.query.filter_by(rollno=rollno).first()
        attendances = Attendence.query.filter_by(rollno=rollno).all()
        
        # Calculate average attendance
        total_attendance = sum(attendance.attendance for attendance in attendances)
        avg_attendance = total_attendance / len(attendances) if attendances else 0
        
        return render_template('search.html', bio=bio, avg_attendance=avg_attendance)

    return render_template('search.html')


@app.route("/delete/<string:rollno>", methods=['POST', 'GET'])
@login_required
def delete(rollno):
    post = Student.query.filter_by(rollno=rollno).first()  # Changed id to rollno
    db.session.delete(post)
    db.session.commit()
    flash("Slot Deleted Successfully", "danger")
    return redirect('/studentdetails')

@app.route("/edit/<string:rollno>", methods=['POST', 'GET'])
@login_required
def edit(rollno):
    post = Student.query.filter_by(rollno=rollno).first()
    if post is None:
        flash("Student record not found", "danger")
        return redirect('/studentdetails')

    if request.method == "POST":
        sname = request.form.get('sname')
        sem = request.form.get('sem')
        gender = request.form.get('gender')
        branch = request.form.get('branch')
        email = request.form.get('email')
        num = request.form.get('num')
        address = request.form.get('address')

        # Don't allow changing the roll number
        post.sname = sname
        post.sem = sem
        post.gender = gender
        post.branch = branch
        post.email = email
        post.number = num
        post.address = address
        db.session.commit()
        flash("Slot is Updated", "success")
        return redirect('/studentdetails')

    dept = Department.query.all()
    return render_template('edit.html', posts=post, dept=dept)



@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exist", "warning")
            return render_template('/signup.html')
        
        newuser = User(username=username, email=email, password=password)
        db.session.add(newuser)
        db.session.commit()
        flash("Signup Successful. Please Login", "success")
        return render_template('login.html')
          
    return render_template('signup.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials", "danger")
            return render_template('login.html')    

    return render_template('login.html')

@app.route('/count')
def display_count():
    counts = Count.query.all()
    return render_template('count.html', counts=counts)
# from sqlalchemy.orm import outerjoin

# @app.route('/count')
# def display_count():
#     # Query to get all departments and their respective student counts, even if count is 0
#     counts = db.session.query(Department, func.coalesce(Count.student_count, 0).label('student_count')) \
#                        .outerjoin(Count, (Department.dept == Count.dept) & (Department.sem == Count.sem) ) \
#                        .all()

#     return render_template('count.html', counts=counts)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successful", "warning")
    return redirect(url_for('login'))

# @app.route('/addstudent', methods=['POST', 'GET'])
# @login_required
# def addstudent():
#     dept = Department.query.all()
#     if request.method == "POST":
#         rollno = request.form.get('rollno')
#         sname = request.form.get('sname')
#         sem = request.form.get('sem')
#         gender = request.form.get('gender')
#         branch = request.form.get('branch')
#         email = request.form.get('email')
#         num = request.form.get('num')
#         address = request.form.get('address')
        
#         query = Student(rollno=rollno, sname=sname, sem=sem, gender=gender, branch=branch, email=email, number=num, address=address)
#         db.session.add(query)
#         db.session.commit()
#         flash("Booking Confirmed", "info")

#     return render_template('student.html', dept=dept)

@app.route('/addstudent', methods=['POST', 'GET'])
@login_required
def addstudent():
    # dept=db.engine.execute("SELECT * FROM `department`")
    dept = Department.query.all()
    if request.method == "POST":
        # Extract data from the form
        sname = request.form.get('sname')
        sem = request.form.get('sem')
        gender = request.form.get('gender')
        branch = request.form.get('branch')
        email = request.form.get('email')
        num = request.form.get('num')
        address = request.form.get('address')
        
        # Generate a unique rollno value if needed
        # Example: rollno = generate_unique_rollno()
        
        # Create a new Student instance with the extracted data
        student = Student(sname=sname, sem=sem, gender=gender, branch=branch, email=email, number=num, address=address)
        
        # Add the student instance to the session
        db.session.add(student)
        
        try:
            # Commit the changes to the database
            db.session.commit()
            flash("Student record added successfully", "success")
        except Exception as e:
            # Rollback the session in case of an error
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

        # Redirect to the student details page or any other appropriate page
        return redirect(url_for('studentdetails'))

    return render_template('student.html', dept=dept)


@app.route('/test')
def test():
    try:
        Test.query.all()
        return 'My database is Connected'
    except:
        return 'My db is not Connected'

if __name__ == "__main__":
    app.run(debug=True)
