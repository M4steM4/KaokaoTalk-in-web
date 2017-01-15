from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from flask import g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO,emit,join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'development-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)


class user(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    userid = db.Column(db.Text, nullable = False)
    userpw = db.Column(db.Text, nullable = False)

    def __init__(self,userid,userpw):
        self.userid = userid
        self.userpw = userpw

        def __repr__(self):
            return '<user %r>' % self.id

@app.route('/')
def index():

    usr = None
    if 'name' in session:
        usr = user.query.filter_by(userid=session['name']).one()

    return render_template('index.html',user=usr)

@app.route('/logout')
def logout():
    session.pop('name',None)
    return redirect(url_for('index'))

@app.route('/login', methods=['POST','GET'])
def login():
    error = None
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        usr = user.query.filter_by(userid=username).first()
        if usr is None:
            error = '아이디 또는 비밀번호가 잘못되었습니다.'
        elif not check_password_hash(usr.userpw,password):
            error = '아이디 또는 비밀번호가 잘못되었습니다.'
        else:
            session['name'] = usr.userid
            return redirect(url_for('index'))
    return render_template('login.html', error = error)


@app.route('/regist', methods=['POST','GET'])
def regist():
    error = None
    if request.method == 'POST':
        usrcheck = user.query.filter_by(userid=request.form['userid']).first()
        if usrcheck is None:
            userdata = user(request.form['userid'],generate_password_hash(request.form['userpw']))
            db.session.add(userdata)
            db.session.commit()
            session['name'] = request.form['userid']
            return redirect('/')
        else:
            error = '이미 있는 아이디입니다.'

    return render_template('regist.html',error= error)

@app.route('/room',methods=['POST','GET'])
def room():
    if request.method == 'POST':
        roomid = request.form['selector']
        session['room'] = roomid
        return redirect('/chat')

    return render_template('room.html')

@app.route('/chat')
def chat():
    name = session.get('name', '')
    room = session.get('room', '')
    return render_template('chat.html', name=name,room=room)

a = [[],[],[]]
@socketio.on('joined', namespace='/chat')
def joined(message):
    room=session.get('room')
    join_room(room)
    whojoin = session.get('name')
    roomint = int(room) - 1
    global a
    a[roomint].append(whojoin)
    a[roomint] = list(set(a[roomint]))
    emit('status', {'msg': session.get('name') + '님이 채팅방에 입장하셨습니다.', 'list' : a[roomint],'count' : len(a[roomint])},room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    time = datetime.now()
    nowhour = str(time.hour)
    nowmin = str(time.minute)
    who = session.get('name')
    room=session.get('room')
    emit('message', {'msg': session.get('name') + ':' + message['msg'], 'nowhour' : nowhour , 'nowmin' : nowmin,'who':who},room=room)

@socketio.on('left', namespace='/chat')
def left(message):
    room=session.get('room')
    leave_room(room)
    wholeft = session.get('name')
    roomint = int(room) - 1
    global a
    a[roomint].remove(wholeft)
    emit('status', {'msg': session.get('name') + '님이 채팅방에서 나가셨습니다.','list' : a[roomint],'count' : len(a[roomint])},room=room)


if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0',port=8080,debug=True)
