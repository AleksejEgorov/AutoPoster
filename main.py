import sys
import yaml
import json
import os
from autoposter_classes import PostEncoder
from autoposter_tg import get_new_tg_posts, repost_to_tg
from autoposter_vk import get_new_vk_posts

def main():
    with open('config.yaml', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
    
    os.makedirs(config['temp_dir'], exist_ok=True)
    if config['source'] == 'tg':
        new_posts = sorted(get_new_tg_posts(config), key=lambda post: post.id)
    elif config['source'] == 'vk':
        new_posts = sorted(get_new_vk_posts(config), key=lambda post: post.id)
        repost_to_tg(config, new_posts)
        
    else:
        print('Unknown source', file=sys.stderr)
        return
    
    return new_posts
    

    
if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    print(json.dumps(main(), cls=PostEncoder))