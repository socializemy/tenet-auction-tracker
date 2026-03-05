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
