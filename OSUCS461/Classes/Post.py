from OSUCS461.Models import UserPost
from OSUCS461.Classes.Database import DB
from datetime import datetime

tables = DB.GetTables()
post_table = tables[1]

class PostClass:
    def __init__(self):
        self.ids = []

    def get_posts(self):
        return DB.GetWhere(post_table)

    def add_to_db(self, user_data):
        if self.ids:
            new_id = self.ids[-1] + 1
        else:
            new_id = 0
        time_now = datetime.now()
        new_post = UserPost(time_created=time_now, uuid=new_id, **user_data.model_dump())
        DB.Add(post_table, new_post.model_dump())
        self.ids.append(new_id)
        return new_post