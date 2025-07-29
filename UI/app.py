import requests
from datetime import datetime
import time
from flask import Flask, render_template, request, jsonify
import psycopg2
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "pond_data",
    "user": "pond_user",
    "password": "secretpassword"
}

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/weather")
def weather():
    return render_template("weather.html")

@app.route("/diagnostics")
def diagnostics():
    return render_template("diagnostics.html")


@app.route("/api/dashboard")
def api_dashboard():
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT
              extract(epoch from timestamp) * 1000,
              level_cm,
              outflow_lps
            FROM pond_metrics
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """, (start, end))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        level = [[int(row[0]), row[1]] for row in rows]
        outflow = [[int(row[0]), row[2]] for row in rows]

        return jsonify({"level": level, "outflow": outflow})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



@app.route("/api/weather/meteogram")
def weather_meteogram():
    try:
        import requests
        from datetime import datetime
        import pytz

        url = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=49.6265900&lon=18.3016172&altitude=350"
        headers = {
            "User-Agent": "MyWeatherApp/1.0 (email@example.com)"
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        result = []
        for entry in data["properties"]["timeseries"]:
            time_iso = entry["time"]
            time_ts = int(datetime.fromisoformat(time_iso.replace("Z", "+00:00")).timestamp() * 1000)

            details = entry.get("data", {}).get("instant", {}).get("details", {})
            wind = details.get("wind_speed", 0)
            wind_direction = details.get("wind_from_direction", 0)
            temperature = details.get("air_temperature", 0)
            pressure = details.get("air_pressure_at_sea_level", 1013)

            rain = 0
            if "next_1_hours" in entry["data"]:
                rain = entry["data"]["next_1_hours"]["details"].get("precipitation_amount", 0)

            result.append({
                "time": time_ts,
                "temperature": temperature,
                "rain": rain,
                "wind": wind,
                "wind_direction": wind_direction,
                "pressure": pressure
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/weather/daily")
def daily_forecast():
    LAT = 49.6265900
    LON = 18.3016172
    ALT = 350
    URL = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={LAT}&lon={LON}&altitude={ALT}"

    headers = {"User-Agent": "pond-monitoring-app/1.0"}
    r = requests.get(URL, headers=headers)
    data = r.json()

    # Ukládání agregovaných údajů po dnech
    daily = defaultdict(lambda: {
        "temps": [], "wind_avg": [], "wind_gust": [], "rain": 0.0, "icons": []
    })

    for entry in data["properties"]["timeseries"]:
        dt = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        date = dt.date().isoformat()
        inst = entry["data"].get("instant", {}).get("details", {})
        temp = inst.get("air_temperature")
        wind = inst.get("wind_speed")
        gust = inst.get("wind_speed_of_gust")

        if temp is not None:
            daily[date]["temps"].append(temp)
        if wind is not None:
            daily[date]["wind_avg"].append(wind)
        if gust is not None:
            daily[date]["wind_gust"].append(gust)

        rain = entry["data"].get("next_1_hours", {}).get("details", {}).get("precipitation_amount", 0.0)
        daily[date]["rain"] += rain

        icon = entry["data"].get("next_1_hours", {}).get("summary", {}).get("symbol_code")
        if icon:
            daily[date]["icons"].append(icon)

    # Výpočet výsledné denní řady
    result = []
    for date, values in sorted(daily.items())[:7]:
        if not values["temps"]:
            continue
        result.append({
            "date": date,
            "temp": max(values["temps"]),
            "wind_avg": sum(values["wind_avg"]) / len(values["wind_avg"]) if values["wind_avg"] else 0,
            "wind_gust": max(values["wind_gust"]) if values["wind_gust"] else 0,
            "rain": round(values["rain"], 1),
            "icon": max(set(values["icons"]), key=values["icons"].count) if values["icons"] else "clearsky_day"
        })

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
