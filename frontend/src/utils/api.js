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

// ── Notes ──────────────────────────────────────────────────────────────

export async function fetchNotes(propertyId) {
    const res = await fetch(`${API_BASE}/api/properties/${propertyId}/notes`);
    if (!res.ok) throw new Error("Failed to fetch notes");
    return res.json();
}

export async function addNote(propertyId, author, body) {
    const res = await fetch(`${API_BASE}/api/properties/${propertyId}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ author, body }),
    });
    if (!res.ok) throw new Error("Failed to add note");
    return res.json();
}

export async function deleteNote(propertyId, noteId) {
    const res = await fetch(`${API_BASE}/api/properties/${propertyId}/notes/${noteId}`, {
        method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete note");
}

// ── Photos ─────────────────────────────────────────────────────────────

export async function fetchPhotos(propertyId) {
    const res = await fetch(`${API_BASE}/api/properties/${propertyId}/photos`);
    if (!res.ok) throw new Error("Failed to fetch photos");
    return res.json();
}

export async function uploadPhoto(propertyId, file, caption = "", uploadedBy = "Team") {
    const form = new FormData();
    form.append("file", file);
    if (caption) form.append("caption", caption);
    form.append("uploaded_by", uploadedBy);
    const res = await fetch(`${API_BASE}/api/properties/${propertyId}/photos`, {
        method: "POST",
        body: form,
    });
    if (!res.ok) throw new Error("Failed to upload photo");
    return res.json();
}

export async function deletePhoto(propertyId, photoId) {
    const res = await fetch(`${API_BASE}/api/properties/${propertyId}/photos/${photoId}`, {
        method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete photo");
}

// ── CSV Export ──────────────────────────────────────────────────────────

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
