'''
This module contains telegram-related functions
'''

import logging
import telebot
from autoposter_classes import Post
from autoposter_common import reformat_post_text


logger = logging.getLogger(__name__)


def repost_to_tg(config: dict, posts: list[Post]):
    '''Repost to telegram'''
    bot = telebot.TeleBot(config['telegram']['token'])
    for post in posts:
        post_text = reformat_post_text(config, post, 'tg')

        medias = []

        for photo in post.photos:
            with open(photo.file_path, 'rb') as photo_file:
                medias.append(telebot.types.InputMediaPhoto(media=photo_file))

        medias[0].caption = post_text
        medias[0].parse_mode = 'markdown'

        bot.send_media_group(
            chat_id=config['telegram']['channel_id'],
            media=medias
        )

        logger.info(
            "Post id=%s (%s photos) reposted to Telegram channel %s",
            post.id,
            len(medias),
            config['telegram']['channel_id']
        )

# if __name__ == '__main__':
#     import os
#     import yaml
#     from autoposter_vk import get_new_vk_posts

#     os.chdir(os.path.dirname(__file__))

#     with open('config.yaml', encoding='utf-8') as config_file:
#         app_config = yaml.load(config_file, Loader=yaml.FullLoader)

#     os.makedirs(app_config['temp_dir'], exist_ok=True)

#     app_config['telegram']['channel_id'] = -1002282539965
#     new_posts = sorted(get_new_vk_posts(app_config), key=lambda post: post.id)
#     repost_to_tg(app_config, new_posts)
