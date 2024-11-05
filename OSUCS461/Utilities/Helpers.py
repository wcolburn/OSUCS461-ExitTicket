import asyncio
import inspect
import io
import csv
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta, tzinfo, time, timezone
from decimal import Decimal
from functools import wraps, partial
from json import JSONEncoder, dumps, loads
from http import HTTPStatus
import time
from fastapi import HTTPException
import re
import random
import string

from pydantic import ValidationError

def _encodeutf8(item):
	return item.encode('utf-8')


def _decodeutf8(item):
	return item.decode('utf-8')


def get_status_response(status_code, response_msg, raw=False):
	if raw is True:
		return
	try:
		status_code_description = HTTPStatus(status_code).phrase
	except KeyError:
		status_code_description = "Unknown"

	return (
		f'{status_code} {status_code_description}',
		[('Content-Type', 'text/plain')],
		_encodeutf8(f'{response_msg}')
	)

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False

    return True

def _badRequestHandler(
	args=None,
	function=None,
	exception=None,
	response_msg=None,
	status=None,
	req_args=None
):
	"""Handles bad requests and returns a 400 Bad Request response

	Parameters:
		args (dict): The request arguments
		function (function): The function to inspect
		exception (Exception): The exception to handle
		response_msg (str): The response message
		status (int): The response status code
		req_args (list): The required arguments

	Returns:
		(tuple): A tuple containing the response status, headers, and body
	"""
	# if exception is a ValidationError
	if isinstance(exception, ValidationError):
		return get_status_response(400, exception.json())
	# chekc for Mysql OperationalError
	elif exception and isinstance(exception, tuple):
		response_msg = ('Exception Raised: {}').format(''.join(exception))
		return get_status_response(500, exception.args[0])
	elif exception and not args:
		response_msg = ('Exception Raised: {}').format(''.join(exception.args[0]))
		return get_status_response(400, response_msg)
	elif response_msg and status:
		return get_status_response(status, response_msg)
	elif args and function:
		sig = inspect.signature(function)
		sig_values = sig.parameters.values()
		required_args = [
			param.name for param in sig_values if param.default == inspect._empty
		]

		missing_params = []
		for param in required_args:
			if param not in args:
				missing_params.append(param)
		if missing_params:
			return get_status_response(
				400, f'Missing required param(s): {", ".join(missing_params)}'
			)
		elif exception:
			return _badRequestHandler(exception=exception)
		else:
			return get_status_response(400, 'Exception Raised')
	elif args and req_args:
		missing_params = []
		for param in req_args:
			if param not in args:
				missing_params.append(param)
		if missing_params:
			return get_status_response(
				400, f'Missing required param(s): {", ".join(missing_params)}'
			)
		elif exception:
			return _badRequestHandler(exception=exception)
	else:
		return get_status_response(400, 'Exception Raised')


def interval(start, end):
	"""start and end are datetime instances"""
	diff = end - start
	ret = diff.days * 24 * 60 * 60 * 1000000
	ret += diff.seconds * 1000000
	ret += diff.microseconds
	return ret


def convert(d):
	diff = d - datetime(1970,1,1,0,0, tzinfo=None)
	ret = diff.days * 24 * 60 * 60
	ret += diff.seconds
	return ret


def converttime(t):
	ret = t.hour * 60 * 60 * 1000000
	ret += t.minute * 60 * 1000000
	ret += t.second * 1000000
	ret += t.microsecond
	return ret


class GMT0(tzinfo):
	def utcoffset(self, dt): return timedelta(hours=0) + self.dst(dt);
	def tzname(self,dt): return "GMT +0";
	def dst(self, dt): return timedelta(0);

gmt0 = GMT0()
epoch = datetime(1970,1,1,0,0, tzinfo=gmt0)


def makedatetime(d): return epoch+timedelta(microseconds=d);


def epochMidnight():
	#this ONLY works for today at present
	midnight = datetime.combine(datetime.today(), time.min)
	epochMidnight = int((midnight - datetime(1970,1,1)).total_seconds())+28800
	print('Utilities.today.epochMidnight:', epochMidnight)
	return epochMidnight


CORSHeaders = [
	('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS'),
# 	('Access-Control-Allow-Origin', 'jason.bendhelps.com'),
	('Access-Control-Allow-Credentials','true'),
	('Access-Control-Allow-Headers', 'access-control-allow-origin,Authorization,Content-Type,Accept,Origin,User-Agent,DNT,Cache-Control,X-Mx-ReqToken,Keep-Alive,X-Requested-With,If-Modified-Since,X-Request')
]


CardinalLookup = [ "th","st","nd","rd","th","th","th","th","th","th" ]


def intToCardinal(n):
	if n % 100 >= 11 and n % 100 <= 13:
		return str(n)+"th"
	return str(n)+CardinalLookup[n % 10]


class DecimalEncoder(JSONEncoder):
	def default(self, o):
		if isinstance(o, Decimal):
			# wanted a simple yield str(o) in the next line,
			# but that would mean a yield on the line with super(...),
			# which wouldn't work (see my comment below), so...
			return float(o)
		return super(DecimalEncoder, self).default(o)

'''https://en.wikipedia.org/wiki/List_of_HTTP_status_codes'''
ErrorCodes = {
	'400': '400 Bad Request',
	'401': '401 Unauthorized',
	'402': '402 Payment Required',
	'403': '403 Forbidden',
	'404': '404 Not Found',
	'405': '405 Method Not Allowed',
	'406': '406 Not Acceptable',
	'409': '409 Conflict',
	'415': '415 Unsupported Media Type',
	'418': '418 I\'m a teapot',
	'500': '500 Internal Server Error',
	'501': '501 Not Implemented',
	'504': '504 Gateway Timeout',
	'507': '507 Insufficient Storage'
}

def formatErrorData(code, raw, verbose_message=None):
	strCode = str(code)
	retMsg = ErrorCodes[strCode] if strCode in ErrorCodes else ErrorCodes['418']
	raise HTTPException(
		status_code=code,
		detail=verbose_message if verbose_message else retMsg
	)

def wrap(func):
	@wraps(func)
	async def run(*args, loop=None, executor=None, **kwargs):
		if loop is None:
			loop = asyncio.get_event_loop()
		pfunc = partial(func, *args, **kwargs)
		return await loop.run_in_executor(executor, pfunc)
	return run

def convert_time_created(time_created):
	# Define the Pacific Time timezone (UTC-7 hours for Pacific Daylight Time)
	pacific_tz = timezone(timedelta(hours=-7), name="Pacific Daylight Time")

	# Convert epoch to datetime object in UTC
	utc_time = datetime.fromtimestamp(time_created, tz=timezone.utc)

	# Convert UTC time to Pacific Time
	pacific_time = utc_time.astimezone(pacific_tz)

	# Format the datetime object to the desired string format
	formatted_time = pacific_time.strftime('%a %b %d %Y %H:%M:%S %Z%z')
	return f"{formatted_time}"



def random_9char():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=9))
