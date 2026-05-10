import React, { useState, useMemo } from 'react';
import { formatAuctionDateInfo, computeBidRatio, bidRatioColor, parseAuctionDate, effectiveStatus } from '../utils/helpers';

const SOURCE_SHORT = {
    "Nationwide Posting": "Nationwide",
    "Quality Loan": "Qual.Loan",
    "Clear Recon WA": "ClearRecon",
    "Auction.com": "Auction",
    "Xome": "Xome",
    "Elite Post & Pub": "Elite",
    "Aztec Trustee WA": "Aztec",
    "Stox Posting": "Stox",
    "ServiceLink ASAP": "SvcLink",
    "InsourceLogic": "Insource",
};

const SOURCE_COLORS = {
    "Nationwide Posting": "#2563EB",
    "Quality Loan": "#7C3AED",
    "Clear Recon WA": "#059669",
    "Auction.com": "#D97706",
    "Xome": "#DB2777",
    "Elite Post & Pub": "#0891B2",
    "Aztec Trustee WA": "#65A30D",
    "Stox Posting": "#EA580C",
    "ServiceLink ASAP": "#6366F1",
    "InsourceLogic": "#BE123C",
};

const RowBadge = ({ status }) => {
    const lower = status?.toLowerCase() || '';
    let bg = 'rgba(237,28,36,0.08)', color = 'var(--accent-primary)', border = 'rgba(237,28,36,0.2)';
    if (lower.includes('postpone')) { bg = 'rgba(245,166,35,0.1)'; color = '#E09415'; border = 'rgba(245,166,35,0.25)'; }
    else if (lower.includes('cancel')) { bg = 'rgba(122,122,122,0.1)'; color = 'var(--text-secondary)'; border = 'rgba(122,122,122,0.2)'; }
    return (
        <span style={{
            display: 'inline-block', padding: '0.15rem 0.45rem', borderRadius: '3px',
            fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em',
            background: bg, color, border: `1px solid ${border}`, whiteSpace: 'nowrap',
        }}>
            {status || 'Active'}
        </span>
    );
};

const TH = ({ children, col, sort, onSort, style = {} }) => {
    const active = sort.col === col;
    return (
        <th
            onClick={col ? () => onSort(col) : undefined}
            style={{
                padding: '0.55rem 0.75rem',
                textAlign: 'left',
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                fontWeight: 600,
                color: active ? 'var(--accent-primary)' : 'var(--text-secondary)',
                borderBottom: '2px solid var(--border-color)',
                background: 'var(--bg-primary)',
                position: 'sticky',
                top: 0,
                whiteSpace: 'nowrap',
                cursor: col ? 'pointer' : 'default',
                userSelect: 'none',
                zIndex: 2,
                ...style,
            }}
        >
            {children}
            {col && (
                <span style={{ marginLeft: '3px', opacity: active ? 1 : 0.3 }}>
                    {active ? (sort.dir === 'asc' ? '↑' : '↓') : '↕'}
                </span>
            )}
        </th>
    );
};

