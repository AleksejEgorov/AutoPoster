'''
This is main module for autoposter
'''

import os
import time
import logging
import yaml
from autoposter_common import write_last_id, cleanup_content, get_photo_tags
from autoposter_vk import get_new_vk_posts
from autoposter_tg import repost_to_tg
from autoposter_inst import repost_to_instagram


def repost_cycle(config: dict, logger: logging.Logger) -> None:
    '''General cycle: import from VK, repost to TG and IG'''
    if config['source'] == 'vk':
        logger.debug('Getting new posts from VK')
        try:
            new_posts = sorted(get_new_vk_posts(config), key=lambda post: post.id)
        except Exception as err:
            logger.error('Cannot get posts from VK: %s', err)
            return
    else:
        logger.error(f'Source {config['source']} is unknown')
        return

    if new_posts:
        repost_status = {'vk': False, 'tg': False, 'inst': False}

        repost_status[config['source']] = True
        logger.info(f'Source is {config['source']}, reposting to {repost_status.keys()}')
        while False in repost_status.values():
            # To Telegram
            if not repost_status['tg']:
                try:
                    repost_to_tg(config, new_posts)
                    repost_status['tg'] = True
                except Exception as err:
                    logger.error('Error while reposting to Telegram: %s', err)
                    time.sleep(5)
            # To instagram
            # Maybe number of attempts
            if not repost_status['inst']:
                try:
                    get_photo_tags(config, new_posts)
                    repost_to_instagram(config, new_posts)
                    repost_status['inst'] = True
                except Exception as err:
                    logger.error('Error while reposting to Instagram: %s', err)
                    time.sleep(5)

        write_last_id(config, new_posts[-1].id)
        cleanup_content(config, new_posts)

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    with open('config.yaml', encoding='utf-8') as config_file:
        main_config = yaml.load(config_file, Loader=yaml.FullLoader)

    main_logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=str(main_config['log_level']).upper(),
        format=main_config['log_format']
    )
    main_logger.info('Autoposter started')


    os.makedirs(main_config['temp_dir'], exist_ok=True)

    while True:
        repost_cycle(main_config, main_logger)
        main_logger.debug('Sleep %s', {main_config['pool_interval']})
        time.sleep(main_config['pool_interval'])
