/**
 * Returns the county assessor/auditor deep-link URL for a given APN + county.
 * Spokane County uses the SCOUT parcel search system.
 *   - With APN  → direct parcel deep-link (no typing required)
 *   - Without APN → base SCOUT search page (caller should copy address to clipboard)
 */
export const getCountyAuditorUrl = (apn, county) => {
    const c = (county || '').toLowerCase();
    if (c.includes('spokane')) {
        if (apn) {
            return `https://cp.spokanecounty.org/SCOUT/propertyinformation/Default.aspx?parcel=${encodeURIComponent(apn)}`;
        }
        // No APN yet — send to the search page; caller is expected to copy address to clipboard
        return 'https://cp.spokanecounty.org/scout/propertyinformation/';
    }
    return null;
};

/**
 * Returns a Google Street View URL for a given address + city.
 */
export const getStreetViewUrl = (address, city) => {
    if (!address) return null;
    const query = encodeURIComponent(`${address}, ${city || ''}, WA`);
    return `https://www.google.com/maps/search/?api=1&query=${query}`;
};

/**
 * Computes bid-to-value ratio as a percentage string (e.g. "64.2").
 * Returns null if inputs are missing or zero.
 */
export const computeBidRatio = (bid, value) => {
    if (!bid || !value || value === 0) return null;
    return ((bid / value) * 100).toFixed(1);
};

/**
 * Returns a color token based on bid-to-value ratio:
 *   < 60%  = green (strong deal)
 *   60–79% = orange (moderate)
 *   ≥ 80%  = red (thin margin)
 */
export const bidRatioColor = (ratioStr) => {
    if (!ratioStr) return 'var(--text-secondary)';
    const r = parseFloat(ratioStr);
    if (r < 60) return '#059669';
    if (r < 80) return '#d97706';
    return '#dc2626';
};

/**
 * Parses any known auction date format into a JS Date for sorting.
 * Handles: YYYY-MM-DD, "Aug 28, 10:00 AM", "May 09 - May 11"
 * Returns far-future date for unparseable values so they sort last.
 */
export const parseAuctionDate = (dateStr) => {
    if (!dateStr) return new Date('9999-12-31');
    const now = new Date();
    const thisYear = now.getFullYear();

    // ISO: YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        return new Date(dateStr + 'T00:00:00');
    }

    // Range: "May 09 - May 11" — take start date
    if (dateStr.includes(' - ')) {
        const start = dateStr.split(' - ')[0].trim();
        const d = new Date(`${start}, ${thisYear}`);
        if (!isNaN(d)) {
            if (d < now) d.setFullYear(thisYear + 1);
            return d;
        }
    }

    // "Aug 28, 10:00 AM" — strip time, infer year
    const withTime = dateStr.match(/^([A-Za-z]+ \d+),\s*\d+:\d+/);
    if (withTime) {
        const d = new Date(`${withTime[1]}, ${thisYear}`);
        if (!isNaN(d)) {
            if (d < now) d.setFullYear(thisYear + 1);
            return d;
        }
    }

    // Native fallback
    const d = new Date(dateStr);
    return isNaN(d) ? new Date('9999-12-31') : d;
};

/**
 * Returns the effective status for display.
 * If the scraper left it as "Active" but the auction date has passed, return "Ended".
 */
export const effectiveStatus = (status, auctionDate) => {
    const s = (status || '').toLowerCase();
    if (s.includes('postpone') || s.includes('cancel') || s.includes('end')) return status;
    if (auctionDate && parseAuctionDate(auctionDate) < new Date()) return 'Ended';
    return status || 'Active';
};

export const formatAuctionDateInfo = (dateString, timeString) => {
    if (!dateString) return { pillText: null, bottomDate: 'TBD' };

    let pillText = null;
    let bottomDate = dateString;
    const lower = dateString.toLowerCase();

    // Check if it's already a relative string (e.g. from Auction.com scraper)
    if (lower.includes('starts in') || lower.includes('ends in')) {
        pillText = dateString;

        // Try to estimate the actual date based on the number of days
        const match = lower.match(/\d+/);
        if (match) {
            const days = parseInt(match[0], 10);
            const target = new Date();
            target.setDate(target.getDate() + days);
            bottomDate = target.toISOString().split('T')[0];
        } else {
            bottomDate = 'TBD';
        }
    } else {
        // It's a standard date format
        try {
            const target = new Date(dateString);
            if (!isNaN(target.getTime())) {
                const today = new Date();
                today.setHours(0, 0, 0, 0); // Start of today
                target.setHours(0, 0, 0, 0);

                const diffTime = target - target.getTimezoneOffset() * 60000 - today; // adjusting for simple local math
                // A simpler diffing logic
                const diffDays = Math.ceil((target - today) / (1000 * 60 * 60 * 24));

                if (diffDays > 0) {
                    pillText = `Starts in ${diffDays} days`;
                } else if (diffDays === 0) {
                    pillText = `Starts today`;
                } else {
                    pillText = `Ended`;
                }
                bottomDate = dateString; // Just use the original string which is probably YYYY-MM-DD
            }
        } catch {
            // If date parsing fails, just leave it as is
        }
    }

    // Capitalize pillText properly
    if (pillText) {
        pillText = pillText.charAt(0).toUpperCase() + pillText.slice(1);
    }

    if (timeString && bottomDate !== 'TBD' && !bottomDate.includes(timeString)) {
        bottomDate += ` • ${timeString}`;
    }

    return { pillText, bottomDate };
};
