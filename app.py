from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
<<<<<<< HEAD
def index():
=======
def home():
>>>>>>> d01cfefb033855bd967d4d274b0a2d95e7e826cd
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)