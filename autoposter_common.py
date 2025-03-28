'''
This module contains functions, not specified for some out service.

'''
import os
import logging
import shutil
import re
import asyncio
import requests
from googletrans import Translator
from autoposter_classes import Post

logger = logging.getLogger(__name__)

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
        except OSError as e:
            logger.error('Cannot remove content from %s: %s', post_content, e)


def get_photo_tags(config, posts: list[Post]) -> None:
    '''
    Receive photo tags from immaga.com
    '''
    immaga_auth = (config['imagga']['api_key'], config['imagga']['api_secret'])

    for post in posts:
        logger.debug('Processing post %s', post.id)
        post_tags = []
        for photo in post.photos:
            logger.debug(print(f'Photo {photo.id}'))

            with open(photo.file_path, 'rb') as image:
                tag_response = requests.post(
                    'https://api.imagga.com/v2/tags',
                    auth=immaga_auth,
                    files={'image': image},
                    timeout=10
                )

            logger.info(
                '%s tags received for photo %s',
                len(tag_response.json()['result'].get('tags')),
                photo.id
            )

            photo_tags = tag_response.json()['result'].get('tags')
            tags_string = ', '.join(
                set(
                    tag_data['tag']['en'] for tag_data in sorted(
                        photo_tags,
                        key=lambda tag_data: tag_data['confidence'],
                        reverse=True
                    )
                )
            )

            logger.info('Photo %s tags are: %s', photo.id, tags_string)

            for tag in photo_tags:
                photo.tags.append(tag['tag']['en'])
            logger.debug('tags: %s', photo.tags)
            post_tags.extend(photo_tags)
        post.tags = list(
            set(
                tag_data['tag']['en'] for tag_data in sorted(
                    post_tags,
                    key=lambda tag_data: tag_data['confidence'],
                    reverse=True
                )
            )
        )
        logger.info('Post %s tags are %s', post.id, ", ".join(post.tags))


async def translate_text(text, src_lang = 'ru', dst_lang = 'en'):
    '''Translate photo title with google translate'''
    async with Translator() as translator:
        result = await translator.translate(text, src=src_lang, dest=dst_lang)
    logger.info('Text %s translated as %s', text, result.text)
    return result.text


def reformat_post_text(config: dict, post: Post, target: str) -> str:
    '''
    Replace vk links to markdown links.
    Apply customization, described in config['replaces']
    '''
    # https://pylint.readthedocs.io/en/stable/user_guide/messages/refactor/consider-using-assignment-expr.html
    # text = post.text
    if not (text := post.text):
        return ''
    replaces = config['replaces']
    vk_link_pattern = re.compile(r'\[id\d+\|[\w\s]+\]')
    vk_links = re.findall(vk_link_pattern, text)

    if target == 'tg':
        for vk_link in vk_links:
            vk_id, vk_name = vk_link.strip('[]').split('|')
            if vk_id in replaces.keys():
                text = text.replace(vk_link, replaces[vk_id]['tg'])
                logger.debug('VK link %s replaced with %s', vk_link, replaces[vk_id]["tg"])
            else:
                text = text.replace(vk_link, f'[{vk_name}](https://vk.com/{vk_id})')
                logger.debug(
                    'VK link %s replaced with [%s](https://vk.com/%s)',
                    vk_link,
                    vk_name,
                    vk_id
                )
    elif target == 'inst':
        text = text.replace('В кадре:', 'Md:')
        for vk_link in vk_links:
            vk_id, vk_name = vk_link.strip('[]').split('|')
            if vk_id in replaces.keys():
                text = text.replace(vk_link, replaces[vk_id]['inst'])
                logger.debug('VK link %s replaced with %s', vk_link, replaces[vk_id]["inst"])
            else:
                text = text.replace(vk_link, vk_name)
                logger.debug('VK link %s replaced with %s', vk_link, vk_name)
        text = asyncio.run(translate_text(text))
    return text


if __name__ == '__main__':
    import yaml

    os.chdir(os.path.dirname(__file__))

    with open('config.yaml', encoding='utf-8') as config_file:
        app_config = yaml.load(config_file, Loader=yaml.FullLoader)
    example_post = Post(1)
    example_post.text = "Самшит.\nВ кадре: [id309406780|Алиса Морозова] и [id19|Oher shit]."
    tg_text = reformat_post_text(app_config, example_post, 'tg')
    inst_text = reformat_post_text(app_config, example_post, 'inst')

    print(tg_text)
    print(inst_text)
