from Config import MySQL as DatabaseConfig
from ThirdParty.MySQL import MySQL

DB = MySQL(**DatabaseConfig)
