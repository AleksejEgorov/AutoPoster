'''
This class describes photo in post
'''
import logging
import requests
from time import sleep
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

class Photo:
    '''
    This class describes photo in post
    '''
    def __init__(self, photo_id, file_path: str, url: str):
        ''' New photo '''
        self.__id = photo_id
        self.__file_path = file_path
        self.__url = url
        self.__tags = []
        self.__squared_file_path = None

    @property
    def url(self):
        ''' Return photo url '''
        return self.__url

    @property
    def tags(self):
        ''' Return photo tags '''
        return self.__tags

    @tags.setter
    def tags(self, tags: list[str]):
        ''' Set photo tags '''
        self.__tags = tags

    def get_immaga_tags(self, config) -> list[str]:
        '''
        Receive photo tags from immaga.com
        '''
        immaga_auth = (config['imagga']['api_key'], config['imagga']['api_secret'])

        logger.debug(print('Processing photo %s', self.__id))

        attempts_left = 3
        need_retry = True
        tag_response = None

        while attempts_left > 0 and need_retry:
            attempts_left -= 1
            try:
                with open(self.__file_path, 'rb') as image:
                    tag_response = requests.post(
                        'https://api.imagga.com/v2/tags',
                        auth=immaga_auth,
                        files={'image': image},
                        timeout=config['imagga']['timeout']
                    )

                logger.info(
                    '%s tags received for photo %s',
                    len(tag_response.json()['result'].get('tags')),
                    self.__id
                )
            except requests.exceptions.ConnectionError as err:
                logger.warning(
                    '%s error receiving tags for photo %s (attempts left %s): %s',
                    type(err),
                    self.__id,
                    attempts_left,
                    err
                )
                if attempts_left == 0:
                    logger.error('All attempts to receive tags for photo %s failed', self.__id)
                    raise
                sleep(30)
            except Exception as err:
                logger.error(
                    '%s Error receiving tags for photo %s: %s',
                    type(err),
                    self.__id,
                    err
                )
                raise
            need_retry = False

        if tag_response is None:
            logger.error(
                'Error receiving tags for photo %s: %s',
                self.__id,
            )
            raise

        photo_tags = tag_response.json()['result'].get('tags')
        tags_string = ', '.join(
            set(
                tag_data['tag']['en'] for tag_data in sorted(
                    photo_tags,
                    key=lambda tag_data: tag_data['confidence'],
                    reverse=True
                )
            )
        )

        logger.info('Photo %s tags are: %s', self.__id, tags_string)

        for tag in photo_tags:
            self.__tags.append(tag['tag']['en'])
        logger.debug('tags: %s', self.__tags)
        return self.__tags


    def squarefy(self, size: int, color: str):
        '''
        Create sqare image with white fields. For IG
        '''
        photo = Image.open(self.__file_path)
        resized_photo = ImageOps.contain(photo, (size, size))
        logger.debug('Photo %s resized to %s', self.__file_path, resized_photo.size)
        squared_photo = ImageOps.pad(resized_photo, (size, size), color=color)
        logger.debug(
            'Photo %s squared to %s and filled with %s',
            self.__file_path,
            squared_photo.size,
            color
        )
        self.__squared_file_path  = self.__file_path.replace('.jpg','_inst.jpg')
        squared_photo.save(self.__squared_file_path )
        logger.debug('Squared photo saved to %s', self.__squared_file_path)
        return self.__squared_file_path
