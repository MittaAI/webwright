from flask import Flask, render_template, request, make_response
import datetime
from lib.util import build_command_list, random_string
import urllib

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

    @app.route('/base.js')
    def base_js():
        now = datetime.datetime.now(datetime.timezone.utc)
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Add other variables as needed
        context = {
            'timestamp': timestamp,
            'line': request.args.get('line', ''),
        }
        
        response = make_response(render_template('js/base.js', **context))
        response.headers['Content-Type'] = 'application/javascript'
        return response

    @app.route('/j', methods=['POST', 'GET'])
    def javascript_command():        
        # application info
        app_id = random_string(9)
        target_id = request.form.get('target_id')

        # get the json document
        json_documents = request.get_json()
        
        # get the line
        line = json_documents.get('line', request.form.get('line', request.args.get('line', '')))
        line = urllib.parse.unquote(line)

        # determine the command
        command = line.split()[0][1:] if line.startswith('!') else get_user_setting(request.user.uid, "mode", default="console")

        # build path to command
        command_path = f'templates/commands/{command}.js'

        content = {
            "app_id": app_id,
            "target_id": target_id,
            "line": line.replace('"', '\\"').replace("'", "\\'"),
            "command": command,
        }

        try:
            # render local commands
            response = make_response(render_template(command_path, **content))
            response.headers['Content-Type'] = 'application/json'
        except Exception as ex:
            print(f"Error: {ex}")
            # return not found app
            response = make_response(render_template('commands/notfound.js', **content))
            response.headers['Content-Type'] = 'application/json'

        return response

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=7000)