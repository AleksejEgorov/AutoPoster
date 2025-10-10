'''
This module contains instagram related functions
'''

import os
import logging
import requests
from PIL import Image, ImageOps
from autoposter_classes import Post, PostEncoder
from autoposter_common import reformat_post_text

logger = logging.getLogger(__name__)

def squarefy_photo(photo_path: str, size: int, color: str):
    '''
    Create sqare image with white fields. For IG
    '''
    photo = Image.open(photo_path)
    resized_photo = ImageOps.contain(photo, (size, size))
    logger.debug('Photo %s resized to %s', photo_path, resized_photo.size)
    squared_photo = ImageOps.pad(resized_photo, (size, size), color=color)
    logger.debug('Photo %s squared to %s and filled with %s', photo_path, squared_photo.size, color)
    squared_photo_path = photo_path.replace('.jpg','_inst.jpg')
    squared_photo.save(squared_photo_path)
    logger.debug('Squared photo saved to %s', squared_photo_path)
    return squared_photo_path

def repost_to_instagram(config: dict, posts: list[Post]) -> None:
    '''
    Repost to IG as single photo or carousel
    '''
    ig_token = config['instagram']['app_token']
    if config["instagram"]["proxy"]:
        proxies = {
            'http': config["instagram"]["proxy"],
            'https': config["instagram"]["proxy"]
        }
        logger.info('Using proxy %s', config["instagram"]["proxy"])
    else:
        proxies = None

    inst_me = requests.get(
        'https://graph.instagram.com/v21.0/me',
        params={
            'access_token': ig_token,
            'fields': 'user_id,username,account_type,name'
        },
        proxies=proxies,
        timeout=10
    )

    ig_id = inst_me.json()['user_id']
    logger.debug('Instagram user ID is %s', ig_id)


    for post in posts:
        # prepare tag list:
        tags = config['instagram']['default_tags'].copy()
        logger.debug('Source post %s tags are %s', post.id, post.tags)
        post_tags_count = config['instagram']['total_tags_count'] - len(tags) - 1
        logger.debug(
            'Post %s has %s mandatory tags, %s custom expected',
            post.id,
            len(tags),
            post_tags_count
        )
        post_tags = list(filter(lambda tag: ' ' not in tag, post.tags))[0:post_tags_count]
        logger.info('Post %s selected tags: %s', post.id, post_tags)
        tags.extend(post_tags)
        tags = [f'#{tag}' for tag in tags]
        logger.debug('Final tags list: %s', tags)
        inst_text = f'{reformat_post_text(config, post, 'inst')}\n{" ".join(tags)}'
        logger.info('Post %s prepared text: %s', post.id, inst_text.replace('\n','\\n'))

        # prepare photo list
        inst_photos = []
        for photo in post.photos:
            local_photo_path = squarefy_photo(
                photo.file_path,
                1280,
                config['instagram']['fill_color']
            )
            web_photo_path = '/'.join(
                [
                    config["instagram"]['web_photo_location'],
                    str(post.id),
                    os.path.basename(local_photo_path)
                ]
            )
            inst_photos.append(web_photo_path)

        logger.debug('Post %s photo web urls: %s', post.id, inst_photos)

        # https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing
        # https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media?locale=en_US
        if len(inst_photos) > 1:
            # Carousel
            child_containers = []
            for photo in inst_photos:
                photo_container = requests.post(
                    f'https://graph.instagram.com/v21.0/{ig_id}/media',
                    params={
                        'image_url': photo,
                        'is_carousel_item': 'true',
                        'access_token': ig_token
                    },
                    proxies=proxies,
                    timeout=10
                )
                child_containers.append(photo_container.json()['id'])
            carousel_container = requests.post(
                f'https://graph.instagram.com/v21.0/{ig_id}/media',
                params={
                    'caption': inst_text,
                    'media_type': 'CAROUSEL',
                    'children': ','.join(child_containers),
                    'access_token': ig_token
                },
                proxies=proxies,
                timeout=10
            )

            inst_post = requests.post(
                 f'https://graph.instagram.com/v21.0/{ig_id}/media_publish',
                params={
                    'creation_id': carousel_container.json()['id'],
                    'access_token': ig_token
                },
                proxies=proxies,
                timeout=30
            )

            try:
                logger.info(
                    'Post %s is reposted to Instagram with ID %s',
                    post.id,
                    inst_post.json()['id']
                )
            except Exception as err:
                logger.error('Instagram API error: %s', inst_post.json())
                raise


        else:
            # Single photo
            photo_container = requests.post(
                f'https://graph.instagram.com/v21.0/{ig_id}/media',
                params={
                    'image_url': inst_photos[0],
                    'caption': inst_text,
                    'access_token': ig_token
                },
                proxies=proxies,
                timeout=10
            )
            inst_post = requests.post(
                f'https://graph.instagram.com/v21.0/{ig_id}/media_publish',
                params={
                    'creation_id': photo_container.json()['id'],
                    'access_token': ig_token
                },
                proxies=proxies,
                timeout=30
            )

            try:
                logger.info(
                    'Post %s is reposted to Instagram with ID %s',
                    post.id,
                    inst_post.json()['id']
                )
            except Exception as err:
                logger.error('Instagram API error: %s', inst_post.json())
                raise


if __name__ == '__main__':
    import yaml
    import json
    # from autoposter_vk import get_new_vk_posts

    os.chdir(os.path.dirname(__file__))

    with open('config.yaml', encoding='utf-8') as config_file:
        app_config = yaml.load(config_file, Loader=yaml.FullLoader)

    # new_posts = get_new_vk_posts(config)
    # get_photo_tags(config, new_posts)

    with open(
        os.path.join(app_config['temp_dir'], 'test_post.json'),
        encoding='utf-8'
    ) as json_post:
        new_posts = json.load(json_post)

    # example_posts = list(map(lambda post: Post(post), new_posts))
    # https://pylint.readthedocs.io/en/latest/user_guide/messages/warning/unnecessary-lambda.html
    example_posts = [Post(post) for post in new_posts]

    repost_to_instagram(app_config, example_posts)
    print(json.dumps(new_posts, cls=PostEncoder))

    # if app_config["instagram"]["proxy"]:
    #     proxies = {
    #         'http': app_config["instagram"]["proxy"],
    #         'https': app_config["instagram"]["proxy"]
    #     }
    # else:
    #     proxies = None
    # inst_me = requests.get(
    #     'https://graph.instagram.com/v21.0/me',
    #     params={
    #         'access_token': config['instagram']['app_token'],
    #         'fields': 'user_id,username,account_type,name'
    #     },
    #     proxies=proxies
    # )
    # print(inst_me.json())
    # print(inst_me.json())
