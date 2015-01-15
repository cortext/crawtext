from bottle import route, run, template

@route('/crawtext/<project>')
def index(name):
    return template('<b>Welcome to {{project}}</b>!', name=name)

@get('/create')
def upload_view():
    return """
    <form action="/upload" method="post" enctype="multipart/form-data">
    <input type="text" name="name" />
    <input type="file" name="data" />
    <input type="submit" name="submit" value="upload now" />
    </form>
    """
 
@post('/create')
def do_upload():
    name = request.forms.get('name')
    data = request.files.get('data')
    if name is not None and data is not None:
        raw = data.file.read() # small files =.=
    filename = data.filename
    return "Hello %s! You uploaded %s (%d bytes)." % (name, filename, len(raw))
    return "You missed a field." 

run(host='localhost', port=8080)
