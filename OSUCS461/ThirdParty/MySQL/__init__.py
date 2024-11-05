_scriptname = 'ThirdParty.MySQL'

from json import loads
from copy import deepcopy
from .mysql_core import mysql_core
from .mysql_functions import mysql_functions

from OSUCS461.Utilities import (
	createHash,
	isNumber,
	isUnicode,
	isList,
	bisectSearchRC,
)

"""
	for the sake of keeping things very manageable in the first version we will only have the
	following types available:
		int
		varchar(len)
		text
		double
		timestamp
		tinyint(1) - for boolean-esque values

NOTE:	right now we cannot handle likes and there's really no way to pass field comparisons in for the wheres
"""


class MySQL(mysql_core):
	def __init__(self, host="127.0.0.1", port=3306, user="root", passwd="", db=None):
		mysql_core.__init__(self, host, port, user, passwd, db)
		self.CreateDatabase(db)

	def CreateDatabase(self, name):
		return self.create("CREATE DATABASE IF NOT EXISTS %s;" % name)

	def DropDatabase(self, name):
		return self.get_results("drop database %s;" % name)

	def GetTables(self):
		tables = self.get_results("show tables")
		if tables:
			return [list(table.values())[0] for table in tables]

	Tables = property(GetTables)

	def DescribeTable(self, table, raw=False):
		columns = self.get_results("desc %s" % table)
		if columns and raw is True:
			return columns
		elif columns:
			return [self._mapDescribeColumn(c) for c in columns]

	def _options(self, options):
		ret = []
		for k, v in list(options.items()):
			key = k.lower()
			value = None

			if key == "allow_null" and v is True:
				value = "NULL"
			elif key == "allow_null":
				value = "NOT NULL"
			elif key == "primary_key" and v is True:
				value = "PRIMARY KEY"
			elif key == "auto_increment" and v is True:
				value = k
			elif key == "default_value":
				value = "default %s" % v

			if value:
				ret.append(value)

		return " ".join(ret)

	def _mapDescribeColumn(self, oc):
		mapped_old = {"name": oc["Field"], "type": oc["Type"]}

		if mapped_old["type"].find("(") != -1:
			mapped_old["type"], mapped_old["length"] = mapped_old["type"][:-1].split(
				"("
			)
			if mapped_old["type"] == "int":
				del mapped_old["length"]
			else:
				mapped_old["length"] = int(mapped_old["length"])

		options = {}
		if oc["Extra"] and oc["Extra"].lower() == "auto_increment":
			options["auto_increment"] = True
		if oc["Default"]:
			options["default_value"] = oc["Default"]
		if oc["Key"] and oc["Key"].lower() == "pri":
			options["primary_key"] = True

		if oc["Null"] and oc["Null"].lower() == "yes":
			options["allow_null"] = True
		elif oc["Null"]:
			options["allow_null"] = False

		mapped_old["options"] = options
		return mapped_old

	def ModifyTable(self, table, columns):
		old_schema = self.DescribeTable(table, True)
		keyed_old = self.MakeKeyedObject(old_schema, "Field")
		keyed_new = self.MakeKeyedObject(columns, "name")

		add = []
		typecast = []
		change = []
		omit_from_drop = []
		for k, v in list(keyed_new.items()):
			if "old_name" in v:
				if v["old_name"] in keyed_old:
					change.append(v)
					omit_from_drop.append(v["old_name"])

			elif k in keyed_old:
				oc = keyed_old[k]  # old column
				mapped_old = self._mapDescribeColumn(oc)

				if "options" not in v:
					v["options"] = {}
				if (
					"allow_null" in mapped_old["options"]
					and "allow_null" not in v["options"]
				):
					v["options"]["allow_null"] = mapped_old["options"]["allow_null"]
				elif "primary_key" in v["options"]:
					v["options"]["allow_null"] = False
				if not mapped_old == v:
					col = deepcopy(v)
					if "options" in col and "primary_key" in col["options"]:
						del col["options"]["primary_key"]
					typecast.append(col)

			else:
				add.append(v)

		new_keys = list(keyed_new.keys())
		drop = [
			k
			for k in list(keyed_old.keys())
			if k not in new_keys and k not in omit_from_drop
		]
		if len(add) > 0:
			for c in add:
				print(self.AlterTable(table, "add", c))
		if len(change) > 0:
			for c in change:
				print(self.AlterTable(table, "change", c))
		if len(drop) > 0:
			for c in drop:
				print(self.AlterTable(table, "drop", {"name": c}))
		if len(typecast) > 0:
			for c in typecast:
				print(self.AlterTable(table, "typecast", c))

		return True

	def AlterTable(self, table, do, column):
		if do not in ["add", "drop", "typecast", "change"]:
			raise Exception("do must be add, drop, typecast or change. %s invalid" % do)

		name = column["name"]
		options = ""
		column_type = ""

		if do != "drop":
			column_type = column["type"]

		if do == "typecast":
			do = "modify"

		if do == "change":
			if "old_name" not in column or "name" not in column:
				raise Exception(
					"you must include both the old_name and name of column for change"
				)
			name = " ".join((column["old_name"], column["name"]))

		if "length" in column:
			column_type += "(%s)" % column["length"]
		elif column_type == "varchar" and "length" not in column:
			column_type += "(32)"

		if "options" in column:
			options = self._options(column["options"])

		query = (
			"%s;"
			% (
				"alter table %s %s column %s %s %s"
				% (table, do, name, column_type, options)
			).strip()
		)
		return self.query(query)

	def CreateTable(self, table, columns):
		print("CreateTable.columns: %s %s" % (table, repr(columns)))
		_fields = []
		uuid = False
		for c in columns:
			column_type = c["type"]
			options = ""

			if "length" in c:
				column_type += "(%s)" % c["length"]
			elif column_type == "varchar" and "length" not in c:
				column_type += "(32)"

			if "options" in c:
				options = self._options(c["options"])

			if c["name"] == "uuid":
				uuid = True

			_fields.append(" ".join((c["name"], column_type, options)).strip())

		if uuid is False:
			_fields.append("uuid varchar(56) NOT NULL")

		query = "create table %s(%s);" % (table, ", ".join(_fields))
		return self.query(query)

	def DropTable(self, table):
		query = "%s;" % ("drop table %s" % table).strip()
		return self.query(query)

	def RemapKey(self, data, old_key, new_key):
		data[new_key] = data[old_key]
		del data[old_key]
		return data

	def GetBy(self, table, field_params):
		wheres = self.ProcessWheres(field_params)
		if not wheres:
			return
		return self.get_row("select * from %s where %s;" % (table, wheres))

	def _AddReplace(self, table, data, do):
		print("MySQL._AddReplace.data:", data)
		if "uuid" not in data:
			data.uuid = createHash(table)

		column_names = []
		column_values = []
		for column, value in data.items():
			if value is not None:
				column_names.append(column)
				column_values.append(self._mapesc(value))
		action = "insert into" if do != "replace" else do
		query = f"{action} {table} ({','.join(column_names)}) values ({','.join(column_values)});"

		ret = self.query(query)

		if ret and "insert_id" in ret:
			ret["uuid"] = data["uuid"]

		return ret

	def Replace(self, table, data):
		return self._AddReplace(table, data, "replace")

	def Add(self, table, data):
		return self._AddReplace(table, data, "add")

	def BulkAdd(self, table, data_list, batch_size=1000):
		def generate_query(batch):
			columns = ', '.join(batch[0].keys())
			values = []
			for data in batch:
				value_str = ', '.join([f"'{str(value)}'" if value is not None else 'NULL' for value in data.values()])
				values.append(f"({value_str})")
			values_str = ',\n'.join(values)
			return f"INSERT INTO {table} ({columns})\nVALUES\n{values_str};"

		# insert in batches
		total_added = 0
		for i in range(0, len(data_list), batch_size):
			batch = data_list[i:i+batch_size]
			query = generate_query(batch)
			try:
				ret = self.query(query)
				if ret:
					total_added += len(batch)
				else:
					print(f"Error occurred in batch insert: {ret}")
			except Exception as e:
				print(f"Error occurred in batch insert: {e}")
		return total_added

	def QuadAdd(self, table, data, fields, primary_key):
		a_values = list(map(self._mapesc, data))
		query = "insert into %s (%s, %s) values " % (
			table,
			primary_key,
			",".join(fields),
		)
		query += "((if((select max(p.%s) from %s p) is NULL, 1, " % (primary_key, table)
		query += "(select max(p.%s)*2 from %s p))), %s);" % (
			primary_key,
			table,
			",".join(a_values),
		)
		return self.query(query)

	def Update(self, table, data, field_params, force=False):
		update = []
		data = {k: v for k, v in data.items() if v is not None}

		if force is False:
			old_entry = self.GetBy(table, field_params)
			print("MySQL.Update.old_entry:", old_entry)
			if old_entry is None:
				return old_entry
			DoesMatch = True
			for k, v in list(data.items()):
				if v is None:
					v = "null"

				if isNumber(v) or v.lower() == "null" or v.lower() == "now()":
					update.append("%s=%s" % (k, v))
				else:
					update.append("%s=%s" % (k, self._mapesc(v)))

				if True in (isUnicode(old_entry[k]), isUnicode(v)):
					oldEntry = old_entry[k]
					if oldEntry is not None:
						try:
							oldEntry.decode("utf-8")
						except:
							oldEntry = oldEntry.encode("utf-8")

						newEntry = v
						try:
							newEntry.decode("utf-8")
						except:
							newEntry = newEntry.encode("utf-8")

						if oldEntry != newEntry:
							DoesMatch = False

				elif old_entry is None or old_entry[k] != v:
					DoesMatch = False

			if DoesMatch:
				return True
		else:
			for k, v in list(data.items()):
				if v is None:
					v = "null"
				if isNumber(v) or v.lower() == "null" or v.lower() == "now()":
					update.append("%s=%s" % (k, v))
				else:
					update.append("%s=%s" % (k, self._mapesc(v)))

		if len(update) > 0:
			wheres = ""
			try:
				wheres = self.ProcessWheres(field_params)
			except Exception as inst:
				print("MySQL.Update.wheres.ERROR:", inst)
				wheres = field_params
			update_sql = "update %s set %s where %s;" % (
				table,
				",".join(update),
				wheres,
			)
			return self.query(update_sql)

	def UpdateVarWhere(self, table, sets, where_field, where_value):
		return self.query(
			"update %s set %s where %s = '%s';"
			% (table, sets, where_field, where_value)
		)

	def GetAll(self, table, orderby=None, orderby_dir="DESC", limit=None, offset=None, get_count=False):
		return self.GetAllWhere(
			table=table,
			orderby=orderby,
			orderby_dir=orderby_dir,
			limit=limit,
			offset=offset,
			get_count=get_count,
		)

	def GetOneWhere(self, table, field_params=None, joiner="and"):
		return self.get_row(
			self._makeGetWhereQuery(
				table=table, fields="*", field_params=field_params, joiner=joiner
			)
		)

	def GetWhere(
		self,
		table,
		fields="*",
		field_params=None,
		orderby=None,
		orderby_dir="DESC",
		joiner="and",
		limit=None,
		offset=None,
		get_count=False,
	):
		results = self.get_results(
			self._makeGetWhereQuery(
				table, fields, field_params, orderby, orderby_dir, joiner, limit, offset
			)
		)
		count = self.get_count(
			self._makeCountQuery(
				table, field_params, joiner
			)
		)
		results_plus = {"results": results, "count": count}

		if get_count:
			return results_plus

		return results

	def _makeCountQuery(
			self,
			table,
			field_params=None,
			joiner="and"
		):
			wheres = ""
			if field_params is not None:
				try:
					wheres = self.ProcessWheres(field_params, joiner)
				except:
					wheres = field_params

			if wheres:
				wheres = " where %s" % wheres

			count = "select count(*) from %s%s;" % (table, wheres)

			return count

	def _makeGetWhereQuery(
		self,
		table,
		fields,
		field_params=None,
		orderby=None,
		orderby_dir="DESC",
		joiner="and",
		limit=None,
		offset=None,
	):
		if fields != "*" and type(fields) is bytes:
			try:
				fields = ",".join(loads(fields))
			except:
				fields = [fields]

		if isList(fields):
			fields = ",".join(fields)

		wheres = ""
		if field_params is not None:
			try:
				wheres = self.ProcessWheres(field_params, joiner)
			except:
				wheres = field_params

		if wheres:
			wheres = " where %s" % wheres

		if orderby is None:
			orderby = ""
		else:
			orderby = " order by %s %s" % (orderby, orderby_dir)

		if limit is not None:
			limit = " limit " + str(limit)
		else:
			limit = ""
		if offset is not None:
			offset = " offset " + str(offset)
		else:
			offset = ""

		sql_query = "select %s from %s%s%s%s%s;" % (
			fields,
			table,
			wheres,
			orderby,
			limit,
			offset,
		)

		return sql_query

	def GetAllWhere(
		self,
		table,
		field_params=None,
		orderby=None,
		orderby_dir="DESC",
		joiner="and",
		limit=None,
		offset=None,
		get_count=False,
	):
		return self.GetWhere(
			table, "*", field_params, orderby, orderby_dir, joiner, limit, offset, get_count,
		)

	def GetManyByIds(
		self,
		table,
		fields,
		field,
		ids=None,
		orderby=None,
		orderby_dir="DESC",
		joiner="and",
	):
		if not ids:
			return []
		if type(ids) is bytes:
			try:
				ids = loads(ids)
			except:
				ids = [ids]
		ids = ",".join(["'%s'" % x for x in ids])

		return self.GetWhere(
			table,
			fields,
			"%s in (%s)" % (field, ids),
			orderby,
			orderby_dir,
			joiner
		)

	def DeleteWhere(self, table, field_params):
		wheres = self.ProcessWheres(field_params)
		if not wheres:
			return
		return self.query("delete from %s where %s;" % (table, wheres))

	def Delete(self, table):
		return self.query("delete from %s;" % table)

	def BulkDeleteWhere(self, table, field_params, batch_size=1000):

		# from ProcessWheres
		if type(field_params) in [bytes, str]:
			field_params = loads(field_params)
		if type(field_params) is dict:
			field_params = list(field_params.items())

		if type(field_params) is list:

			# same as criteria used by ProcessWheres to determine if a param is an IN clause
			IN_params = [param for param in field_params if len(param)>=2 and type(param[1]) is list]
			print(f'IN_params: {IN_params}' if IN_params and len(IN_params[0][1]) < batch_size else f'{len(IN_params[0][1])} items in first IN param found')

			# if there was just one IN param found and it had a huge batch of values to search for
			if len(IN_params)==1 and len(IN_params[0][1]) > batch_size:
				big_list = IN_params[0][1]
				print('big list ', big_list)
				smaller_lists = [big_list[i:i + batch_size] for i in range(0, len(big_list), batch_size)]
				print('smaller lists', smaller_lists)
				other_params = [param for param in field_params if param != IN_params[0]]
				print('other params ', other_params)
				new_sets_of_field_params = []
				for smaller_list in smaller_lists:
					new_list = other_params[:]
					print('new list ', new_list)
					new_list.append((IN_params[0][0], smaller_list))
					print('new list with batch of IN param ', new_list)
					new_sets_of_field_params.append(new_list)
				print('new sets of field params ', new_sets_of_field_params)
				affected_rows = 0
				last_query_response = None
				for set_of_field_params in new_sets_of_field_params:
					last_query_response = self.DeleteWhere(table, set_of_field_params)
					affected_rows += last_query_response.get('affected_rows', 0)
				if last_query_response.get('affected_rows'):
					last_query_response['affected_rows'] = affected_rows
					return last_query_response
				else:
					return {}

			# if there were no IN clauses, multiple IN clauses, or one IN clause but it was small
			else:
				print('there were no IN clauses, multiple IN clauses, or one IN clause but it was small')
				if len(IN_params) > 1 and any(len(param[1]) > batch_size for param in IN_params):
					print("Warning: This function doesn't currently have support to handle multiple large IN clauses in a query.")
					print("Invoking normal DeleteWhere, which may take a while or error if MySQL can't handle the large IN clause.")
				return self.DeleteWhere(table, field_params)

		else:
			return self.DeleteWhere(table, field_params)

	"""
		field_params can be either dict or list/tuples
		NEED: to add between support - http://dev.mysql.com/doc/refman/5.0/en/comparison-operators.html#function_greatest
	"""

	def ProcessWheres(self, field_params=None, joiner="and"):
		if not field_params:
			return ""
		if not joiner:
			joiner = "and"
		if type(field_params) in [bytes, str]:
			field_params = loads(field_params)
		if type(field_params) is dict:
			field_params = list(field_params.items())

		wheres = []
		for param in field_params:
			param = list(param)
			if len(param) == 2:
				param.append("=")
			field_name, field_value, field_comparison = param

			if isinstance(field_value, list):
				quoted_values = ",".join(f"'{v}'" for v in field_value)
				where_clause = f"{field_name} IN ({quoted_values})"
			else:
				sfv = str(field_value)
				if sfv.lower() in ["null", "true", "false"]:
					if field_comparison in ["=", "is"]:
						field_comparison = "is"
					else:
						field_comparison = "is not"
					field_value = sfv
				else:
					if isinstance(field_value, float):
						value = str(field_value)
					else:
						value = None
					fx = str(field_value)
					paren = fx.find("(")
					if paren != -1:
						fx = fx[:paren]
					if value != sfv and not bisectSearchRC(
						mysql_functions, fx.upper(), return_type=bool
					):
						field_value = "'%s'" % field_value
				where_clause = " ".join((field_name, field_comparison, field_value))

			wheres.append(where_clause)

		if len(wheres) != 0:
			return (" %s " % joiner).join(wheres)
		return ""

	def MakeKeyedObject(self, data, key):
		def getval(d, key):
			if type(d) is dict:
				return d[key]
			return getattr(d, key)

		if not data:
			return
		return dict([(getval(d, key), d) for d in data])

	def _mapesc(self, val):
		if val == "now()":
			return val
		elif type(val) is int or type(val) is float:
			return str(val)
		else:
			val = val.replace("?", "&#63")
			return f"'{self.escape_string(val)}'"

	def GetDBSize(self):
		"""returns kb"""
		return float(
			self.get_var(
				'SELECT ROUND(SUM((DATA_LENGTH + INDEX_LENGTH))/1048576,2) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = "%s";'
				% self.creds["db"],
				True,
			)
		)
