import os
import logging
import telebot
from autoposter_classes import Post
from autoposter_common import reformat_post_text 


logger = logging.getLogger(__name__)


def repost_to_tg(config: dict, posts: list[Post]):
    bot = telebot.TeleBot(config['telegram']['token'])
    for post in posts:
        post_text = reformat_post_text(config, post, 'tg')
        
        medias = list()

        for photo in post.photos:
            medias.append(telebot.types.InputMediaPhoto(media=open(photo.file_path, 'rb')))
        
        medias[0].caption = post_text
        medias[0].parse_mode = 'markdown'
        
        bot.send_media_group(config['telegram']['channel_id'], medias)
        logger.info(f"Post id={post.id} ({len(medias)} photos) reposted to Telegram channel {config['telegram']['channel_id']}")

if __name__ == '__main__':
    import yaml
    from autoposter_vk import get_new_vk_posts

    os.chdir(os.path.dirname(__file__))

    with open('config.yaml', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    os.makedirs(config['temp_dir'], exist_ok=True)

    config['telegram']['channel_id'] = -1002282539965
    new_posts = sorted(get_new_vk_posts(config), key=lambda post: post.id)
    repost_to_tg(config, new_posts)
    
    