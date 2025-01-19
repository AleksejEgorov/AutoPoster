import os
import logging
import shutil
import requests
import re
import asyncio
from googletrans import Translator
from autoposter_classes import Post

logger = logging.getLogger(__name__)

def get_last_id(config):
    last_id_file_path = os.path.join(config['temp_dir'], '.last')

    if os.path.exists(last_id_file_path):
        with open(last_id_file_path) as last_id_file:
            last_id = int(last_id_file.read().strip())
    else:
        last_id = 0
        
    logger.debug(f'Last id is {last_id}')
    return last_id


def write_last_id(config, last_id):
    last_id_file_path = os.path.join(config['temp_dir'], '.last')

    with open(last_id_file_path, 'w', encoding='utf-8') as last_id_file:
        last_id_file.write(str(last_id))
        logger.debug(f'Last id is written to {last_id_file_path}')


def make_content_dir(config):
    content_dir = os.path.join(config['temp_dir'], 'content')
    os.makedirs(content_dir, exist_ok=True)
    logger.debug(f'Content dir is {content_dir}')
    return content_dir

def cleanup_content(config, posts):
    for post in posts:
        post_content = os.path.join(config['temp_dir'],'content',str(post.id))
        try:
            shutil.rmtree(post_content)
            logger.info(f'Post content removed from {post_content}')
        except Exception as e:
            logger.error(f'Cannot remove content from {post_content}: {e}')


def get_photo_tags(config, posts: list[Post]):
    immaga_auth = (config['imagga']['api_key'], config['imagga']['api_secret'])

    for post in posts:
        logger.debug(f'Processing post {post.id}')
        post_tags = []
        for photo in post.photos:
            logger.debug(print(f'Photo {photo.id}'))
            
            tag_response = requests.post(
                'https://api.imagga.com/v2/tags',
                auth=immaga_auth,
                files={'image': open(photo.file_path, 'rb')}
            )
            logger.info(f'{len(tag_response.json()['result'].get('tags'))} tags received for photo {photo.id}')
            
            photo_tags = tag_response.json()['result'].get('tags')
            
            for tag in photo_tags:
                photo.tags.append(tag['tag']['en'])
            logger.debug(f'tags: {photo.tags}')
            post_tags.extend(photo_tags)
        post.tags = list(
            map(
                lambda tag_data: tag_data['tag']['en'], 
                sorted(post_tags, key=lambda tag_data: tag_data['confidence'], reverse=True)
            )
        )


async def translate_text(text, src_lang = 'ru', dst_lang = 'en'):
    async with Translator() as translator:
        result = await translator.translate(text, src=src_lang, dest=dst_lang)
    logger.info(f'Text {text} translated as {result.text}')
    return result.text


def reformat_post_text(config: dict, post: Post, target: str) -> str:
    text = post.text
    replaces = config['replaces']
    vk_link_pattern = re.compile(r'\[id\d+\|[\w\s]+\]')
    vk_links = re.findall(vk_link_pattern, text)
    
    if target == 'tg':
        for vk_link in vk_links:
            vk_id, vk_name = vk_link.strip('[]').split('|')
            if vk_id in replaces.keys():
                text = text.replace(vk_link, replaces[vk_id]['tg'])
                logger.debug(f'VK link {vk_link} replaced with {replaces[vk_id]["tg"]}')
            else:
                text = text.replace(vk_link, f'[{vk_name}](https://vk.com/{vk_id})')
                logger.debug(f'VK link {vk_link} replaced with [{vk_name}](https://vk.com/{vk_id})')
    elif target == 'inst':
        text = text.replace('В кадре:', 'Md:')
        text = asyncio.run(translate_text(text))
        for vk_link in vk_links:
            vk_id, vk_name = vk_link.strip('[]').split('|')
            if vk_id in replaces.keys():
                text = text.replace(vk_link, replaces[vk_id]['inst'])
                logger.debug(f'VK link {vk_link} replaced with {replaces[vk_id]["inst"]}')
            else:
                text = text.replace(vk_link, vk_name)
                logger.debug(f'VK link {vk_link} replaced with {vk_name}')
    return text


    
    
if __name__ == '__main__':
    import yaml
    import os
        
    os.chdir(os.path.dirname(__file__))
    
    with open('config.yaml', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
    post = Post(1)
    post.text = "Самшит.\nВ кадре: [id309406780|Алиса Морозова] и [id19|Oher shit]."
    tg_text = reformat_post_text(config, post, 'tg')
    inst_text = reformat_post_text(config, post, 'inst')
    
    print(tg_text)
    print(inst_text)