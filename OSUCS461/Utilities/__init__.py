import bisect, cgi, os, time, hashlib, random, datetime, re
from urllib.parse import parse_qs
from geventhttpclient import HTTPClient, URL
from json import loads, JSONEncoder
from codecs import getencoder
from decimal import Decimal
from .Helpers import convert, _encodeutf8, get_status_response

import html.entities as entity
from html import unescape

getModifiedTime = os.path.getmtime
getFileExists = os.path.exists

MimeTypes = {
	'jpe' : 'image/jpeg',
	'jpeg' : 'image/jpeg',
	'jpg' : 'image/jpeg',
	'png' : 'image/png',
}

emailpattern = re.compile('^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$', re.IGNORECASE)
def verifyEmail(s):
	return emailpattern.search(s) is not None


def isList(data): return (type(data) is list);
def isTuple(data): return (type(data) is tuple);
def isDict(data): return (type(data) is dict);
def isString(data): return (type(data) is bytes);
def isUnicode(data): return (type(data) is str);
def isInt(data): return (type(data) is int);
def isFloat(data): return (type(data) is float);
def isLong(data): return (type(data) is int);
def isNumber(data):
	return (
		type(data) in [
			int,
			float,
			int
		]
	)


enc = getencoder('us-ascii')


def deUnicodeText(_text, _encoding='utf-8'):
	try:
		if not isUnicode(_text) and isString(_text):
			_text = str(_text, _encoding)
			return enc(_text, 'xmlcharrefreplace')[0]
		elif isUnicode(_text):
			return enc(_text, 'xmlcharrefreplace')[0]
		return _text

	except Exception as inst:
		print('deUnicodeText', inst)


def decodeToEntity(s):
	t = ""
	for i in s:
		if ord(i) in entity.codepoint2name:
			name = entity.codepoint2name.get(ord(i))
			t += "&" + name + ";"
		else:
			t += i
	return t.replace('\'', '\\\'')


encodeFromEntityPattern = re.compile("&(\w+?);")
def descapeEntity(m, defs=entity.entitydefs):
	# callback: translate one entity to its ISO Latin value
	try:
		return defs[m.group(1)]
	except KeyError:
		return m.group(0) # use as is


def encodeFromEntity(string):
	return unescape(string)


def gracefulLoads(data):
	if type(data) in (bytes, str) and data[:1] in ('{', '['):
		return loads(data)
	return data


def parseAndDelistArguments(args):
	if type(args) in [bytes, str] and args[:1] in ['{', '[']:
		args = loads(args)
		if type(args) in [list, list]: return args;
	else:
		args = parse_qs(args)

	return delistArguments(args)


def delistArguments(args):
	'''
		Takes a dictionary, 'args' and de-lists any single-item lists then
		returns the resulting dictionary.
		{'foo': ['bar']} would become {'foo': 'bar'}
	'''

	def flatten(k,v):
		if len(v) == 1 and type(v) is list: return (str(k), v[0]);
		return (str(k), v)

	return dict([flatten(k,v) for k,v in list(args.items())])


def parseQuerystring(s):
	return delistArguments(parse_qs(s))


def processFormArgs(env, args):
	verb = env['REQUEST_METHOD']
	wsgi_input = env['wsgi.input']

	if wsgi_input.content_length and verb in ['PUT', 'POST']:
# 		print 'updating post_env'
		post_env = env.copy()
		post_env['QUERY_STRING'] = ''

		if 'CONTENT_TYPE' not in env or env['CONTENT_TYPE'] != 'application/json':
			form = cgi.FieldStorage(
				fp=wsgi_input,
				environ=post_env,
				keep_blank_values=True
			)
# 			print 'form:', form, type(form)
# 			print 'form.keys:', form.keys()
			form_data = [(k, form[k].value) for k in list(form.keys())]
		else:
			readData = wsgi_input.read()
			print('readData:', readData)
			form_data = loads(readData)

		print('form_data: ', form_data)
		args.update(form_data)
		print(args)
	return args


def checkRequiredArgs(args, required_args):
	for arg in required_args:
		if arg not in args:
			return get_status_response(500, 'arg: '+arg+' required')


