import os
from fitparse import FitFile
from datetime import datetime

def semicircles_to_degrees(semicircles):
    return semicircles * (180 / 2**31)

def process_fit_file(fit_path):
    fitfile = FitFile(fit_path)
    coordinates = []
    first_timestamp = None

    for record in fitfile.get_messages("record"):
        data = {field.name: field.value for field in record}
        lat = data.get("position_lat")
        lon = data.get("position_long")
        alt = data.get("enhanced_altitude", 0)

        if lat and lon:
            lat_deg = semicircles_to_degrees(lat)
            lon_deg = semicircles_to_degrees(lon)
            coordinates.append(f"{lon_deg},{lat_deg},{alt}")

            if not first_timestamp:
                first_timestamp = data.get("timestamp")

    if not coordinates:
        print(f"⚠️  Нет координат в файле: {fit_path}")
        return

    filename_base = os.path.splitext(os.path.basename(fit_path))[0]
    if first_timestamp:
        date_str = first_timestamp.strftime("%Y-%m-%d_%H%M")
        pretty_date = first_timestamp.strftime("%d.%m.%y %H:%M")
    else:
        date_str = "unknown"
        pretty_date = "Unknown time"

    output_filename = f"RK_kml_{filename_base}_{date_str}.kml"
    track_name = f"Walking {pretty_date}"

    kml_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.1" xmlns:trails="http://www.google.com/kml/trails/1.0">
  <Document>
    <name>{output_filename}</name>
    <Placemark>
      <name>{track_name}</name>
      <Style>
        <LineStyle>
          <color>ff0000ff</color>
          <width>4</width>
        </LineStyle>
      </Style>
      <MultiGeometry>
        <LineString>
          <tessellate>1</tessellate>
          <coordinates>
{chr(10).join(coordinates)}
          </coordinates>
        </LineString>
      </MultiGeometry>
    </Placemark>
  </Document>
</kml>
"""

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(kml_template)
    print(f"✅ Сохранён: {output_filename}")

# Обход всех .fit файлов в текущей директории
for file in os.listdir("."):
    if file.lower().endswith(".fit"):
        process_fit_file(file)
