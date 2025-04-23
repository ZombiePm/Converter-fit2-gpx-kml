import os
from fitparse import FitFile
from datetime import datetime

def semicircles_to_degrees(semicircles):
    return semicircles * (180 / 2**31)

def process_fit_file(fit_path):
    fitfile = FitFile(fit_path)
    points = []
    first_timestamp = None

    for record in fitfile.get_messages("record"):
        data = {field.name: field.value for field in record}
        lat = data.get("position_lat")
        lon = data.get("position_long")
        alt = data.get("enhanced_altitude", 0)
        time = data.get("timestamp")
        heart_rate = data.get("heart_rate")
        speed = data.get("speed")

        if lat and lon and time:
            lat_deg = semicircles_to_degrees(lat)
            lon_deg = semicircles_to_degrees(lon)

            point = {
                "lat": lat_deg,
                "lon": lon_deg,
                "ele": alt,
                "time": time.isoformat() + "Z",  # GPX требует формат ISO8601
                "hr": heart_rate,
                "speed": speed,
            }
            points.append(point)

            if not first_timestamp:
                first_timestamp = time

    if not points:
        print(f"⚠️  Нет координат в файле: {fit_path}")
        return

    filename_base = os.path.splitext(os.path.basename(fit_path))[0]
    date_str = first_timestamp.strftime("%Y-%m-%d_%H%M") if first_timestamp else "unknown"
    output_filename = f"{filename_base}_{date_str}.gpx"

    # Генерация GPX
    gpx_header = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="fitparse-gpx" xmlns="http://www.topografix.com/GPX/1/1"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:schemaLocation="http://www.topografix.com/GPX/1/1
                     http://www.topografix.com/GPX/1/1/gpx.xsd"
 xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
  <trk>
    <name>{name}</name>
    <trkseg>""".format(name=filename_base)

    gpx_footer = """
    </trkseg>
  </trk>
</gpx>"""

    gpx_points = ""
    for pt in points:
        gpx_points += f"""
      <trkpt lat="{pt['lat']}" lon="{pt['lon']}">
        <ele>{pt['ele']}</ele>
        <time>{pt['time']}</time>
        <extensions>
          <gpxtpx:TrackPointExtension>"""
        if pt["hr"] is not None:
            gpx_points += f"""
            <gpxtpx:hr>{pt['hr']}</gpxtpx:hr>"""
        if pt["speed"] is not None:
            gpx_points += f"""
            <gpxtpx:speed>{pt['speed']}</gpxtpx:speed>"""
        gpx_points += """
          </gpxtpx:TrackPointExtension>
        </extensions>
      </trkpt>"""

    # Запись в файл
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(gpx_header + gpx_points + gpx_footer)

    print(f"✅ GPX сохранён: {output_filename}")

# Обработка всех .fit файлов в текущей директории
for file in os.listdir("."):
    if file.lower().endswith(".fit"):
        process_fit_file(file)