def getFile(filename, display_exceptions=True):
	try:
		if os.path.exists(filename):
			return open(filename, 'r').read()
	except Exception as inst:
		if display_exceptions:
			print('bigFileGet.error:', filename, inst)


def fixed(data, precision=5):
	return round(Decimal(data), precision)


def scale(value, precision=100):
	return int(Decimal(value) * Decimal(precision))


# convert scale(fixed()) values back to originl string decimal values
def unscale(value):
	return str(round(Decimal(int(value)) / Decimal(10000), 5))


def bigFileGet(filename, display_exceptions=True):
	try:
		if os.path.exists(filename) is True:
			fread = open(filename, 'r')
			data = fread.read()
			return data.strip().split('\n')

	except Exception as inst:
		if display_exceptions is True:
			print('bigFileGet(%s)' % filename, inst)


def timestampMilliseconds(timestamp=None):
	if not timestamp: timestamp = time.time()*1000;
	return int(timestamp)

def now():
	return timestampMilliseconds()

def timestampSeconds(timestamp=None):
	if not timestamp: timestamp = time.time();
	return int(timestamp)

def nowSeconds():
	return timestampSeconds()

def timestamp(timestamp=None):
	return timestampSeconds(timestamp)


def sanitize_filename(filename):
	if '..' in filename or filename.startswith(('/', '\\')) or filename.startswith(('C:', 'D:', 'E:', 'F:', 'G:', 'H:', 'I:', 'J:', 'K:', 'L:', 'M:', 'N:', 'O:', 'P:', 'Q:', 'R:', 'S:', 'T:', 'U:', 'V:', 'W:', 'X:', 'Y:', 'Z:')):
		return False

	return filename


def putFile(filename, content, mode='w', make_if_missing=False):
	try:
		sanitized_filename = sanitize_filename(filename=filename)
		if not sanitized_filename:
			print('putFile.ERROR: Filename was corrupt. File was not created.', filename)
			return False
		if make_if_missing:
			a_dir = sanitized_filename.split('/')
			a_dir.pop()
			dir = '/'.join(a_dir)
			if not os.path.exists(dir): os.makedirs(dir);
	except Exception as inst:
		pass

	try:
		fout = open(sanitized_filename, mode)
		fout.write(content)
		fout.close()

	except Exception as inst:
		print('putFile.ERROR:',  sanitized_filename, inst)


def putForRebuild(filename, content, make_if_missing=False):
	try:
		if make_if_missing:
			a_dir = filename.split('/')
			a_dir.pop()
			dir = '/'.join(a_dir)
			if not os.path.exists(dir):
				os.makedirs(dir)
	except Exception as inst:
		pass

	try:
		fout = open(filename, 'a')
		fout.write(content+'\n')
		fout.close()
	except Exception as inst:
		print('putForRebuild.ERROR:',  filename, inst)


def getREST(url):
	_url = URL(url)
	http = HTTPClient.from_url(_url, connection_timeout=1000, network_timeout=1000)
# 	print 'getREST._url:', _url.request_uri
	response = http.get(_url.request_uri)
	content = response.read()
	http.close()
# 	print 'getREST.response:', response
	return loads(content)


def createHash(input_string):
	input = _encodeutf8(
		''.join([
			str(x) for x in [
				os.getpid(),
				random.Random().randint(0,100000000),
				datetime.datetime.now(),
				input_string
			]
		])
	)
	return hashlib.md5(input).hexdigest()


def escapeSingleQuotes(keys, data):
	ret = {}
	for key in keys:
		try:
# 			ret[key] = data[key].replace('\'', '\\\'')
			ret[key] = decodeToEntity(data[key])
		except:
			if key in data:
				ret[key] = data[key]
	return ret


def SHA224Hash(input_string):
	input = _encodeutf8(
		''.join([
			str(x) for x in [
				os.getpid(),
				random.Random().randint(0,100000000),
				datetime.datetime.now(),
				input_string
			]
		])
	)
	return hashlib.sha224(input).hexdigest()


# TODO: remove this after dataclass refactor is complete
# temporarily added back in for compatibility with un-databased classes
def SHA224Digest(input):
	if isList(input) or isTuple(input):
		input = ''.join(map(str, input))

	if not isString(input):
		input = _encodeutf8(str(input))
	return hashlib.sha224(input).hexdigest()


