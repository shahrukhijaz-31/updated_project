from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
db = SQLAlchemy(app)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    score = db.relationship('Score', backref='Quiz', lazy=True)


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    quizes = db.relationship('Quiz', backref='Teacher', lazy='dynamic')

    def __init__(self, username, password):
        self.password = password
        self.username = username


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'),
                           nullable=False)

    def __init__(self, name, teacher_id):
        self.name = name
        self.teacher_id = teacher_id


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    correct_ans = db.Column(db.String(3), nullable=False)
    statement = db.Column(db.String(80), nullable=False)
    option_a = db.Column(db.String(80), nullable=False)
    option_b = db.Column(db.String(80), nullable=False)
    option_c = db.Column(db.String(80), nullable=False)
    option_d = db.Column(db.String(80), nullable=False)
    quiz_id = db.Column(db.Integer, nullable=False)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marks = db.Column(db.Integer, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'),
                           nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'),
                        nullable=False)


db.create_all()


@app.route("/student_index")
def student_index():
    quizes = Quiz.query.all()
    # student_id = Student.query.filter_by(username=session['username']).first()
    # quizes_attempted = Score.query.filter_by(student_id=student_id)
    return render_template("student_index.html", quizes=quizes)


@app.route('/admin')
def admin():
    if 'username' is None:
        return redirect(url_for("index"))
    teachers = Teacher.query.all()
    students = Student.query.all()
    user_data = {'students': students, 'teachers': teachers}
    return render_template("admin.html", user_data=user_data)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/start_quiz/<int:quiz_id>/<string:student_username>', methods=['GET', 'POST'])
def start_quiz(quiz_id, student_username):
    questions = Question.query.filter_by(quiz_id=quiz_id)
    quiz_data = {'questions': questions, 'student_username': student_username}
    return render_template("attempt_quiz.html", quiz_data=quiz_data)


@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    username = request.form["username"]
    score = 0
    quiz_solution = list()
    quiz_id = request.form["quiz_id"]
    questions = Question.query.filter_by(quiz_id=quiz_id)
    for question in questions:
        selected_ans = request.form['option'+str(question.id)]
        correct_ans = question.correct_ans
        if correct_ans == "A":
            correct_ans = question.option_a
        if correct_ans == "B":
            correct_ans = question.option_b
        if correct_ans == "C":
            correct_ans = question.option_c
        if correct_ans == "D":
            correct_ans = question.option_d
        if correct_ans == selected_ans:
            score += 1
        question_solution = {'question_statement': question.statement,
                             'correct_ans': correct_ans, 'selected_ans': selected_ans}
        quiz_solution.append(question_solution)
    result = {'score': score, 'solution': quiz_solution, 'username': username, 'quiz_id': quiz_id}
    return render_template("result.html", result=result)


@app.route('/save_marks/<username>/<score>/<quiz_id>')
def save_marks(username, score, quiz_id):
    student = Student.query.filter_by(username=username).first()
    score = Score(student_id=student.id, marks=score, quiz_id=quiz_id)
    db.session.add(score)
    db.session.commit()
    return redirect(url_for("student_index"))


@app.route('/attempt_quiz', methods=['GET', 'POST'])
def attempt_quiz():
    return render_template("attempt_quiz.html")


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user_type = request.form['type']
    if user_type == 'Teacher':
        user = Teacher.query.filter_by(username=username).first()
        if user is None:
            return "incorrect username"
        else:
            if user.password == password:
                session['username'] = username
                session['id'] = user.id
                return redirect(url_for('teacher_index'))
            else:
                return "incorrect password"
    if user_type == 'Admin':
        if username == 'admin' and password == 'admin':
            return redirect(url_for('admin'))
    else:
        user = Student.query.filter_by(username=username).first()
        if user is None:
            return "incorrect username"
        else:
            if user.password == password:
                session['username'] = username
                session['id'] = user.id
                return redirect(url_for('student_index'))
            else:
                return "incorrect password"


