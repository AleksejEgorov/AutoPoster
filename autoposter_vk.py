import os
import vk
import urllib.request
from autoposter_classes import Post,PostEncoder
from autoposter_common import get_last_id, write_last_id, make_content_dir

def get_new_vk_posts(config):
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
        print('No new VK posts')
        return posts
    
    for post in new:
        if 'attachments' in post:
            current_post = Post(post['date'])
            current_post.text = post['text']
            print(f'Processing VK post id={post['id']}, date={post['date']}, text="{post['text']}"')
            
            post_dir = os.path.join(content_dir, str(post['date']))
            os.makedirs(post_dir, exist_ok=True)
            photos = list(map(lambda photo_data: photo_data['photo'], filter(lambda attachment: attachment['type'] == 'photo', post['attachments'])))
            
            for photo in photos:
                photo_url = photo['orig_photo']['url']
                photo_file = os.path.join(post_dir,f'{photo['id']}.jpg')
                urllib.request.urlretrieve(photo_url, photo_file)
                
                if __name__ == '__main__':
                    print(photo_file)
                    
                current_post.add_photo(photo['id'], photo_file)
            
            posts.append(current_post)
            
    return posts


def repost_to_vk(config, posts):
    vk_api = vk.API(access_token=config['vk']['token'])
    for post in posts:
        photos = list(map(lambda photo: photo.file_path, post.photos))
        try:
            vk_api.wall.post(owner_id=config['vk']['group_id'], attachments=photos, message=post.text)
        except Exception as e:
            print(f'Error while sending post {post.id}: {e}')
    
    
if __name__ == '__main__':
    import yaml
    import os
    import json
        
    os.chdir(os.path.dirname(__file__))
    
    with open('config.yaml', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
    
    os.makedirs(config['temp_dir'], exist_ok=True)
    
    new_posts = get_new_vk_posts(config)
    print(json.dumps(new_posts, cls=PostEncoder))