const PropertyListView = ({ properties, loading, onPropertySelect }) => {
    const [sort, setSort] = useState({ col: 'auction_date', dir: 'asc' });

    const toggleSort = (col) => {
        setSort(s => s.col === col ? { col, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { col, dir: 'asc' });
    };

    const sorted = useMemo(() => {
        const arr = [...properties];
        arr.sort((a, b) => {
            let av, bv;
            if (sort.col === 'auction_date') { av = parseAuctionDate(a.auction_date); bv = parseAuctionDate(b.auction_date); }
            else if (sort.col === 'starting_bid') { av = a.starting_bid || 0; bv = b.starting_bid || 0; }
            else if (sort.col === 'estimated_value') { av = a.estimated_value || 0; bv = b.estimated_value || 0; }
            else if (sort.col === 'address') { av = a.address || ''; bv = b.address || ''; }
            else if (sort.col === 'bid_ratio') {
                av = (a.starting_bid && a.estimated_value) ? a.starting_bid / a.estimated_value : 999;
                bv = (b.starting_bid && b.estimated_value) ? b.starting_bid / b.estimated_value : 999;
            } else { av = 0; bv = 0; }
            if (av < bv) return sort.dir === 'asc' ? -1 : 1;
            if (av > bv) return sort.dir === 'asc' ? 1 : -1;
            return 0;
        });
        return arr;
    }, [properties, sort]);

    if (loading) return <div className="list-loader"><div className="spinner" /><p>Loading properties…</p></div>;
    if (!properties.length) return <div className="list-empty"><p>No properties found matching your criteria.</p></div>;

    return (
        <div style={{ flex: 1, overflow: 'auto', background: 'var(--bg-primary)' }}>
            <div style={{ padding: '0.5rem 1.5rem', borderBottom: '1px solid var(--border-color)', fontSize: '0.85rem', fontWeight: 500, background: 'var(--bg-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>{sorted.length} properties</span>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>— click any row to open</span>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                <thead>
                    <tr>
                        <TH sort={sort} style={{ width: '56px', paddingLeft: '1.5rem' }}></TH>
                        <TH col="address" sort={sort} onSort={toggleSort}>Address</TH>
                        <TH sort={sort}>Status</TH>
                        <TH col="starting_bid" sort={sort} onSort={toggleSort}>Opening Bid</TH>
                        <TH col="estimated_value" sort={sort} onSort={toggleSort}>Est. Value</TH>
                        <TH col="bid_ratio" sort={sort} onSort={toggleSort}>Ratio</TH>
                        <TH sort={sort}>Beds · Ba · Sqft</TH>
                        <TH col="auction_date" sort={sort} onSort={toggleSort}>Auction Date</TH>
                        <TH sort={sort}>APN</TH>
                        <TH sort={sort} style={{ paddingRight: '1.5rem' }}>Source</TH>
                    </tr>
                </thead>
                <tbody>
                    {sorted.map((prop, idx) => {
                        const { bottomDate, pillText } = formatAuctionDateInfo(prop.auction_date, prop.auction_time);
                        const status = effectiveStatus(prop.status, prop.auction_date);
                        const bidRatio = computeBidRatio(prop.starting_bid, prop.estimated_value);
                        const ratioColor = bidRatioColor(bidRatio);
                        let sourcesList = [];
                        try { sourcesList = JSON.parse(prop.sources_list || '[]'); } catch { sourcesList = [prop.source]; }

                        return (
                            <tr
                                key={prop.id}
                                onClick={() => onPropertySelect(prop)}
                                style={{
                                    cursor: 'pointer',
                                    borderBottom: '1px solid var(--border-color)',
                                    background: idx % 2 === 0 ? 'var(--bg-primary)' : 'var(--bg-secondary)',
                                }}
                                onMouseOver={e => { e.currentTarget.style.background = 'rgba(237,28,36,0.04)'; e.currentTarget.style.borderColor = 'rgba(237,28,36,0.15)'; }}
                                onMouseOut={e => { e.currentTarget.style.background = idx % 2 === 0 ? 'var(--bg-primary)' : 'var(--bg-secondary)'; e.currentTarget.style.borderColor = 'var(--border-color)'; }}
                            >
                                {/* Thumbnail */}
                                <td style={{ padding: '0.4rem 0.5rem 0.4rem 1.5rem', width: '56px' }}>
                                    {prop.image_url ? (
                                        <img src={prop.image_url} alt="" style={{ width: '52px', height: '40px', objectFit: 'cover', borderRadius: '4px', display: 'block' }} />
                                    ) : (
                                        <div style={{ width: '52px', height: '40px', background: 'var(--bg-tertiary)', borderRadius: '4px' }} />
                                    )}
                                </td>

                                {/* Address */}
                                <td style={{ padding: '0.5rem 0.75rem', minWidth: '160px' }}>
                                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.3, fontSize: '0.875rem' }}>{prop.address}</div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '1px' }}>
                                        {prop.city}{prop.zip_code ? ` ${prop.zip_code}` : ''}
                                    </div>
                                </td>

                                {/* Status */}
                                <td style={{ padding: '0.5rem 0.75rem', whiteSpace: 'nowrap' }}>
                                    <RowBadge status={status} />
                                </td>

                                {/* Opening Bid */}
                                <td style={{ padding: '0.5rem 0.75rem', fontWeight: 700, whiteSpace: 'nowrap', fontFamily: 'var(--font-heading)', fontSize: '0.95rem' }}>
                                    {prop.starting_bid ? `$${prop.starting_bid.toLocaleString()}` : <span style={{ color: 'var(--text-secondary)' }}>TBD</span>}
                                </td>

                                {/* Est. Value */}
                                <td style={{ padding: '0.5rem 0.75rem', whiteSpace: 'nowrap', color: '#059669', fontWeight: 600 }}>
                                    {prop.estimated_value ? `$${prop.estimated_value.toLocaleString()}` : <span style={{ color: 'var(--text-secondary)' }}>—</span>}
                                </td>

                                {/* Bid Ratio */}
                                <td style={{ padding: '0.5rem 0.75rem', whiteSpace: 'nowrap' }}>
                                    {bidRatio ? (
                                        <span style={{ fontWeight: 700, color: ratioColor, fontSize: '0.875rem' }}>{bidRatio}%</span>
                                    ) : <span style={{ color: 'var(--text-secondary)' }}>—</span>}
                                </td>

                                {/* Beds/Ba/Sqft */}
                                <td style={{ padding: '0.5rem 0.75rem', whiteSpace: 'nowrap', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                                    {[
                                        prop.bedrooms && `${prop.bedrooms} bd`,
                                        prop.bathrooms && `${prop.bathrooms} ba`,
                                        prop.square_feet && `${prop.square_feet.toLocaleString()} sf`,
                                    ].filter(Boolean).join(' · ') || '—'}
                                </td>

                                {/* Auction Date */}
                                <td style={{ padding: '0.5rem 0.75rem', whiteSpace: 'nowrap', fontSize: '0.82rem' }}>
                                    <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{bottomDate}</div>
                                    {pillText && (
                                        <div style={{ marginTop: '2px' }}>
                                            <span style={{ fontSize: '0.68rem', padding: '1px 6px', borderRadius: '999px', background: '#E2F5E9', color: '#166534', fontWeight: 600 }}>
                                                {pillText}
                                            </span>
                                        </div>
                                    )}
                                </td>

                                {/* APN */}
                                <td style={{ padding: '0.5rem 0.75rem', fontSize: '0.78rem', color: 'var(--text-secondary)', fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                                    {prop.apn || '—'}
                                </td>

                                {/* Source */}
                                <td style={{ padding: '0.5rem 0.75rem 0.5rem 0.75rem', paddingRight: '1.5rem' }}>
                                    <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                                        {sourcesList.slice(0, 2).map(s => {
                                            const color = SOURCE_COLORS[s] || '#7A7A7A';
                                            return (
                                                <span key={s} style={{
                                                    fontSize: '0.62rem', padding: '0.12rem 0.4rem', borderRadius: '3px',
                                                    background: `${color}18`, color, border: `1px solid ${color}40`,
                                                    fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.02em',
                                                    whiteSpace: 'nowrap',
                                                }}>
                                                    {SOURCE_SHORT[s] || s.split(' ')[0]}
                                                </span>
                                            );
                                        })}
                                        {sourcesList.length > 2 && (
                                            <span style={{
                                                fontSize: '0.62rem', padding: '0.12rem 0.4rem', borderRadius: '3px',
                                                background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
                                                border: '1px solid var(--border-color)', fontWeight: 600,
                                            }}>+{sourcesList.length - 2}</span>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

export default PropertyListView;
