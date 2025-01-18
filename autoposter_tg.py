import os
import logging
import telebot
# from telethon import TelegramClient, sync
# from autoposter_common import make_content_dir, get_last_id
from autoposter_classes import Post
from autoposter_common import reformat_post_text 


logger = logging.getLogger(__name__)

# TODO: It works, but sometimes logoff me from all telegram devices. Maybe later...
# def get_new_tg_posts(config):
#     client = TelegramClient('autoposter.session', config['telegram']['api_id'], config['telegram']['api_hash'])
#     posts = []
#     last_id = get_last_id(config)
#     content_dir = make_content_dir(config)

#     async def get_new_messages():
#         async for message in client.iter_messages(config['telegram']['channel_id'], limit=100):
#             if message.date.timestamp() <= last_id:
#                 continue
            
#             current_post = None
#             photo_file_path = None
#             message_date = int(message.date.timestamp())            
#             logger.info(f'Processing tg message id={message.id}, grouped_id={message.grouped_id}, date={message_date}, text="{message.text}"')
#             photo_file_path = os.path.join(content_dir, f'{message_date}', f'{message.id}.jpg')

#             current_post = list(filter(lambda post: post.id == message_date, posts))
#             if current_post:
#                 current_post = current_post[0]
#             else:
#                 current_post = Post(message_date)
#                 posts.append(current_post)    

#             if message.text != '':
#                 current_post.text = message.text

#             current_post.add_photo(message.id, await client.download_media(message, file=photo_file_path))

#     with client:
#         client.loop.run_until_complete(get_new_messages())

#     if __name__ == '__main__' and not posts:
#         logger.debug('No new posts from tg')

#     return posts


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

if __name__ == '__main__':
    import yaml
    from autoposter_vk import get_new_vk_posts

    os.chdir(os.path.dirname(__file__))

    with open('config.yaml', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    os.makedirs(config['temp_dir'], exist_ok=True)

    #new_posts = get_new_tg_posts(config)

    #print(json.dumps(new_posts, cls=PostEncoder))
    config['telegram']['channel_id'] = -1002282539965
    new_posts = sorted(get_new_vk_posts(config), key=lambda post: post.id)
    repost_to_tg(config, new_posts)
    
    