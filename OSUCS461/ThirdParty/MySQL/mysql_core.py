_scriptname = 'ThirdParty.MySQL.mysql_core'

import os
import mariadb
from copy import deepcopy
import traceback
from functools import wraps


IS_CONSUMER = os.environ.get("IS_CONSUMER", "false")
if IS_CONSUMER.lower() == 'true':
	pool_size = 10
else:
	pool_size = 20
 
# logger = custom_logger("MySQL", "mysql_wrapper_logs.log")
# 
# 
# def log_query_details(func):
# 	@wraps(func)
# 	def class_wrapper(self, *args, **kwargs):
# 		script_func = (f"{_scriptname}.{func.__name__}")
# 		logger.info(f"{script_func}: Arguments: args={args}, kwargs={kwargs}")
# 		try:
# 			result = func(self, *args, **kwargs)
# 			logger.info(f"{script_func}: Returned Value - {result}")
# 			return result
# 		except Exception as e:
# 			logger.error(f"{script_func}: Error - {e} - \nStack Trace: {traceback.format_exc()}")
# 	return class_wrapper


class mysql_core:
	def __init__(
		self,
		host="127.0.0.1",
		port=3306,
		user=None,
		password="",
		db=None,
		pool_name="",
		pool_size=pool_size,
	):
		self.creds = {
			"host": host,
			"port": port,
			"user": user,
			"password": password,
			"db": db,
		}

		self.pool = mariadb.ConnectionPool(
			pool_name=pool_name,
			pool_size=pool_size,
			pool_validation_interval=250,
			**self.creds
		)

# 	@log_query_details
	def create(self, query):
		create_creds = deepcopy(self.creds)
		del create_creds["db"]

		try:
			with self.pool.get_connection() as con:
				cursor = con.cursor()
				result = cursor.execute(query)
				return result
		except:
			return None

# 	@log_query_details
	def query(self, query):
		try:
			with self.pool.get_connection() as con:
				cursor = con.cursor()
				cursor.execute(query)
				count = cursor.rowcount  # added to get accurate count
				con.commit()

				if query.find("insert") == 0 or query.find("replace") == 0:
					result = {
						"insert_id": cursor.lastrowid,  # only for auto_increment
						"affected_rows": count,
					}

				elif query.find("delete") == 0:
					if count == 0:
						result = {
							"request": "delete",
							"result": False,
							"affected_rows": count,
						}
					elif count >= 1:
						result = {
							"request": "delete",
							"result": True,
							"affected_rows": count,
						}
				else:
					result = True

				return result
		except Exception as inst:
			print("mysql_core.query.ERROR:", inst, query)
			return None

# 	@log_query_details
	def _get(self, query, cursor_action, override=False):
		try:
			with self.pool.get_connection() as con:
				cursor = con.cursor(prepared=True, dictionary=True)
				cursor.execute(query)
				result = None

				if cursor_action == "fetchall":
					result = cursor.fetchall()
				elif cursor_action == "fetchone":
					result = cursor.fetchone()
				elif cursor_action == "fetchmany":
					result = cursor.fetchmany()

				cursor.close()

				return self.unescape_strings(result)

		except Exception as inst:
			print("mysql_core._get.ERROR:", inst, query)
			return None

# 	@log_query_details
	def get_count(self, query):
		try:
			with self.pool.get_connection() as con:
				cursor = con.cursor(prepared=True)
				cursor.execute(query)
				result = cursor.fetchone()[0]

				cursor.close()

				return result

		except Exception as inst:
			print("mysql_core._get.ERROR:", inst, query)
			return None

# 	@log_query_details
	def run(self, query):
		try:
			with self.pool.get_connection() as con:
				cursor = con.cursor()
				cursor.execute(query)
				con.commit()
		except Exception as inst:
			print("mysql_core.run.ERROR:", inst, query)

# 	@log_query_details
	def get_results(self, query):
		return self._get(query, "fetchall")

# 	@log_query_details
	def get_row(self, query):
		return self._get(query, "fetchone")

	def escape_string(self, val):
		if type(val) is not str:
			return val

		with self.pool.get_connection() as con:
			escaped = con.escape_string(val)
			return escaped

	def unescape_strings(self, val):
		if isinstance(val, dict):
			return {key: self.unescape_strings(value) for key, value in val.items()}
		elif isinstance(val, list):
			return [self.unescape_strings(item) for item in val]
		elif isinstance(val, str):
			return val.replace("&#63", "?")
		else:
			return val


# 	@log_query_details
	def get_var(self, query, override=False):
		try:
			with self.connect(**self.creds) as con:
				cursor = con.cursor()
				cursor.execute(query)
				result = cursor.fetchone()
				return result[0] if result else None
		except:
			return None
