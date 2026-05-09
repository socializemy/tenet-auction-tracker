import { useEffect, useState, useRef, useCallback } from 'react';
import {
    formatAuctionDateInfo,
    getCountyAuditorUrl,
    getStreetViewUrl,
    computeBidRatio,
    bidRatioColor,
} from '../utils/helpers';
import { fetchNotes, addNote, deleteNote, fetchPhotos, uploadPhoto, deletePhoto } from '../utils/api';

const DetailRow = ({ label, value, left }) => (
    <div style={{
        padding: '0.75rem 0',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-between',
        paddingRight: left ? '1rem' : 0,
        paddingLeft: left ? 0 : '1rem',
    }}>
        <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{value || '—'}</span>
    </div>
);

const LinkButton = ({ href, children, onClick, title }) => (
    <a
        href={href}
        target="_blank"
        title={title}
        rel="noopener noreferrer"
        style={{
            padding: '0.4rem 0.9rem',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-color)',
            borderRadius: '3px',
            fontSize: '0.85rem',
            textDecoration: 'none',
            color: 'var(--text-primary)',
            fontWeight: 500,
            transition: 'all 0.15s ease',
        }}
        onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--accent-primary)'; e.currentTarget.style.color = 'var(--accent-primary)'; }}
        onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--border-color)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
        onClick={onClick}
    >
        {children}
    </a>
);

