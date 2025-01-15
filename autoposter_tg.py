import os
from telethon import TelegramClient, sync
from autoposter_classes import Post, PostEncoder
from autoposter_common import get_last_id, write_last_id, make_content_dir


def get_new_tg_posts(config):
    client = TelegramClient('autoposter.session', config['telegram']['api_id'], config['telegram']['api_hash'])
    posts = []
    last_id = get_last_id(config, 'tg')
    content_dir = make_content_dir(config, 'tg')

    async def get_new_messages():
        async for message in client.iter_messages(config['telegram']['channel_id'], min_id=last_id):
            current_post = None
            photo_file_path = None
            print(f'Processing tg message id={message.id}, grouped_id={message.grouped_id}, text="{message.text}"')

            if message.grouped_id is not None:
                current_post = list(filter(lambda post: post.id == message.grouped_id, posts))
                if current_post:
                    current_post = current_post[0]
                else:
                    current_post = Post(message.grouped_id)
                    current_post.last_message_id = message.id
                    posts.append(current_post)

                photo_file_path = os.path.join(content_dir, f'{message.grouped_id}', f'{message.id}.jpg')
            else:
                current_post = Post(message.id)
                photo_file_path = os.path.join(content_dir, f'{message.id}.jpg')
                posts.append(current_post)

            if message.text != '':
                current_post.text = message.text

            current_post.add_photo(message.id, await client.download_media(message, file=photo_file_path))

    with client:
        client.loop.run_until_complete(get_new_messages())

    if not posts:
        print('No new posts')
        return posts

    if posts[0].last_message_id is not None:
        write_last_id(config, 'tg', posts[0].last_message_id)
    else:
        write_last_id(config, 'tg', posts[0].id)

    return posts


def repost_to_tg(config, posts):
    with sync.TelegramClient('autoposter.session', config['telegram']['api_id'], config['telegram']['api_hash']) as client:
        for post in posts:
            photos = list(map(lambda photo: photo.file_path, post.photos))
            try:
                client.send_file(config['telegram']['channel_id'], photos, caption=post.text, parse_mode='markdown')
                print(f"Post id={post.id} ({len(photos)} photos) reposted to Telegram channel {config['telegram']['channel_id']}")
            except Exception as e:
                print(f'Error while sending post {post.id}: {e}')
    return


if __name__ == '__main__':
    import yaml
    import json

    os.chdir(os.path.dirname(__file__))

    with open('config.yaml', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    os.makedirs(config['temp_dir'], exist_ok=True)

    new_posts = get_new_tg_posts(config)

    print(json.dumps(new_posts, cls=PostEncoder))

