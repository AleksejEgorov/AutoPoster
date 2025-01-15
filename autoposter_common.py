import sys
import os
import shutil


def get_last_id(config):
    last_id_file_path = os.path.join(config['temp_dir'], '.last')

    if os.path.exists(last_id_file_path):
        with open(last_id_file_path) as last_id_file:
            last_id = int(last_id_file.read().strip())
    else:
        last_id = 0

    return last_id


def write_last_id(config, last_id):
    last_id_file_path = os.path.join(config['temp_dir'], '.last')

    with open(last_id_file_path, 'w', encoding='utf-8') as last_id_file:
        last_id_file.write(str(last_id))


def make_content_dir(config):
    content_dir = os.path.join(config['temp_dir'], 'content')
    os.makedirs(content_dir, exist_ok=True)
    return content_dir

def cleanup_content(config, posts):
    for post in posts:
        post_content = os.path.join(config['temp_dir'],'content',str(post.id))
        try:
            shutil.rmtree(post_content)
            print(f'Post content removed from {post_content}')
        except Exception as e:
            print(f'Cannot remove content from {post_content}: {e}', file=sys.stderr)