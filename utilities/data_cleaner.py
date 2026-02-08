def clean_data(raw_data: list) -> list:
    cleaned = []

    for row in raw_data:
        country = row.get("Country Name") or row.get("Country") or ""
        region = row.get("Region") or row.get("Continent") or ""

        
        for key, val in row.items():
            if not key:
                continue
            key_str = key.strip()
            if key_str.isdigit():
                if val in ("", None):
                    continue
                try:
                    year = int(key_str)
                    value = float(val)
                except Exception:
                    continue

                cleaned.append({
                    "Country": country,
                    "Region": region,
                    "Year": year,
                    "Value": value
                })

    return cleaned