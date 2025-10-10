'''
This module contains functions, not specified for some out service.

'''
import os
import logging
import shutil
import json
from post import Post


logger = logging.getLogger(__name__)

def get_last_json_id(config: dict, service: str) -> int:
    '''
    Get last processed post id by service from file
    '''
    last_id_file_path = os.path.join(config['temp_dir'], '.last.json')
    if os.path.exists(last_id_file_path):
        with open(last_id_file_path, encoding='utf8') as last_id_file:
            last_json = json.load(last_id_file)
        if service in last_json.keys():
            last_id = last_json[service]
        else:
            last_id = 0
    else:
        last_id = 0

    logger.debug(
        'Last id for service %s is %s',
        service,
        last_id
    )
    return last_id

def write_last_json_id(config: dict, service: str, last_id: int) -> None:
    '''
    Write last processed post id by service to file
    '''
    last_id_file_path = os.path.join(config['temp_dir'], '.last.json')
    if os.path.exists(last_id_file_path):
        with open(last_id_file_path, encoding='utf8') as last_id_file:
            last_json = json.load(last_id_file)
        last_json[service] = last_id
    else:
        last_json = {service: last_id}

    with open(last_id_file_path, 'w', encoding='utf-8') as last_id_file:
        json.dump(last_json, last_id_file)
        logger.info(
            'Last id %s for service %s is written to %s',
            last_id,
            service,
            last_id_file_path
        )

def get_last_id(config):
    '''
    Get last processed post id from file
    '''
    last_id_file_path = os.path.join(config['temp_dir'], '.last')

    if os.path.exists(last_id_file_path):
        with open(last_id_file_path, encoding='utf8') as last_id_file:
            last_id = int(last_id_file.read().strip())
    else:
        last_id = 0

    logger.debug('Last id is %s', last_id)
    return last_id


def write_last_id(config, last_id):
    '''
    Wtite last processeed post id to file
    '''
    last_id_file_path = os.path.join(config['temp_dir'], '.last')

    with open(last_id_file_path, 'w', encoding='utf-8') as last_id_file:
        last_id_file.write(str(last_id))
        logger.debug('Last id is written to %s', last_id_file_path)


def make_content_dir(config):
    '''
    Creates temp content folder for photos.
    IG API allows import photos only from web.
    This folder will be seen from inet.
    '''
    content_dir = os.path.join(config['temp_dir'], 'content')
    os.makedirs(content_dir, exist_ok=True)
    logger.debug('Content dir is %s',content_dir)
    return content_dir

def cleanup_content(config, posts: list[Post]):
    '''
    Cleanup content from temp folder after processing
    '''
    for post in posts:
        post_content = os.path.join(config['temp_dir'],'content',str(post.id))
        try:
            shutil.rmtree(post_content)
            logger.info('Post content removed from %s', post_content)
        except OSError as err:
            logger.error('Cannot remove content from %s: %s', post_content, err)
