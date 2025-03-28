'''
This module contains VK related functions
'''
import os
import logging
import urllib.request
import vk
from autoposter_classes import Post#,PostEncoder
from autoposter_common import get_last_id, make_content_dir

logger = logging.getLogger(__name__)

def get_new_vk_posts(config):
    '''Return new VK posts as list of Post objects'''
    content_dir = make_content_dir(config)
    posts = []
    last_id = get_last_id(config)
    vk_api = vk.API(access_token=config['vk']['token'])

    offset = 0

    new = list(
        filter(
            lambda post: post['date'] > last_id,
            vk_api.wall.get(
                owner_id=config['vk']['group_id'],
                count=100,
                v='5.199',
                filter='owner',
                offset=offset
            )['items']
        )
    )

    if not new:
        logger.debug('No new VK posts')
        return posts

    for post in new:
        if 'attachments' in post:
            current_post = Post(post['date'])
            current_post.text = post['text']
            logger.info(
                'Processing VK post id=%s, date=%s, text="%s", %s attachments',
                post['id'],
                post['date'],
                post['text'],
                len(post['attachments'])
            )

            post_dir = os.path.join(content_dir, str(post['date']))
            os.makedirs(post_dir, exist_ok=True)
            logger.debug(
                'Post content will be saved to %s',
                post_dir
            )
            photos = list(
                map(
                    lambda photo_data: photo_data['photo'],
                    filter(
                        lambda attachment: attachment['type'] == 'photo',
                        post['attachments']
                    )
                )
            )
            for photo in photos:
                photo_url = photo['orig_photo']['url']
                photo_file = os.path.join(post_dir,f'{photo['id']}.jpg')
                urllib.request.urlretrieve(photo_url, photo_file)
                logger.debug(
                    'Photo %s saved to %s',
                    photo['id'],
                    photo_file
                )
                current_post.add_photo(photo['id'], photo_file)

            posts.append(current_post)

    return posts


# if __name__ == '__main__':
#     import yaml
#     import json

#     os.chdir(os.path.dirname(__file__))

#     with open('config.yaml', encoding='utf-8') as config_file:
#         app_config = yaml.load(config_file, Loader=yaml.FullLoader)

#     os.makedirs(app_config['temp_dir'], exist_ok=True)

#     new_posts = get_new_vk_posts(app_config)
#     print(json.dumps(new_posts, cls=PostEncoder))
