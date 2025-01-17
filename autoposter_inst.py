import sys
import os
import instagrapi
import random
from PIL import Image, ImageOps
from autoposter_classes import Post
import requests

def squarefy_photo(photo_path: str, size: int, color: str):
    photo = Image.open(photo_path)
    resized_photo = ImageOps.contain(photo, (size, size))
    squared_photo = ImageOps.pad(resized_photo, (size, size), color=color)
    squared_photo_path = photo_path.replace('.jpg','_inst.jpg')
    squared_photo.save(squared_photo_path)
    return squared_photo_path

def get_photo_tags(config, posts: list[Post]):
    immaga_auth = (config['imagga']['api_key'], config['imagga']['api_secret'])

    for post in posts:
        if __name__ == '__main__':
            print(f'Processing post {post.id}')
        
        for photo in post.photos:
            if __name__ == '__main__':
                print(f'Photo {photo.id}')
            
            tag_response = requests.post(
                'https://api.imagga.com/v2/tags',
                auth=immaga_auth,
                files={'image': open(photo.file_path, 'rb')}
            )

            for tag in tag_response.json()['result'].get('tags'):
                photo.tags.append(tag['tag']['en'])
            if __name__ == '__main__':
                print('tags: ', photo.tags)
            post.tags.extend(photo.tags)
            
def repost_to_instagram(config: dict, posts: list[Post]) -> None:    
    # inst = instagrapi.Client(proxy=config['instagram']['proxy'])
    # inst.login(username=config['instagram']['username'], password=config['instagram']['password'])
    
    for post in posts:
        # prepare tag list:
        tags = config['instagram']['default_tags']      
        post_tags = random.sample(list(filter(lambda tag: ' ' not in tag, post.tags)), config['instagram']['total_tags_count'] - len(tags))
        tags.extend(post_tags)
        tags = list(map(lambda tag: f'#{tag}', tags))
        inst_text = f'{post.text}\n{" ".join(tags)}'
        if __name__ == '__main__':
            print(inst_text)
        # prepare photo list
        inst_photos = []
        for photo in post.photos:
            inst_photos.append(squarefy_photo(photo.file_path, 1280, config['instagram']['fill_color']))
        if __name__ == '__main__':
            print(inst_photos)
        # try:
        #     inst.photo_upload()
        # except Exception as e:
        #     print(f'Instagram post error: {e}', file=sys.stderr)
    # inst.logout()
    
    

        
        
if __name__ == '__main__':
    import yaml
    import os
    import json
    from autoposter_vk import get_new_vk_posts
    from autoposter_classes import PostEncoder
        
    os.chdir(os.path.dirname(__file__))
    
    with open('config.yaml', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
    
    # new_posts = get_new_vk_posts(config)
    # get_photo_tags(config, new_posts)
    
    with open(os.path.join(config['temp_dir'], 'test_post.json'), encoding='utf-8') as json_post:
        new_posts = json.load(json_post)
    
    posts = list(map(lambda post: Post(post), new_posts))
        
    repost_to_instagram(config, posts)
    print(json.dumps(new_posts, cls=PostEncoder))