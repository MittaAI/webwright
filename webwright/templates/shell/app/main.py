from flask import Flask, render_template, request, make_response
import datetime
from lib.util import build_command_list

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template('pages/index.html')

    @app.route('/c', methods=['GET', 'POST'])
    def console():
        now = datetime.datetime.now(datetime.timezone.utc)
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            line = request.cookies.get('line')
        except Exception:
            line = ""

        commands = build_command_list()

        response = make_response(render_template(
            'pages/shell.html',
            line=line,
            commands=commands,
            timestamp=timestamp
        ))

        response.set_cookie('line', '', expires=0)

        return response

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=7000)