from flask import *
import requests
import datetime
from datetime import datetime, timezone, timedelta
from dotenv import dotenv_values

config = dotenv_values(".env")
TOKEN = config["TOKEN"]
LTA_KEY =  config["LTA_KEY"]
TELEGRAM_URL = "https://api.telegram.org/bot" 

app = Flask(__name__)

def get_time_difference(current, arrival):
    if arrival != "":
        arrival_time = datetime.fromisoformat(arrival)
        time_diff = int((arrival_time - current).total_seconds() / 60)
        time_diff = time_diff if time_diff > 0 else 'Bus has just arrived / left'
        return time_diff 
    else:
        return "Bus is not in service"

def get_bus_data(bus_stop_code):
    url = f"http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2?BusStopCode={bus_stop_code}"
    payload={}
    headers = {
    'AccountKey': LTA_KEY
    }
    response = requests.request("GET", url, headers=headers, data=payload).json()
    bus_arrival = ""
    timezone_offset = 8.0  
    tzinfo = timezone(timedelta(hours=timezone_offset))
    currentTime = datetime.now(tzinfo)
    for data in response["Services"]:
        bus_code = data["ServiceNo"]
        next_bus_first = data["NextBus"]["EstimatedArrival"]
        next_bus_second =  data["NextBus2"]["EstimatedArrival"]
        timeDiffFirst = get_time_difference(currentTime, next_bus_first)
        timeDiffSecond = get_time_difference(currentTime, next_bus_second)
        notif = f"{bus_code}: {timeDiffFirst}, {timeDiffSecond}" + '\n'
        bus_arrival += notif 
    return bus_arrival

def parse_message(message):
    chat_id = message["message"]["chat"]["id"]
    bus_stop_code = message["message"]["text"]
    return chat_id, bus_stop_code

def send_message(chat_id, text):
    url = TELEGRAM_URL + TOKEN + '/sendMessage'
    payload = {"chat_id": chat_id, "text": text}
    r = requests.post(url, json=payload)
    return r

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        msg = request.get_json()
        chat_id, bus_stop_code = parse_message(msg)
        if len(bus_stop_code) == 0:
            send_message(chat_id, "Please enter a valid bus stop code")
            return Response('Ok', status=200)
        else:
            bus_data = get_bus_data(bus_stop_code)
            send_message(chat_id, bus_data)
            return Response('Ok', status=200)
    else:
        return '<h1>SG Bus Bot</h1>'

def main():
    print(get_bus_data())

if __name__ == '__main__':
    app.run(debug=True)
