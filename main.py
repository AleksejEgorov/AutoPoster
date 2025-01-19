import yaml
import os
import time
import logging
from autoposter_common import write_last_id, cleanup_content, get_photo_tags
from autoposter_vk import get_new_vk_posts, repost_to_vk
from autoposter_tg import repost_to_tg
from autoposter_inst import repost_to_instagram


def repost_cycle(config: dict) -> None:
    if config['source'] == 'vk':
        logger.debug('Getting new posts from VK')
        new_posts = sorted(get_new_vk_posts(config), key=lambda post: post.id)
    else:
        logger.error(f'Source {config['source']} is not unknown')
        new_posts = None
    
    if new_posts:
        repost_status = {
            'vk': False,
            'tg': False,
            'inst': False
        }
        
        repost_status[config['source']] = True
        logger.info(f'Source is {config['source']}, reposting to {repost_status.keys()}')
        while False in repost_status.values():  
            # To Telegram
            if not repost_status['tg']:
                try:
                    repost_to_tg(config, new_posts)
                    repost_status['tg'] = True
                except Exception as e:
                    logger.error(f'Error while reposting to Telegram: {e}')
                    time.sleep(5)
            # To instagram
            if not repost_status['inst']:
                try:
                    get_photo_tags(config, new_posts)
                    repost_to_instagram(config, new_posts)
                    repost_status['inst'] = True
                except Exception as e:
                    logger.error(f'Error while reposting to Instagram: {e}')
                    time.sleep(5)
            
        write_last_id(config, new_posts[-1].id)
        cleanup_content(config, new_posts)

    
if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    with open('config.yaml', encoding='utf-8') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)
    
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=str(config['log_level']).upper(), 
        format=config['log_format']
    )
    logger.info('Autoposter started')
    
    
    os.makedirs(config['temp_dir'], exist_ok=True)
    
    while True:
        repost_cycle(config)
        logger.debug(f'Sleep {config['pool_interval']}')
        time.sleep(config['pool_interval'])
        
    