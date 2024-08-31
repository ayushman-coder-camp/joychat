from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jfgdarararfacepuddingtrtrtrtgdkg'
socketio = SocketIO(app)

rooms = {}

def create_room_code(characters):
    while True:
        code = ''
        for _ in range(characters):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code

@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        enterBtn = request.form.get('enter-btn', False)
        createBtn = request.form.get('create-btn', False)

        if not name:
            return render_template('index.html', errorText='You have to enter a name.', code=code, name=name)
        
        if enterBtn != False and not code:
            return render_template('index.html', errorText='You have to enter a code to join a room.', code=code, name=name)
        
        room = code
        if createBtn != False:
            room = create_room_code(5)
            rooms[room] = {'people': 0, 'messages': []}
        elif code not in rooms:
            return render_template('index.html', errorText='Room does not exist.', code=code, name=name)
        
        session['room'] = room
        session['name'] = name

        return redirect(url_for('chatroom'))

    return render_template('index.html')

@app.route('/chatroom')
def chatroom():
    room = session.get('room')
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('home'))

    return render_template('chatroom.html', roomcode=room)

@socketio.on('message')
def message(data):
    room = session.get('room')
    name = session.get('name')

    if room not in rooms:
        return
    
    content = {
        "name": name,
        "message": data["msg_data"]
    }

    send(content, to=room)
    rooms[room]['messages'].append(content)
    print(f"{name} said {data['msg_data']}")

@socketio.on('connect')
def connect(auth):
    room = session.get('room')
    name = session.get('name')

    if not room or not name:
        return
    
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({ 'name': name, 'message': 'entered the room' }, to=room)
    rooms[room]['people'] += 1
    print(f'{name} entered room {room}')

@socketio.on('disconnect')
def disconnect():
    room = session.get('room')
    name = session.get('name')
    leave_room(room)

    if room in rooms:
        rooms[room]['people'] -= 1
        if rooms[room]['people'] <= 0:
            del rooms[room]
    
    send({ 'name': name, 'message': 'left the room' }, to=room)
    print(f'{name} left room {room}')

if __name__ == '__main__':
    socketio.run(app, debug=True, port=8002)