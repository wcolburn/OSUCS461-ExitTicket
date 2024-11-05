from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from time import time
import traceback
import uvicorn

from OSUCS461.Utilities.CustomLogger import custom_logger
from OSUCS461.Config import FASTAPI_CONFIG
from OSUCS461.Routers import router

logger = custom_logger('fastAPI', 'fastapi_logs.log')

app = FastAPI()

class LoggingMiddleware(BaseHTTPMiddleware):
	def __init__(self, app):
		super().__init__(app)
	async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
		logger.info(f"Incoming request: {request.method} {request.url}.")# Headers: {request.headers}")

		route_name = "unknown"
		for route in request.app.routes:
			match, _ = route.matches(request.scope)
			if match.name == "FULL":
				route_name = route.endpoint.__name__
				break
		logger.info(f"Handling function: {route_name}")
		start_time = time()
		try:
			response = await call_next(request)
		except Exception as e:
			logger.error(f"Error processing request. Request was handled by: {route_name} \nMethod: {request.method} - URL: {request.url} - Headers: {request.headers} \nStack Trace: {e}\n{traceback.format_exc()}")
		process_time = time() - start_time
		logger.info(f"Completed request in {process_time:.4f} seconds")
		logger.info(f"Response status code: {response.status_code}")
		return response

app.add_middleware(LoggingMiddleware)


def use_route_names_as_operation_ids(app: FastAPI) -> None:
	"""
	Simplify operation IDs so that generated API clients have simpler function
	names.

	Should be called only after all routes have been added.
	"""
	for route in app.routes:
		if isinstance(route, APIRoute):
			route.operation_id = route.name  # in this case, 'read_items'


app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


app.include_router(router)
use_route_names_as_operation_ids(app)

if __name__ == "__main__":
	uvicorn.run("main:app", **FASTAPI_CONFIG.__dict__)
