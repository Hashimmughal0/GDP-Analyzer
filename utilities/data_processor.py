def filter_data(data: list, region: str, year: int) -> list:
    region_norm = (region or "").strip().lower()

    def match_region(r_region: str) -> bool:
        if not r_region:
            return False
        r = r_region.strip().lower()
        if region_norm == r:
            return True
        if region_norm and region_norm in r:
            return True
        if r and r in region_norm:
            return True
        return False

    filtered = [r for r in data if r.get("Year") == year and match_region(r.get("Region", ""))]

   
    if not filtered:
        filtered = [r for r in data if r.get("Year") == year]

    return filtered


def compute_statistic(data: list, operation: str) -> float:
    values = list(map(lambda r: r["Value"], data))

    if not values:
        raise ValueError("No data available after filtering")

    if operation == "average":
        return sum(values) / len(values)

    if operation == "sum":
        return sum(values)

    raise ValueError("Unsupported operation")