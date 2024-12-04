def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions



def print_loaded_config(app):
    for key, value in app.config.items():
        print(f'{key} = {value}')
