from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # 指定未登入時重定向到的頁面

# 使用者模型
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

# 教室借用紀錄模型
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(20), nullable=False)
    classroom = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(20), nullable=False)

# 初始化資料庫
with app.app_context():
    db.create_all()

# 註冊頁面
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        student_id = request.form.get("student_id")
        password = request.form.get("password")

        # 密碼加密
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name=name, student_id=student_id, password=hashed_password)

        db.session.add(user)
        db.session.commit()
        flash("註冊成功！請登入以使用系統。")
        return redirect(url_for("login"))  # 註冊完成後跳轉到登入頁面

    return render_template("register.html")

# 登入頁面
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        student_id = request.form.get("student_id")
        password = request.form.get("password")

        user = User.query.filter_by(student_id=student_id).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("登入成功！")
            return redirect(url_for("index"))
        else:
            flash("登入失敗，請檢查學號或密碼。")

    return render_template("login.html")

# 登出功能
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("您已成功登出。")
    return redirect(url_for("login"))

# 首頁：僅登入使用者可進入
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        # 使用表單中的姓名與學號，允許使用者更新這兩個欄位
        name = request.form.get("name")
        student_id = request.form.get("student_id")
        classroom = request.form.get("classroom")
        date = request.form.get("date")

        # 新增借用紀錄
        new_booking = Booking(name=name, student_id=student_id,
                              classroom=classroom, date=date)
        db.session.add(new_booking)
        db.session.commit()

    # 將目前登入的使用者資訊傳遞給模板
    bookings = Booking.query.filter_by(student_id=current_user.student_id).all()
    return render_template("index.html", bookings=bookings, current_user=current_user)

# 登入管理
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == "__main__":
    app.run(debug=True)