@app.route("/logout", methods=['POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route("/teacher_index")
def teacher_index():
    if 'username' in session:
        return render_template("teacher_index.html")
    return "You are not logged in <br><a href = '/index'></b>" + \
        "click here to log in</b></a>"


@app.route("/create_quiz")
def create_quiz():
    return render_template("create_quiz.html")


@app.route("/create_quiz_body", methods=['POST', 'GET'])
def create_quiz_body():
    question_number = request.form['question_number']
    quiz_name = request.form['quiz_name']
    question_number = 1 + int(question_number)
    quiz_detail = dict({'quiz_name': quiz_name, 'question_number': question_number})
    return render_template("create_quiz_body.html", quiz_detail=quiz_detail)


@app.route("/save_quiz", methods=['POST', 'GET'])
def save_quiz():
    questions = list()
    question_number = request.form['question_number']
    quiz_name = request.form['quiz_name']
    teacher_name = request.form['teacher_name']
    teacher = Teacher.query.filter_by(username=teacher_name).first()

    quiz = Quiz(name=quiz_name, teacher_id=teacher.id)
    db.session.add(quiz)
    db.session.commit()

    for question_id in range(1, int(question_number)):
        question_statement = request.form['question' + str(question_id)]
        correct_ans = request.form['correct_ans'+str(question_id)]
        options = list()
        options.append(dict({'A': request.form['option_a'+str(question_id)]}))
        options.append(dict({'B': request.form['option_a'+str(question_id)]}))
        options.append(dict({'C': request.form['option_a'+str(question_id)]}))
        options.append(dict({'D': request.form['option_a'+str(question_id)]}))
        quiz = Quiz.query.filter_by(name=quiz_name).first()
        question = Question()
        question.quiz_id = quiz.id
        question.correct_ans = correct_ans
        question.statement = question_statement
        question.option_a = request.form['option_a'+str(question_id)]
        question.option_b = request.form['option_b'+str(question_id)]
        question.option_c = request.form['option_c'+str(question_id)]
        question.option_d = request.form['option_d'+str(question_id)]
        db.session.add(question)
        db.session.commit()

        question = {'question': question_statement, 'correct_ans': correct_ans, 'options': options,
                    'teacher_name': teacher_name, 'quiz_name': quiz_name}
        questions.append(question)
    return redirect(url_for('teacher_index'))


@app.route("/quiz_management", methods=['POST', 'GET'])
@app.route("/quiz_management/<string:username>", methods=['POST', 'GET'])
@app.route("/quiz_management/<int:quiz_id>", methods=['POST', 'GET'])
def quiz_management(username=None, quiz_id=None):
    if username is None and quiz_id is None:
        quiz_id = session['id']
        quizes = Quiz.query.filter_by(teacher_id=quiz_id)
        quiz_details = list()
        for quiz in quizes:
            quiz_details.append({'quiz_id': quiz.id, 'name': quiz.name})
        return render_template("quiz_management.html", quiz_details=quiz_details)
    else:
        if quiz_id is None:
            teacher = Teacher.query.filter_by(username=username).first()
            quizes = Quiz.query.filter_by(teacher_id=teacher.id)
            quiz_details = list()
            for quiz in quizes:
                quiz_details.append({'quiz_id': quiz.id, 'name': quiz.name})
            return json.dumps(quiz_details)
        else:
            quizes = Quiz.query.filter_by(teacher_id=quiz_id)
            quiz_details = list()
            for quiz in quizes:
                quiz_details.append({'quiz_id': quiz.id, 'name': quiz.name})
            return json.dumps(quiz_details)


@app.route("/delete_quiz/<quiz_id>", methods=['GET', 'POST'])
def delete_quiz(quiz_id):
    if 'username' in session:
        quiz = Quiz.query.filter_by(id=quiz_id).first()
        if quiz is None:
            return "Error! 404"
        else:
            db.session.delete(quiz)
            db.session.commit()
        return redirect(url_for('quiz_management'))
    else:
        quiz = Quiz.query.filter_by(id=quiz_id).first()
        if quiz is None:
            return "Enter valid quiz id please!"
        else:
            db.session.delete(quiz)
            db.session.commit()
            return redirect(url_for("quiz_management"))


@app.route("/edit_quiz/<quiz_id>", methods=['GET', 'POST'])
@app.route("/edit_quiz", methods=['GET', 'POST'])
def edit_quiz(quiz_id=None):
    if quiz_id is None:
        if 'username' in session:
            questions = get_questions(quiz_id)
            return render_template('edit_quiz.html', questions=json.loads(questions))
        else:
            return "Login Please"
    else:
        if 'username' in session:
            questions = get_questions(quiz_id)
            return render_template('edit_quiz.html', questions=json.loads(questions))
        else:
            return "Login Please"


@app.route("/get_questions/<quiz_id>", methods=['GET'])
def get_questions(quiz_id):
    questions = Question.query.filter_by(quiz_id=quiz_id)
    question_details = list()
    for question in questions:
        options = list()
        options.append(dict({'option_a': question.option_a}))
        options.append(dict({'option_b': question.option_b}))
        options.append(dict({'option_c': question.option_c}))
        options.append(dict({'option_d': question.option_d}))
        question_details.append(dict({'id': question.id, 'statement': question.statement,
                                      'options': options, 'correct_ans': question.correct_ans,
                                      'quiz_id': question.quiz_id}))
    return json.dumps(question_details)


@app.route("/edit_question", methods=['GET', 'POST'])
def edit_question():
    question_id = request.form.get('question_id')
    question = Question.query.filter_by(id=question_id).first()
    question_body = {'id': question.id, 'statement': question.statement,
                     'option_a': question.option_a, 'option_b': question.option_b,
                     'option_c': question.option_c, 'option_d': question.option_d,
                     'correct_ans': question.correct_ans}
    return json.dumps(question_body)


@app.route("/update_question", methods=['POST'])
def update_question():
    question_id = request.form["question_id"]
    question_statement = request.form["question_statement"]
    option_a = request.form["option_a"]
    option_b = request.form["option_b"]
    option_c = request.form["option_c"]
    option_d = request.form["option_d"]
    ans = request.form["ans"]

    question = Question.query.filter_by(id=question_id).first()
    question.correct_ans = ans
    question.statement = question_statement
    question.option_a = option_a
    question.option_b = option_b
    question.option_c = option_c
    question.option_d = option_d
    db.session.commit()
    return redirect(url_for("edit_quiz",quiz_id=question.quiz_id))


@app.route("/delete_question/<quiz_id>", methods=['POST', 'GET'])
def delete_question(quiz_id):
    question = Question.query.filter_by(id=quiz_id).first()
    question_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for("edit_quiz", id=question_id))


@app.route("/add_question", methods=['POST', 'GET'])
def add_question():
    question_body = request.form.get('question_body')
    return "Success"


@app.route("/insert_teacher", methods=['POST'])
def insert_teacher():
    name = request.form["teacher_name"]
    password = request.form["teacher_password"]
    teacher = Teacher.query.filter_by(username=name).first()
    if teacher is None:
        teacher = Teacher(username=name, password=password)
        db.session.add(teacher)
        db.session.commit()
        return redirect(url_for("admin"))
    else:
        return "404 Duplicate Name Error!"


@app.route("/insert_student", methods=['POST'])
def insert_student():
    name = request.form["student_name"]
    password = request.form["student_password"]
    student = Student.query.filter_by(username=name).first()
    if student is None:
        student = Student(username=name, password=password)
        db.session.add(student)
        db.session.commit()
        return redirect(url_for("admin"))
    else:
        return "404 Duplicate Name Error!"


if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = True
    app.run()
