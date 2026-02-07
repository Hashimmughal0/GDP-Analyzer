def filter_data(data: list, region: str, year: int) -> list:
    return list(filter(
        lambda r: r["Region"] == region and r["Year"] == year,
        data
    ))


def compute_statistic(data: list, operation: str) -> float:
    values = list(map(lambda r: r["Value"], data))

    if not values:
        raise ValueError("No data available after filtering")

    if operation == "average":
        return sum(values) / len(values)

    if operation == "sum":
        return sum(values)

    raise ValueError("Unsupported operation")