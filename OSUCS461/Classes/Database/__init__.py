from OSUCS461.Config import MySQL as DatabaseConfig
from OSUCS461.ThirdParty.MySQL import MySQL

DB = MySQL(**DatabaseConfig)
