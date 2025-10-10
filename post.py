'''
This class describes post with one or more photos in it
'''

import os
import logging
import json
import asyncio
import re
from time import sleep
import requests
import telebot
from telebot.types import InputMediaPhoto
from googletrans import Translator
from photo import Photo


logger = logging.getLogger(__name__)

class Post:
    '''
    This class describes post with one or more photos in it
    '''
    def __init__(self, post):
        self.__text: str = ''
        self.__tags: list[str] = []
        self.__photos: list[Photo] = []

        if isinstance(post, dict):
            self.__id = post.get('id')
            self.__text = post.get('text', '')
            self.__tags = post.get('tags', [])
            self.__photos = []
            post_photos = post.get('photos', [])

            for photo_dict in post_photos:
                photo = Photo(photo_dict['id'], photo_dict['file_path'], photo_dict['url'])
                photo.tags = photo_dict['tags']
                self.__photos.append(photo)
        else:
            self.__id = post

    def __str__(self):
        return f'{self.__id} {self.__text} ({len(self.__photos)} photos)'

    @property
    def id(self):
        ''' Return post id '''
        return self.__id

    @property
    def photos(self):
        ''' Return post photos '''
        return self.__photos

    @property
    def text(self):
        ''' Return post text '''
        return self.__text

    @text.setter
    def text(self, text: str):
        self.__text = text

    def add_photo(self, photo_id: int, file: str, url: str ) -> None:
        "Add photo to post"
        self.__photos.append(Photo(photo_id, file, url))


    def to_json(self):
        '''converts post to serializable json'''
        return json.dumps(self, default=lambda o: o.__dict__)

    @staticmethod
    async def __translate_text(text, src_lang = 'ru', dst_lang = 'en'):
        '''Translate photo title with google translate'''
        async with Translator() as translator:
            result = await translator.translate(text, src=src_lang, dest=dst_lang)
        logger.info('Text %s translated as %s', text, result.text)
        return result.text

    def __reformat_text(self, config: dict, target: str) -> str:
        '''
        Replace vk links to markdown links.
        Apply customization, described in config['replaces']
        '''
        # https://pylint.readthedocs.io/en/stable/user_guide/messages/refactor/consider-using-assignment-expr.html
        # text = post.text
        if not (text := self.__text):
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
            text = asyncio.run(self.__translate_text(text))
        return text

    def add_tags(self, config: dict) -> None:
        '''
        Add photo tags to post tags
        '''
        post_tags = config['instagram']['default_tags'].copy()
        logger.debug('Source post %s tags are %s', self.__id, post_tags)
        custom_tags_count = config['instagram']['total_tags_count'] - len(post_tags) - 1
        logger.debug(
            'Post %s has %s mandatory tags, %s custom expected',
            self.__id,
            len(post_tags),
            custom_tags_count
        )
        custom_tags = []

        for photo in self.__photos:
            custom_tags.extend(photo.get_immaga_tags(config))

        post_tags.extend(list(filter(lambda tag: ' ' not in tag, custom_tags)))
        self.__tags = list(set(post_tags))[0:config['instagram']['total_tags_count']]
        self.__tags = [f'#{tag}' for tag in self.__tags]
        logger.info('Post %s final tags are %s', self.__id, self.__tags)

    def repost_to_instagram(self, config: dict) -> None:
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
            logger.info('No proxy for Instagram will be used')
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

        # prepare text
        self.add_tags(config=config)
        inst_text = self.__reformat_text(config, 'inst') + '\n\n' + ' '.join(self.__tags)

        # prepare photo list
        inst_photos = []
        for photo in self.__photos:
            local_photo_path = photo.squarefy(
                1280,
                config['instagram']['fill_color']
            )
            web_photo_path = '/'.join(
                [
                    config["instagram"]['web_photo_location'],
                    str(self.__id),
                    os.path.basename(local_photo_path)
                ]
            )
            inst_photos.append(web_photo_path)

        logger.debug('Post %s photo web urls: %s', self.__id, inst_photos)

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
                    timeout=config['instagram']['timeout']
                )
                sleep(3) # to avoid 9007 error

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
                timeout=config['instagram']['timeout']
            )
            sleep(3) # to avoid 9007 error


            inst_post = requests.post(
                f'https://graph.instagram.com/v21.0/{ig_id}/media_publish',
                params={
                    'creation_id': carousel_container.json()['id'],
                    'access_token': ig_token
                },
                proxies=proxies,
                timeout=config['instagram']['timeout']
            )

            try:
                logger.info(
                    'Post %s is reposted to Instagram with ID %s',
                    self.__id,
                    inst_post.json()['id']
                )
            except Exception as err:
                logger.error(
                    'Instagram API error %s: %s',
                    err,
                    inst_post.json()
                )
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
                timeout=config['instagram']['timeout']
            )
            sleep(3) # to avoid 9007 error

            inst_post = requests.post(
                f'https://graph.instagram.com/v21.0/{ig_id}/media_publish',
                params={
                    'creation_id': photo_container.json()['id'],
                    'access_token': ig_token
                },
                proxies=proxies,
                timeout=config['instagram']['timeout']
            )

            try:
                logger.info(
                    'Post %s is reposted to Instagram with ID %s',
                    self.__id,
                    inst_post.json()['id']
                )
            except Exception as err:
                logger.error(
                    'Instagram API error %s: %s',
                    err,
                    inst_post.json()
                )
                raise

    def repost_to_tg(self, config: dict):
        '''Repost to telegram'''
        bot = telebot.TeleBot(config['telegram']['token'])

        post_text = self.__reformat_text(config, 'tg')

        medias = []

        for photo in self.__photos:
            medias.append(InputMediaPhoto(media=photo.url))

        medias[0].caption = post_text
        medias[0].parse_mode = 'markdown'

        bot.send_media_group(
            chat_id=config['telegram']['channel_id'],
            media=medias
        )

        logger.info(
            "Post id=%s (%s photos) reposted to Telegram channel %s",
            self.__id,
            len(medias),
            config['telegram']['channel_id']
        )


class PostEncoder(json.JSONEncoder):
    '''Service class'''
    def default(self, o):
        return o.__dict__
