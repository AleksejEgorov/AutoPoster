'''
This module describes classes, used in autoposter
'''

import json

class Photo:
    '''
    This class describes photo in post
    '''
    def __init__(self, photo_id, file_path: str, url: str):
        self.id = photo_id
        self.file_path = file_path
        self.url = url
        self.tags = []

class Post:
    '''
    This class describes post with one or more photos in it
    '''
    def __init__(self, post):
        if isinstance(post, dict):
            self.id = post.get('id')
            self.text = post.get('text')
            self.tags = post.get('tags')
            self.source = post.get('source')
            self.photos = []
            for photo_dict in post.get('photos'):
                photo = Photo(photo_dict['id'], photo_dict['file_path'], photo_dict['url'])
                photo.tags = photo_dict['tags']
                self.photos.append(photo)
        else:
            self.id = post
            self.text = ''
            self.tags = []
            self.photos = []
            self.source = None

    def add_photo(self, photo_id: int, file: str, url: str ) -> None:
        "Add photo to post"
        self.photos.append(Photo(photo_id, file, url))

    def __str__(self):
        return f'{self.id} {self.text} ({len(self.photos)} photos)'

    def to_json(self):
        '''converts post to serializable json'''
        return json.dumps(self, default=lambda o: o.__dict__)

class PostEncoder(json.JSONEncoder):
    '''Service class'''
    def default(self, o):
        return o.__dict__
