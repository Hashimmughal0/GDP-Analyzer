def clean_data(raw_data: list) -> list:
    def is_valid(row):
        return (
            row["Value"] not in ("", None) and
            row["Year"].isdigit()
        )

    cleaned = filter(is_valid, raw_data)

    return list(map(lambda row: {
        "Country": row["Country Name"],
        "Region": row["Region"],
        "Year": int(row["Year"]),
        "Value": float(row["Value"])
    }, cleaned))