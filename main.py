'''
This is main module for autoposter
'''

import os
import time
import logging
import yaml
from requests import exceptions as WebErrors
from autoposter_common import write_last_id, cleanup_content
from autoposter_vk import get_new_vk_posts


def repost_cycle(config: dict, logger: logging.Logger) -> None:
    '''General cycle: import from VK, repost to TG and IG'''
    if config['source'] == 'vk':
        logger.debug('Getting new posts from VK')
        try:
            new_posts = sorted(get_new_vk_posts(config), key=lambda post: post.id)
        except WebErrors.ReadTimeout as err:
            logger.warning('VK API timeout %s', err)
            return
        except Exception as err:
            logger.error('%s: Cannot get posts from VK: %s', type(err), err)
            raise
    else:
        logger.error(f'Source {config['source']} is unknown')
        return


    for post in new_posts:
        logger.debug('Post %s has %s photos', post.id, len(post.photos))

        need_to_repost = {
            'vk': False,
            'telegram': False,
            'instagram': False
        }

        for target in need_to_repost:
            need_to_repost[target] = config[target]['enabled']

        need_to_repost[config['source']] = True
        logger.info(
            'Source is %s, reposting to %s',
            config['source'],
            need_to_repost.keys()
        )

        try:
            post.add_tags(config=config)
        except Exception as err:
            logger.error('%s: Error while adding tags to post %s: %s', type(err), post.id, err)
            raise

        while True in need_to_repost.values():
            # To Telegram
            if need_to_repost['telegram']:
                try:
                    post.repost_to_tg(config)
                except Exception as err:
                    logger.error('%s: Error while reposting to Telegram: %s', type(err), err)
                    time.sleep(5)
                    raise

                need_to_repost['telegram'] = False

            # To instagram
            if need_to_repost['instagram']:
                attempts_left = 3
                while attempts_left > 0 and need_to_repost['instagram'] == True:
                    attempts_left -= 1
                    try:
                        post.repost_to_instagram(config)
                    except Exception as err:
                        logger.error('%s: Error while reposting to Instagram: %s', type(err), err)
                        time.sleep(15)
                        if attempts_left == 0:
                            logger.error('No attempts left, skip reposting to Instagram')
                            raise

                need_to_repost['instagram'] = False

        write_last_id(config, post.id)
        cleanup_content(config, posts=[post])

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
