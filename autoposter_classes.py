import json

class Photo:
    def __init__(self, id, file_path: str):
        self.id = id
        self.file_path = file_path
        self.tags = None
        
class Post:
    def __init__(self, post_id):
        self.id = post_id
        self.text = ''
        self.tags = []
        self.photos = []
        self.last_message_id = None
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