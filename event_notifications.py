import requests
import json
import datetime
import math
import asyncio
import os
from json import JSONDecodeError

cwd = os.getcwd()
config_json = json.loads("{}")

config_path = str(cwd) + "/config.json"
print("config at " + config_path)

def is_json_key_present(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False

    return True


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


try:
    with open(config_path, 'r') as config_file:
        config_json = json.loads(config_file.read())
except IOError:
    open(config_path, "a+")
    print("No config found. Check github for example config and populate your config.json file")
    exit(0)
except JSONDecodeError:
    print("invalid config. Check github for example config and populate your config.json file")
    exit(0)

api_key = config_json['api_key']

async def do_loop():
    calendars = config_json['calendars']

    if len(calendars) == 0:
        print("No calendars found in the config. Check github for example config and populate your config.json file")
        exit(0)

    while True:
        for calendar in calendars:
            cal_id = calendar['calendar_id']
            notification_times = calendar['notifications']
            timezones = calendar['timezones']
            discord_info = calendar['discord_info']

            try:
                result = requests.request('GET', 'https://www.googleapis.com/calendar/v3/calendars/' + str(cal_id) + '/events?key=' + str(api_key))
                json_response = json.loads(result.content)

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

                    print(str(name) + " in " + str(minutes_diff) + " minutes")

                    if minutes_diff in notification_times:
                        start_time_value = ""

                        for timezone in timezones:
                            to_add = datetime.timedelta(hours=timezone['utc_offset'])
                            this_zone_time = start + to_add

                            start_time_value += str(timezone['name']) + " - " + this_zone_time.strftime("%a %d %B %Y, %H:%M") + "\n"

                        how_long_message = str(get_time_until_string(minutes_diff))

                        webhook_body = {
                            "embeds": [
                                {
                                    "title": name + " in " + how_long_message,
                                    "url": link,
                                    "color": int(discord_info['color'][1:], 16),
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

                        if is_json_key_present(discord_info, 'bot_name'):
                            webhook_body['username'] = discord_info['bot_name']

                        if is_json_key_present(discord_info, 'bot_icon'):
                            webhook_body['avatar_url'] = discord_info['bot_icon']

                        send = requests.request('POST', discord_info['webhook_url'], json=webhook_body)
                        print(str(send.status_code) + " " + str(send.content))
            except Exception as e:
                print(str(e))

        await asyncio.sleep(60)


asyncio.get_event_loop().run_until_complete(do_loop())
