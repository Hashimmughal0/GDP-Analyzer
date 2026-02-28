from typing import List, Any, Dict
from core.contracts import DataSink


class TransformationEngine:
    def __init__(self, sink: DataSink, config: Dict[str, Any] = None):
        self.sink   = sink
        self.config = config or {}

    def execute(self, raw_data: List[Any]) -> None:
        cleaned   = self._clean(raw_data)
        processed = self._process(cleaned)
        self.sink.write(processed)

    def _clean(self, raw_data: List[dict]) -> List[dict]:
        cleaned = []
        for row in raw_data:
            country = row.get("Country Name") or row.get("Country") or ""
            region  = row.get("Region") or row.get("Continent") or ""
            for key, val in row.items():
                if not key:
                    continue
                key_str = key.strip()
                if not key_str.isdigit():
                    continue
                if val in ("", None):
                    continue
                try:
                    cleaned.append({
                        "Country": country,
                        "Region":  region,
                        "Year":    int(key_str),
                        "Value":   float(val),
                    })
                except (ValueError, TypeError):
                    continue
        return cleaned

    def _process(self, data: List[dict]) -> List[Dict[str, Any]]:
        results      = []
        req_year     = self.config.get("year", 2020)
        req_region   = self.config.get("region", "Asia")
        start_year   = self.config.get("start_year", 2010)
        end_year     = self.config.get("end_year", 2020)
        decline_yrs  = self.config.get("decline_years", 5)

        def in_region(d):
            return req_region.lower() in d["Region"].lower() if req_region else True

        yr_reg = [d for d in data if d["Year"] == req_year and in_region(d)]
        if yr_reg:
            ranked = sorted(yr_reg, key=lambda x: x["Value"], reverse=True)
            results.append({"Label": f"Output 1: Top 10 GDP — {req_region} ({req_year})",    "Data": ranked[:10]})
            results.append({"Label": f"Output 2: Bottom 10 GDP — {req_region} ({req_year})", "Data": ranked[-10:][::-1]})

        country_growth: Dict[str, dict] = {}
        for d in data:
            if not in_region(d):
                continue
            c, y, v = d["Country"], d["Year"], d["Value"]
            if y == start_year:
                country_growth.setdefault(c, {})["start"] = v
            if y == end_year:
                country_growth.setdefault(c, {})["end"] = v
        growth_rates = []
        for c, vals in country_growth.items():
            if "start" in vals and "end" in vals and vals["start"] > 0:
                rate = ((vals["end"] - vals["start"]) / vals["start"]) * 100
                growth_rates.append({"Country": c, "Growth_Rate_%": round(rate, 2)})
        results.append({"Label": f"Output 3: GDP Growth Rate — {req_region} ({start_year}–{end_year})", "Data": growth_rates})

        range_data = [d for d in data if start_year <= d["Year"] <= end_year]
        reg_sums: Dict[str, float] = {}
        reg_counts: Dict[str, int] = {}
        for d in range_data:
            r = d["Region"]
            if r:
                reg_sums[r]   = reg_sums.get(r, 0)   + d["Value"]
                reg_counts[r] = reg_counts.get(r, 0) + 1
        avg_by_cont = [{"Region": r, "Average_GDP": reg_sums[r] / reg_counts[r]}
                       for r in reg_sums if reg_counts[r] > 0]
        results.append({"Label": f"Output 4: Average GDP by Continent ({start_year}–{end_year})", "Data": avg_by_cont})

        year_sums: Dict[int, float] = {}
        for d in range_data:
            year_sums[d["Year"]] = year_sums.get(d["Year"], 0) + d["Value"]
        global_trend = [{"Year": y, "Total_GDP": s} for y, s in sorted(year_sums.items())]
        results.append({"Label": f"Output 5: Global GDP Trend ({start_year}–{end_year})", "Data": global_trend})

        reg_start: Dict[str, float] = {}
        reg_end:   Dict[str, float] = {}
        for d in data:
            r = d["Region"]
            if not r:
                continue
            if d["Year"] == start_year:
                reg_start[r] = reg_start.get(r, 0) + d["Value"]
            if d["Year"] == end_year:
                reg_end[r]   = reg_end.get(r, 0)   + d["Value"]
        reg_growth = []
        for r in reg_start:
            if r in reg_end and reg_start[r] > 0:
                gr = ((reg_end[r] - reg_start[r]) / reg_start[r]) * 100
                reg_growth.append({"Region": r, "Growth_Rate_%": gr})
        if reg_growth:
            fastest = max(reg_growth, key=lambda x: x["Growth_Rate_%"])
            results.append({"Label": f"Output 6: Fastest Growing Continent ({start_year}–{end_year})", "Data": [fastest]})

        countries_hist: Dict[str, Dict[int, float]] = {}
        for d in data:
            if not in_region(d):
                continue
            if end_year - decline_yrs + 1 <= d["Year"] <= end_year:
                c = d["Country"]
                countries_hist.setdefault(c, {})[d["Year"]] = d["Value"]
        decline = []
        for c, hist in countries_hist.items():
            if len(hist) == decline_yrs:
                yrs = sorted(hist)
                if all(hist[yrs[i]] < hist[yrs[i - 1]] for i in range(1, len(yrs))):
                    decline.append({"Country": c})
        results.append({"Label": f"Output 7: Consistent GDP Decline — Last {decline_yrs} Years ({req_region})", "Data": decline})

        total_gdp = sum(reg_sums.values())
        contributions = []
        if total_gdp > 0:
            for r, s in reg_sums.items():
                contributions.append({"Region": r, "Contribution_%": round(s / total_gdp * 100, 2)})
        results.append({"Label": f"Output 8: Continent Contribution to Global GDP ({start_year}–{end_year})", "Data": contributions})

        results.append({
            "Label":  "Graph Data",
            "Type":   "Plot",
            "Data":   yr_reg,
            "Region": req_region,
            "Year":   req_year,
            "Top_N":  self.config.get("top_n", 10),
        })

        return results
