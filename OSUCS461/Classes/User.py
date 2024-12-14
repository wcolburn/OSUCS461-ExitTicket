from OSUCS461.Models import User
from OSUCS461.Classes.Database import DB
from datetime import datetime

tables = DB.GetTables()
user_table = tables[0]

class UserClass:
    def __init__(self):
        self.ids = []

    def add_to_db(self, user_data):
        if self.ids:
            new_id = self.ids[-1] + 1
        else:
            new_id = 0
        time_now = datetime.now()
        new_user = User(time_created=time_now, last_seen=time_now, uuid=new_id, **user_data.model_dump())
        DB.Add(user_table, new_user.model_dump())
        self.ids.append(new_id)
        return new_user

    def get_users(self):
        return DB.GetWhere(user_table)

    def get_user(self, user_id):
        params = {"uuid":user_id}
        return DB.GetBy(user_table, params)

    def update_user(self, uuid, user_data):
        params = {"uuid": uuid}
        new_params = user_data.model_dump()
        DB.Update(user_table, new_params, field_params=params)
        user = DB.GetBy(user_table, params)
        return user

    def delete_user(self, user_id):
        params = {"uuid":user_id}
        return DB.DeleteWhere(user_table, params)