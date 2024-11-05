from datetime import datetime, timedelta, timezone

alpha_time = datetime(2023, 3, 1, 0, 0, 0, 0, tzinfo=timezone.utc) 		# the beginning of time
beta_time = datetime(2025, 1, 1, 0, 0, 0, 0)

def iso_to_epoch(iso_string):
	iso_string = str(iso_string)
	dt = datetime.fromisoformat(iso_string)
	seconds_since_epoch = int(dt.timestamp())
	return seconds_since_epoch if iso_string else None
