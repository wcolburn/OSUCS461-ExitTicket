from OSUCS461.Models import User, UserPost
from OSUCS461.Classes.Database import DB
from datetime import datetime

tables = DB.GetTables()
user_table = tables[0]

class UserClass:
    def __init__(self):
        pass

    def add_to_db(self, user_data):
        time_now = datetime.now()
        new_user = User(time_created=time_now, last_seen=time_now, **user_data.model_dump())
        DB.Add(user_table, new_user.model_dump())
        return new_user

    def get_users(self):
        return DB.GetWhere(user_table)

    def get_user(self, user_id):
        params = {"uuid":user_id}
        return DB.GetBy(user_table, params)
