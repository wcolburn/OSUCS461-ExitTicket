# this file is a template config file, the real configs are in __init__.py
from dataclasses import dataclass

env = "local"
API_VERSION = 'v1'
SERVER = 'osucapstone.com'
FRONTEND = 'osucapstone.com'

@dataclass(repr=False)
class BaseConfig:
    reload: bool = True
    use_colors: bool = True
    port: int = 8855

@dataclass
class LocalConfig(BaseConfig):
    host: str = "127.0.0.1"

@dataclass
class StagingConfig(BaseConfig):
    host: str = "staging.osucapstone.com"

@dataclass
class ProdConfig(BaseConfig):
    host: str = "osucapstone.com"

configs = {
    "local" : LocalConfig(),
    "sandbox" : StagingConfig(),
    "prod" : ProdConfig()
}

FASTAPI_CONFIG = configs[env]

MySQL = {
	'local' : {
		'host' : '127.0.0.1',
		'port' : 3306,
		"user": "xxx",
        "passwd": "xxxx",
 		'db' : 'osucs461'
	},
	'sandbox' : {
		'host' : 'xxxx',
		'port' : 3306,
		"user": "xxx",
        "passwd": "xxxx",
 		'db' : 'osucs461'
	},
	'prod' : {
		'host' : 'xxxx',
		'port' : 3306,
		"user": "xxx",
        "passwd": "xxxx",
 		'db' : 'osucs461'
	}
}[env]
