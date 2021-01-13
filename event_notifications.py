import requests
import json
import datetime
import math
import asyncio
import os

cwd = os.getcwd()
config_file = open(str(cwd) + "\config.json", 'r')
config_json = json.loads("{}")

try:
    config_json = json.loads(config_file.read())
except:
    print("No config found. Check github for example config and populate your config.json file")
    exit(0)

##CURRENTLY TRANSFERRING ALL WEBHOOK AND CALENDAR INFO INTO A CONFIG FILE

calendar_id = ""
webhook_url = ""
api_key = config_json['api_key']

minutes_before_notify = [1440, 4320]

timezones = [
    {
        "name": "US",
        "utc_offset": -5
    },
    {
        "name": "UK",
        "utc_offset": 0
    },
    {
        "name": "NL",
        "utc_offset": 1
    }
]


def get_time_until_string(minutes_until):
    weeks = math.floor(minutes_until / 10080)
    days = math.floor(minutes_until / 1440)
    hours = math.floor(minutes_until / 60)
    minutes_until = math.floor(minutes_until)

    if weeks > 0:
        return str(weeks) + " week(s)"
    elif days > 0:
        return str(days) + " day(s)"
    elif hours > 0:
        return str(hours) + " hour(s)"
    else:
        return str(minutes_until) + " minute(s)"


async def do_loop():
    while True:
        try:
            result = requests.request('GET', 'https://www.googleapis.com/calendar/v3/calendars/' + str(
                calendar_id) + '/events?key=' + str(api_key))
            json_response = json.loads(result.content)

            testing = False

            events = json_response['items']

            for event in events:
                name = event['summary']
                link = event['htmlLink']

                start_raw = event['start']['dateTime']
                end_raw = event['end']['dateTime']

                if start_raw.endswith("Z"):
                    start_raw = start_raw.replace("Z", "+00:00")

                if end_raw.endswith("Z"):
                    end_raw = end_raw.replace("Z", "+00:00")

                start = datetime.datetime.fromisoformat(start_raw)
                end = datetime.datetime.fromisoformat(end_raw)
                now = datetime.datetime.now(tz=start.tzinfo)

                duration = end - start
                duration_text = str(duration)

                if start < now:
                    continue

                date_different = start - now
                minutes_diff = math.floor((date_different.total_seconds() / 60))

                print("check at " + now.strftime("%a %d %B %Y, %H:%M") + " - minutes diff is " + str(minutes_diff))

                if minutes_diff in minutes_before_notify or testing:
                    start_time_value = ""

                    for timezone in timezones:
                        to_add = datetime.timedelta(hours=timezone['utc_offset'])
                        this_zone_time = start + to_add

                        start_time_value += str(timezone['name']) + " - " + this_zone_time.strftime(
                            "%a %d %B %Y, %H:%M") + "\n"

                    how_long_message = str(get_time_until_string(minutes_diff))

                    webhook_body = {
                        "embeds": [
                            {
                                "title": name + " in " + how_long_message,
                                "url": link,
                                "color": 0xffff00,
                                "timestamp": start.isoformat(),
                                "fields": [
                                    {
                                        "name": "Start Time(s)",
                                        "value": start_time_value,
                                        "inline": False
                                    },
                                    {
                                        "name": "Duration",
                                        "value": duration_text,
                                        "inline": "False"
                                    }
                                ]
                            }
                        ]
                    }

                    send = requests.request('POST', webhook_url, json=webhook_body)
                    print(str(send.status_code) + " " + str(send.content))
        except Exception as e:
            print(str(e))

        await asyncio.sleep(60)


asyncio.get_event_loop().run_until_complete(do_loop())