def keyInDict(data, key):
	return key in data and data[key]


def keynat(string):
	r'''A natural sort helper function for sort() and sorted()
	without using regular expression.

	>>> items = ('Z', 'a', '10', '1', '9')
	>>> sorted(items)
	['1', '10', '9', 'Z', 'a']
	>>> sorted(items, key=keynat)
	['1', '9', '10', 'Z', 'a']
	'''
	r = []
	for c in string:
		try:
			c = int(c)
			try:
				r[-1] = r[-1] * 10 + c
			except:
				r.append(c)
		except:
			r.append(c)
	return r


class JSONDateTimeEncoder(JSONEncoder):
	def default(self, obj):
		if isinstance(obj, time.struct_time):
			return convert(datetime.datetime(*obj[:6]))
		if isinstance(obj, (datetime.date, datetime.datetime)):
			return obj.isoformat();
		return JSONEncoder.default(self, obj)


def bisectSearchRC(haystack, item, index_pos=None, return_type=None):

	if not return_type: return_type = int;

	def returnValue(value):
		if return_type is bool and value == -1:
			return False
		elif return_type is bool:
			return True
		elif value != -1:
			return value

	try:
		item_index = bisect.bisect_left(haystack, item)
		if item_index < len(haystack):
			if index_pos is not None and item[index_pos] == haystack[item_index][index_pos]:
				return returnValue(item_index)
			elif index_pos is None and item == haystack[item_index]:
				return returnValue(item_index)

	except Exception as inst:
		print('bisectSearchRC.ERROR', inst)

	return returnValue(-1)


def parseBooleanArg(arg):
	if arg is None: return False;
	if type(arg) is bool: return arg;
	if arg.lower() == 'true': return True;
	return False


def print_timing(func):
	def wrapper(*arg):
		t1 = time.time()
		res = func(*arg)
		t2 = time.time()
		print('%s took %0.3fms' % (func.__name__, (t2-t1)*1000.0))
		return res
	return wrapper


def getDirectoryFiles(path, extension=None):
	files = os.listdir(path)

	if extension is not None:
		return [
			file for file in files
			if file.endswith(extension)
		]

	return files

def GetContentFiles(path, suffix=None):
	ret = []
	for f in os.listdir(path):
		if(suffix != None):
			if f.endswith(suffix):
				ret.append(f)
		else:
			ret.append(f)
	return ret

class UtilityClass:

	@classmethod
	def createLocationUUID(cls, *args):
		return cls.createUUID(''.join([
			str(scale(fixed(item), 10000))
			for item in (args)
		]))

	@staticmethod
	def createUUID(input):
		if isList(input) or isTuple(input):
			input = ''.join(map(str, input))

		if not isString(input):
			input = _encodeutf8(str(input))
		return hashlib.sha224(input).hexdigest()

	@staticmethod
	def createExperienceImageUUID(expereince_uuid, image_uuid):
		return expereince_uuid + image_uuid

	@staticmethod
	def prepareForDB(obj):
		return {
			key: value
			for key, value in obj.__dict__.items()
			if value is not None
		}

	#TODO: check if d2(existing obj) has null values or None values. If NUlls, check if a None to null compare is passing or not. if so, might be a good reason to remove None values in BaseActions.get_fields()
	#TODO: possibly, rename d1 to required_fields and d2 to existing_obj
	@staticmethod
	def check_value_match(d1, d2):
		for key, value in d1.items():
			if key in d2 and d2[key] != value:
				return False
			elif key not in d2:
				# maybe change to raise exception?
				return False
		return True

		# Alt Method, optimization of new version
		return all(key in d2 and d2[key] == value for key, value in d1.items())

		# old version, checking if new version is better
		for key, value in d1.items():
			if key in d2 and d2[key] == value:
				return True
		return False

	@staticmethod
	def clean_model_args(self):
		for key, value in self.__dict__.items():
			if value is not None and value.strip() == '':
				setattr(self, key, None)

	@staticmethod
	def validate_args(self, args):
		missing_fields = [field for field in args if not getattr(self, field)]
		if missing_fields:
			raise Exception(f'Missing required field(s): {missing_fields}')
		else:
			return True
