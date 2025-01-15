import os


def get_last_id(config, service):
    last_id_file_path = os.path.join(config['temp_dir'], service, '.last')

    if os.path.exists(last_id_file_path):
        with open(last_id_file_path) as last_id_file:
            last_id = int(last_id_file.read().strip())
    else:
        last_id = 0

    return last_id


def write_last_id(config, service, last_id):
    last_id_file_path = os.path.join(config['temp_dir'], service, '.last')

    with open(last_id_file_path, 'w', encoding='utf-8') as last_id_file:
        last_id_file.write(str(last_id))


def make_content_dir(config, service):
    service_dir = os.path.join(config['temp_dir'], service)
    os.makedirs(service_dir, exist_ok=True)
    content_dir = os.path.join(service_dir, 'content')
    os.makedirs(content_dir, exist_ok=True)
    return content_dir