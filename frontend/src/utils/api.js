const API_BASE = import.meta.env.VITE_API_URL !== undefined ? import.meta.env.VITE_API_URL : "http://localhost:8000";

export async function fetchProperties(params = {}) {
    const query = new URLSearchParams();
    if (params.county) query.set("county", params.county);
    if (params.city) query.set("city", params.city);
    if (params.sort_by) query.set("sort_by", params.sort_by);
    if (params.min_bid != null) query.set("min_bid", params.min_bid);
    if (params.max_bid != null) query.set("max_bid", params.max_bid);

    const res = await fetch(`${API_BASE}/api/properties?${query.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch properties");
    return res.json();
}

export async function fetchProperty(id) {
    const res = await fetch(`${API_BASE}/api/properties/${id}`);
    if (!res.ok) throw new Error("Property not found");
    return res.json();
}

export async function triggerScrape() {
    const res = await fetch(`${API_BASE}/api/trigger-scrape`, { method: "POST" });
    return res.json();
}

export async function fetchScrapeStatus() {
    const res = await fetch(`${API_BASE}/api/scrape-status`);
    return res.json();
}

export async function fetchStats() {
    const res = await fetch(`${API_BASE}/api/stats`);
    return res.json();
}

export function exportCsv(properties) {
    const headers = [
        "address", "city", "county", "auction_date", "auction_time",
        "starting_bid", "estimated_value", "status", "source", "tsn", "zillow_url"
    ];
    const rows = properties.map(p =>
        headers.map(h => {
            const v = p[h] ?? "";
            return `"${String(v).replace(/"/g, '""')}"`;
        }).join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `spokane-auctions-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}
