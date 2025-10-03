from typing import List, Dict
from datetime import datetime


def parse_weather_log(filepath: str = "data/weather_log.txt") -> List[Dict]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except FileNotFoundError:
        return []

    if not content:
        return []

    blocks = content.split("\n\n")
    records = []

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or not lines[0].startswith("Дата и время"):
            continue

        datetime_raw = lines[0].replace("Дата и время ", "")
        if "__" in datetime_raw:
            date_part, time_part = datetime_raw.split("__", 1)
            # Преобразуем "17-19-47" → "17:19"
            time_str = time_part.replace("-", ":", 2)[:5]  # "17:19"
        else:
            date_part = datetime_raw
            time_str = "00:00"

        record = {
            "date_str": date_part,
            "time_str": time_str
        }

        for line in lines[1:]:
            if ": " in line:
                key, value = line.split(": ", 1)
                try:
                    record[key] = int(value)
                except ValueError:
                    continue

        required = ["Температура", "Ветер", "Давление", "Влажность"]
        if all(k in record for k in required):
            records.append(record)

    return records


def get_weather_by_day(date_str: str, filepath: str = "data/weather_log.txt") -> List[Dict]:
    all_records = parse_weather_log(filepath)
    return [r for r in all_records if r["date_str"] == date_str]


def get_latest_days(filepath: str = "data/weather_log.txt", days: int = 7) -> List[Dict]:
    all_records = parse_weather_log(filepath)
    if not all_records:
        return []

    unique_dates = sorted({r["date_str"] for r in all_records}, reverse=True)
    latest_dates = set(unique_dates[:days])

    latest_records = [r for r in all_records if r["date_str"] in latest_dates]

    latest_records.sort(key=lambda r: (r["date_str"], r["time_str"]))
    return latest_records[-20:]