const PropertyModal = ({ property: prop, onClose }) => {
    useEffect(() => {
        const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [onClose]);

    let sourcesList = [];
    let sourceUrls = [];
    try { sourcesList = JSON.parse(prop.sources_list || '[]'); } catch { sourcesList = [prop.source]; }
    try { sourceUrls = JSON.parse(prop.source_urls || '[]'); } catch { sourceUrls = []; }

    const { pillText, bottomDate } = formatAuctionDateInfo(prop.auction_date, prop.auction_time);

    // Hero image fallback chain: Zillow photo → Street View → hidden
    const primaryHero = prop.zillow_photo_url || prop.image_url;
    const fallbackHero = prop.zillow_photo_url ? prop.image_url : null;
    const [heroSrc, setHeroSrc] = useState(primaryHero);
    const [heroFailed, setHeroFailed] = useState(!primaryHero);
    const handleHeroError = () => {
        if (fallbackHero && heroSrc !== fallbackHero) {
            setHeroSrc(fallbackHero);
        } else {
            setHeroFailed(true);
        }
    };

    // Deal metrics
    const bidRatio = computeBidRatio(prop.starting_bid, prop.estimated_value);
    const ratioColor = bidRatioColor(bidRatio);
    const equitySpread = prop.estimated_value && prop.starting_bid
        ? prop.estimated_value - prop.starting_bid
        : null;

    // Quick-access links
    const auditorUrl = getCountyAuditorUrl(prop.apn, prop.county);
    const streetViewUrl = getStreetViewUrl(prop.address, prop.city);

    // ── Notes state ──
    const [copiedAddress, setCopiedAddress] = useState(false);
    const [notes, setNotes] = useState([]);
    const [notesLoading, setNotesLoading] = useState(true);
    const [noteAuthor, setNoteAuthor] = useState('');
    const [noteBody, setNoteBody] = useState('');
    const [noteSubmitting, setNoteSubmitting] = useState(false);

    const loadNotes = useCallback(async () => {
        try {
            const data = await fetchNotes(prop.id);
            setNotes(data);
        } catch { /* ignore */ } finally {
            setNotesLoading(false);
        }
    }, [prop.id]);

    useEffect(() => { loadNotes(); }, [loadNotes]);

    const handleAddNote = async (e) => {
        e.preventDefault();
        if (!noteBody.trim()) return;
        setNoteSubmitting(true);
        try {
            await addNote(prop.id, noteAuthor.trim() || 'Team', noteBody.trim());
            setNoteBody('');
            await loadNotes();
        } catch { /* ignore */ } finally {
            setNoteSubmitting(false);
        }
    };

    const handleDeleteNote = async (noteId) => {
        try {
            await deleteNote(prop.id, noteId);
            setNotes(prev => prev.filter(n => n.id !== noteId));
        } catch { /* ignore */ }
    };

    // ── Photos state ──
    const [photos, setPhotos] = useState([]);
    const [photosLoading, setPhotosLoading] = useState(true);
    const [lightboxPhoto, setLightboxPhoto] = useState(null);
    const photoInputRef = useRef(null);

    const loadPhotos = useCallback(async () => {
        try {
            const data = await fetchPhotos(prop.id);
            setPhotos(data);
        } catch { /* ignore */ } finally {
            setPhotosLoading(false);
        }
    }, [prop.id]);

    useEffect(() => { loadPhotos(); }, [loadPhotos]);

    const handlePhotoUpload = async (e) => {
        const files = Array.from(e.target.files);
        for (const file of files) {
            try {
                await uploadPhoto(prop.id, file);
            } catch { /* ignore */ }
        }
        await loadPhotos();
        e.target.value = '';
    };

    const handleDeletePhoto = async (photoId) => {
        try {
            await deletePhoto(prop.id, photoId);
            setPhotos(prev => prev.filter(p => p.id !== photoId));
            if (lightboxPhoto?.id === photoId) setLightboxPhoto(null);
        } catch { /* ignore */ }
    };

    return (
        <div
            onClick={onClose}
            className="property-modal-overlay"
            style={{
                position: 'fixed', inset: 0, zIndex: 1000,
                background: 'rgba(0,0,0,0.6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                padding: '1rem',
                backdropFilter: 'blur(4px)',
            }}
        >
            <div
                onClick={e => e.stopPropagation()}
                className="property-modal-panel"
                style={{
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-color)',
                    maxWidth: '700px',
                    width: '100%',
                    maxHeight: '90vh',
                    overflowY: 'auto',
                    boxShadow: '0 25px 60px rgba(0,0,0,0.25)',
                    animation: 'fadeIn 0.25s ease-out',
                }}
            >
                {/* Hero Image */}
                {!heroFailed && (
                    <div style={{ width: '100%', height: '240px', overflow: 'hidden', position: 'relative' }}>
                        <img
                            src={heroSrc}
                            alt={prop.address}
                            loading="lazy"
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            onError={handleHeroError}
                        />
                        <div style={{
                            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                            background: 'linear-gradient(to bottom, transparent 50%, rgba(0,0,0,0.5))',
                        }} />
                    </div>
                )}

                {/* Header */}
                <div className="modal-header-section" style={{
                    padding: '2rem 2rem 1rem',
                    borderBottom: '2px solid var(--accent-primary)',
                    marginBottom: '1.5rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                }}>
                    <div>
                        <h2 style={{ fontSize: '1.8rem', marginBottom: '0.25rem' }}>
                            {prop.address}
                        </h2>
                        <p style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-body)' }}>
                            {prop.city}, WA {prop.zip_code || ''} &nbsp;·&nbsp; {prop.county} County
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        style={{
                            background: 'none', border: 'none', cursor: 'pointer',
                            fontSize: '1.5rem', color: 'var(--text-secondary)',
                            padding: '0.25rem 0.5rem', lineHeight: 1,
                        }}
                    >✕</button>
                </div>

                {/* Content grid */}
                <div className="modal-content-grid" style={{ padding: '0 2rem 2rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem 2rem' }}>

                    {/* Auction Date */}
                    <div>
                        <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>Auction Date</div>
                        <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '1.1rem' }}>{bottomDate}</div>
                        {pillText && (
                            <div style={{ fontSize: '0.85rem', color: '#059669', fontWeight: 500, marginTop: '0.4rem', background: '#E2F5E9', padding: '2px 8px', borderRadius: '4px', display: 'inline-block' }}>
                                {pillText}
                            </div>
                        )}
                    </div>

                    {/* Status */}
                    <div>
                        <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>Status</div>
                        <span className={`status-badge ${(prop.status || '').toLowerCase().includes('postpone') ? 'postponed' : ''} ${(prop.status || '').toLowerCase().includes('cancel') ? 'canceled' : ''}`}>
                            {prop.status || 'Active'}
                        </span>
                    </div>

                    {/* Opening Bid */}
                    <div>
                        <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>Opening Bid</div>
                        <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '1.3rem', color: 'var(--text-primary)' }}>
                            {prop.starting_bid > 0 ? `$${prop.starting_bid.toLocaleString()}` : 'TBD'}
                        </div>
                    </div>

                    {/* Estimated Market Value */}
                    <div>
                        <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>Est. Market Value (Zillow)</div>
                        <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '1.3rem', color: prop.estimated_value ? '#059669' : 'var(--text-secondary)' }}>
                            {prop.estimated_value ? `$${prop.estimated_value.toLocaleString()}` : '—'}
                        </div>
                    </div>

                    {/* ── Deal Metrics bar ── */}
                    {(bidRatio || equitySpread !== null) && (
                        <div style={{
                            gridColumn: '1 / -1',
                            background: 'var(--bg-secondary)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '6px',
                            padding: '1rem 1.25rem',
                            display: 'flex',
                            gap: '2rem',
                            flexWrap: 'wrap',
                        }}>
                            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-secondary)', width: '100%', marginBottom: '0.25rem' }}>
                                Deal Metrics
                            </div>

                            {bidRatio && (
                                <div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Bid / Market Value</div>
                                    <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '1.4rem', color: ratioColor }}>
                                        {bidRatio}%
                                    </div>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                                        {parseFloat(bidRatio) < 60 ? '▲ Strong deal' : parseFloat(bidRatio) < 80 ? '◆ Moderate' : '▼ Thin margin'}
                                    </div>
                                </div>
                            )}

                            {equitySpread !== null && (
                                <div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Equity Spread</div>
                                    <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '1.4rem', color: equitySpread >= 0 ? '#059669' : '#dc2626' }}>
                                        {equitySpread >= 0 ? '+' : ''}{equitySpread.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
                                    </div>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.15rem' }}>
                                        Market minus opening bid
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* ── Property Details ── */}
                    <div style={{ gridColumn: '1 / -1', marginTop: '0.5rem' }}>
                        <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem' }}>
                            Property Details
                        </div>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr 1fr',
                            gap: '0',
                            borderTop: '1px solid var(--border-color)',
                            fontSize: '0.95rem',
                        }}>
                            <DetailRow label="Beds"             value={prop.bedrooms}                                       left />
                            <DetailRow label="Baths"            value={prop.bathrooms} />
                            <DetailRow label="Square Footage"   value={prop.square_feet ? prop.square_feet.toLocaleString() : null} left />
                            <DetailRow label="Lot Size"         value={prop.lot_size} />
                            <DetailRow label="Property Type"    value={prop.property_type}                                  left />
                            <DetailRow label="Year Built"       value={prop.year_built} />
                            <DetailRow label="Trustee Sale #"   value={prop.tsn}                                            left />
                            <DetailRow label="APN / Parcel ID"  value={prop.apn} />
                        </div>
                    </div>

                    {/* ── Quick Links ── */}
                    <div style={{ gridColumn: '1 / -1' }}>
                        <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                            Quick Links
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                            {prop.zillow_url && (
                                <LinkButton href={prop.zillow_url}>Zillow Listing →</LinkButton>
                            )}
                            {streetViewUrl && (
                                <LinkButton href={streetViewUrl}>Street View →</LinkButton>
                            )}
                        </div>
                    </div>

                </div>

                {/* ── County Record (SCOUT) ── */}
                {prop.scout_fetched_at && (
                    <div style={{ padding: '1.5rem 2rem', borderTop: '1px solid var(--border-color)' }}>

                        {/* Section header */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                                County Record
                                <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 400 }}>
                                    Spokane County SCOUT
                                </span>
                            </div>
                            {prop.apn && (
                                <a href={`https://cp.spokanecounty.org/scout/propertyinformation/Summary.aspx?PID=${encodeURIComponent(prop.apn)}`}
                                   target="_blank" rel="noopener noreferrer"
                                   style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 500 }}>
                                    View Full Record ↗
                                </a>
                            )}
                        </div>

                        {/* Owner card */}
                        {prop.owner_name && (
                            <div style={{ background: 'var(--bg-secondary)', borderRadius: '6px', padding: '0.75rem 1rem', marginBottom: '1rem', display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                                <div>
                                    <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Owner of Record</div>
                                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{prop.owner_name}</div>
                                    {prop.owner_address && <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{prop.owner_address}</div>}
                                </div>
                                {prop.scout_legal && (
                                    <div>
                                        <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>Legal Description</div>
                                        <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{prop.scout_legal}</div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Assessment + Tax grid */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginBottom: '1rem' }}>
                            {[
                                { label: 'Total Assessed', value: prop.assessed_value ? `$${prop.assessed_value.toLocaleString()}` : null },
                                { label: 'Land Value',     value: prop.assessed_land     ? `$${prop.assessed_land.toLocaleString()}`     : null },
                                { label: 'Building Value', value: prop.assessed_building ? `$${prop.assessed_building.toLocaleString()}` : null },
                                { label: 'Annual Taxes',   value: prop.annual_taxes  ? `$${prop.annual_taxes.toLocaleString()}`  : null },
                                { label: 'Taxes Owing',    value: prop.taxes_owing   ? `$${prop.taxes_owing.toLocaleString()}`   : null, highlight: prop.taxes_owing > 0 },
                                { label: 'Lot Size (County)', value: prop.scout_land_sqft ? `${prop.scout_land_sqft.toLocaleString()} sq ft` : null },
                            ].filter(r => r.value).map(({ label, value, highlight }) => (
                                <div key={label} style={{ background: 'var(--bg-secondary)', borderRadius: '6px', padding: '0.6rem 0.8rem' }}>
                                    <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>{label}</div>
                                    <div style={{ fontWeight: 700, fontSize: '1rem', color: highlight ? '#dc2626' : 'var(--text-primary)' }}>{value}</div>
                                </div>
                            ))}
                        </div>

                        {/* County characteristics row */}
                        {(prop.scout_house_type || prop.scout_basement_sqft || prop.scout_garage_sqft || prop.scout_parcel_class) && (
                            <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
                                {prop.scout_parcel_class && <span><strong style={{ color: 'var(--text-primary)' }}>Class:</strong> {prop.scout_parcel_class}</span>}
                                {prop.scout_house_type   && <span><strong style={{ color: 'var(--text-primary)' }}>Type:</strong> {prop.scout_house_type}</span>}
                                {prop.scout_basement_sqft && <span><strong style={{ color: 'var(--text-primary)' }}>Basement:</strong> {prop.scout_basement_sqft.toLocaleString()} sq ft</span>}
                                {prop.scout_garage_sqft  && <span><strong style={{ color: 'var(--text-primary)' }}>Garage:</strong> {prop.scout_garage_sqft.toLocaleString()} sq ft</span>}
                                {prop.scout_tca          && <span><strong style={{ color: 'var(--text-primary)' }}>TCA:</strong> {prop.scout_tca}</span>}
                            </div>
                        )}

                        {/* Sales History */}
                        {prop.scout_sales && (() => {
                            let sales = [];
                            try { sales = JSON.parse(prop.scout_sales); } catch {}
                            if (!sales.length) return null;
                            return (
                                <div style={{ marginBottom: '1rem' }}>
                                    <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Sales History</div>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                        <thead>
                                            <tr style={{ background: 'var(--bg-secondary)' }}>
                                                {['Date', 'Sale Price', 'Instrument'].map(h => (
                                                    <th key={h} style={{ padding: '0.4rem 0.6rem', textAlign: 'left', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {sales.map((s, i) => (
                                                <tr key={i} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                                    <td style={{ padding: '0.4rem 0.6rem', color: 'var(--text-secondary)' }}>{s.date}</td>
                                                    <td style={{ padding: '0.4rem 0.6rem', fontWeight: 600, color: 'var(--text-primary)' }}>{s.price ? `$${Number(s.price).toLocaleString()}` : '—'}</td>
                                                    <td style={{ padding: '0.4rem 0.6rem', color: 'var(--text-secondary)' }}>{s.instrument}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            );
                        })()}

                        {/* Permit History */}
                        {prop.scout_permits && (() => {
                            let permits = [];
                            try { permits = JSON.parse(prop.scout_permits); } catch {}
                            if (!permits.length) return null;
                            return (
                                <div>
                                    <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Permit History</div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                        {permits.slice(0, 8).map((p, i) => (
                                            <div key={i} style={{ display: 'flex', gap: '0.75rem', fontSize: '0.82rem', padding: '0.35rem 0', borderBottom: '1px solid var(--border-color)' }}>
                                                <span style={{ fontFamily: 'monospace', color: 'var(--accent-primary)', minWidth: '110px', flexShrink: 0 }}>{p.number}</span>
                                                <span style={{ color: 'var(--text-secondary)', minWidth: '80px', flexShrink: 0 }}>{p.date}</span>
                                                <span style={{ color: 'var(--text-primary)' }}>{p.description}</span>
                                            </div>
                                        ))}
                                        {permits.length > 8 && <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', paddingTop: '0.25rem' }}>+{permits.length - 8} more permits — <a href={`https://cp.spokanecounty.org/scout/propertyinformation/Summary.aspx?PID=${encodeURIComponent(prop.apn)}`} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-primary)' }}>view all on SCOUT</a></div>}
                                    </div>
                                </div>
                            );
                        })()}

                    </div>
                )}

                {/* ── No County Record yet ── */}
                {!prop.scout_fetched_at && (
                    <div style={{ padding: '1.25rem 2rem', borderTop: '1px solid var(--border-color)', background: 'var(--bg-secondary)' }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
                            <div style={{ flex: 1, minWidth: '200px' }}>
                                <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                                    County Record
                                </div>
                                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>
                                    No county data scraped yet for this property.
                                    Search SCOUT manually using the address below.
                                </div>
                                <div style={{
                                    display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                                    background: 'var(--bg-primary)', border: '1px solid var(--border-color)',
                                    borderRadius: '4px', padding: '0.4rem 0.7rem',
                                    fontSize: '0.9rem', fontFamily: 'monospace', color: 'var(--text-primary)',
                                    userSelect: 'all', cursor: 'text',
                                }}>
                                    {prop.address}{prop.city ? `, ${prop.city}` : ''}{', WA'}
                                </div>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', alignSelf: 'center' }}>
                                <button
                                    onClick={() => {
                                        const addr = `${prop.address}, ${prop.city || 'Spokane'}, WA`;
                                        const copyFallback = () => {
                                            const ta = document.createElement('textarea');
                                            ta.value = addr;
                                            ta.style.position = 'fixed';
                                            ta.style.opacity = '0';
                                            document.body.appendChild(ta);
                                            ta.focus();
                                            ta.select();
                                            document.execCommand('copy');
                                            document.body.removeChild(ta);
                                        };
                                        if (navigator.clipboard) {
                                            navigator.clipboard.writeText(addr).catch(copyFallback);
                                        } else {
                                            copyFallback();
                                        }
                                        setCopiedAddress(true);
                                        setTimeout(() => setCopiedAddress(false), 2000);
                                    }}
                                    style={{
                                        padding: '0.4rem 0.9rem', fontSize: '0.82rem', fontWeight: 600,
                                        background: copiedAddress ? '#16a34a' : 'var(--accent-primary)',
                                        color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer',
                                        transition: 'background 0.2s ease', whiteSpace: 'nowrap',
                                    }}
                                >
                                    {copiedAddress ? '✓ Copied!' : 'Copy Address'}
                                </button>
                                <a
                                    href="https://cp.spokanecounty.org/scout/propertyinformation/"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{
                                        padding: '0.4rem 0.9rem', fontSize: '0.82rem', fontWeight: 500,
                                        background: 'var(--bg-primary)', border: '1px solid var(--border-color)',
                                        borderRadius: '4px', textDecoration: 'none',
                                        color: 'var(--text-primary)', textAlign: 'center', whiteSpace: 'nowrap',
                                    }}
                                >
                                    Open SCOUT ↗
                                </a>
                            </div>
                        </div>
                    </div>
                )}

                {/* ── Team Photos ── */}
                <div style={{ padding: '1.5rem 2rem', borderTop: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                            Team Photos {photos.length > 0 && <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}>({photos.length})</span>}
                        </div>
                        <button
                            onClick={() => photoInputRef.current?.click()}
                            style={{
                                padding: '0.35rem 0.9rem', fontSize: '0.8rem', fontWeight: 600,
                                background: 'var(--accent-primary)', color: '#fff',
                                border: 'none', borderRadius: '4px', cursor: 'pointer',
                            }}
                        >+ Upload Photos</button>
                        <input
                            ref={photoInputRef}
                            type="file"
                            accept="image/*"
                            multiple
                            style={{ display: 'none' }}
                            onChange={handlePhotoUpload}
                        />
                    </div>

                    {photosLoading ? (
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Loading photos…</div>
                    ) : photos.length === 0 ? (
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontStyle: 'italic' }}>No team photos yet. Upload the first one!</div>
                    ) : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '0.5rem' }}>
                            {photos.map(photo => (
                                <div key={photo.id} style={{ position: 'relative', borderRadius: '4px', overflow: 'hidden', aspectRatio: '4/3', background: 'var(--bg-secondary)', cursor: 'pointer' }}>
                                    <img
                                        src={photo.url}
                                        alt={photo.caption || 'Property photo'}
                                        onClick={() => setLightboxPhoto(photo)}
                                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                        onError={e => { e.target.style.display = 'none'; }}
                                    />
                                    <button
                                        onClick={() => handleDeletePhoto(photo.id)}
                                        title="Remove photo"
                                        style={{
                                            position: 'absolute', top: '4px', right: '4px',
                                            background: 'rgba(0,0,0,0.6)', color: '#fff',
                                            border: 'none', borderRadius: '50%',
                                            width: '22px', height: '22px', fontSize: '0.7rem',
                                            cursor: 'pointer', lineHeight: 1,
                                        }}
                                    >✕</button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* ── Lightbox ── */}
                {lightboxPhoto && (
                    <div
                        onClick={() => setLightboxPhoto(null)}
                        style={{
                            position: 'fixed', inset: 0, zIndex: 2000,
                            background: 'rgba(0,0,0,0.85)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            padding: '2rem',
                        }}
                    >
                        <img
                            src={lightboxPhoto.url}
                            alt={lightboxPhoto.caption || ''}
                            onClick={e => e.stopPropagation()}
                            style={{ maxWidth: '90vw', maxHeight: '85vh', objectFit: 'contain', borderRadius: '4px', boxShadow: '0 8px 40px rgba(0,0,0,0.5)' }}
                        />
                    </div>
                )}

                {/* ── Team Notes ── */}
                <div style={{ padding: '1.5rem 2rem', borderTop: '1px solid var(--border-color)' }}>
                    <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem' }}>
                        Team Notes {notes.length > 0 && <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}>({notes.length})</span>}
                    </div>

                    {/* Add note form */}
                    <form onSubmit={handleAddNote} style={{ marginBottom: '1.25rem' }}>
                        <input
                            type="text"
                            placeholder="Your name (optional)"
                            value={noteAuthor}
                            onChange={e => setNoteAuthor(e.target.value)}
                            style={{
                                width: '100%', boxSizing: 'border-box',
                                padding: '0.5rem 0.75rem', marginBottom: '0.5rem',
                                border: '1px solid var(--border-color)', borderRadius: '4px',
                                background: 'var(--bg-secondary)', color: 'var(--text-primary)',
                                fontSize: '0.9rem',
                            }}
                        />
                        <textarea
                            placeholder="Add a team note…"
                            value={noteBody}
                            onChange={e => setNoteBody(e.target.value)}
                            rows={3}
                            style={{
                                width: '100%', boxSizing: 'border-box',
                                padding: '0.5rem 0.75rem', marginBottom: '0.5rem',
                                border: '1px solid var(--border-color)', borderRadius: '4px',
                                background: 'var(--bg-secondary)', color: 'var(--text-primary)',
                                fontSize: '0.9rem', resize: 'vertical',
                            }}
                        />
                        <button
                            type="submit"
                            disabled={noteSubmitting || !noteBody.trim()}
                            style={{
                                padding: '0.45rem 1.1rem', fontSize: '0.875rem', fontWeight: 600,
                                background: noteBody.trim() ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                                color: noteBody.trim() ? '#fff' : 'var(--text-secondary)',
                                border: '1px solid var(--border-color)', borderRadius: '4px',
                                cursor: noteBody.trim() ? 'pointer' : 'default',
                                transition: 'all 0.15s ease',
                            }}
                        >{noteSubmitting ? 'Saving…' : 'Add Note'}</button>
                    </form>

                    {/* Notes list */}
                    {notesLoading ? (
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Loading notes…</div>
                    ) : notes.length === 0 ? (
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontStyle: 'italic' }}>No notes yet.</div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {notes.map(note => (
                                <div key={note.id} style={{
                                    background: 'var(--bg-secondary)',
                                    border: '1px solid var(--border-color)',
                                    borderRadius: '6px',
                                    padding: '0.75rem 1rem',
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                                        <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--accent-primary)' }}>{note.author}</span>
                                        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                                {new Date(note.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                            <button
                                                onClick={() => handleDeleteNote(note.id)}
                                                title="Delete note"
                                                style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.8rem', padding: '0' }}
                                            >✕</button>
                                        </div>
                                    </div>
                                    <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-primary)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{note.body}</p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* ── Sources footer ── */}
                <div style={{ padding: '1.5rem 2rem', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-color)' }}>
                    <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
                        Found on {sourcesList.length} source{sourcesList.length !== 1 ? 's' : ''}
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {sourcesList.map((src, i) => (
                            <LinkButton key={src} href={sourceUrls[i] || '#'}>{src}</LinkButton>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PropertyModal;
