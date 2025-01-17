import json

class Photo:
    def __init__(self, id, file_path: str):
        self.id = id
        self.file_path = file_path
        self.tags = []
        
class Post:
    def __init__(self, post):
        if isinstance(post, dict):
            self.id = post.get('id')
            self.text = post.get('text')
            self.tags = post.get('tags')
            self.source = post.get('source')
            self.photos = []
            for photo_dict in post.get('photos'):
                photo = Photo(photo_dict['id'], photo_dict['file_path'])
                photo.tags = photo_dict['tags']
                self.photos.append(photo)
        else:
            self.id = post
            self.text = ''
            self.tags = []
            self.photos = []
            self.source = None

    def add_photo(self, id: int, file: str ) -> None:
        self.photos.append(Photo(id, file))
        
    def __str__(self):
        return f'{self.id} {self.text} ({len(self.photos)} photos)'
    
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)
    
class PostEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__