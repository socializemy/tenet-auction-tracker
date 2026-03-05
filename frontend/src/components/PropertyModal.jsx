import { useEffect } from 'react';

import { formatAuctionDateInfo } from '../utils/helpers';

const PropertyModal = ({ property: prop, onClose }) => {
    // Close on Escape
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

    return (
        <div
            onClick={onClose}
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
                {/* Image */}
                {prop.image_url && (
                    <div style={{ width: '100%', height: '240px', overflow: 'hidden', position: 'relative' }}>
                        <img
                            src={prop.image_url}
                            alt={prop.address}
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            onError={e => { e.target.style.display = 'none'; }}
                        />
                        <div style={{
                            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                            background: 'linear-gradient(to bottom, transparent 50%, rgba(0,0,0,0.5))',
                        }} />
                    </div>
                )}

                {/* Header */}
                <div style={{
                    padding: '2rem 2rem 0',
                    borderBottom: '2px solid var(--accent-primary)',
                    marginBottom: '1.5rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    paddingBottom: '1rem',
                }}>
                    <div>
                        <h2 style={{ fontSize: '1.8rem', marginBottom: '0.25rem' }}>
                            {prop.address}
                        </h2>
                        <p style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-body)' }}>
                            {prop.city}, WA {prop.zip_code || ''}
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

                {/* Content */}
                <div style={{ padding: '0 2rem 2rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem 2rem' }}>
                    {/* Auction Info */}
                    <div>
                        <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>Auction Date</div>
                        <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '1.1rem' }}>
                            {bottomDate}
                        </div>
                        {pillText && (
                            <div style={{ fontSize: '0.85rem', color: '#059669', fontWeight: 500, marginTop: '0.4rem', background: '#E2F5E9', padding: '2px 8px', borderRadius: '4px', display: 'inline-block' }}>
                                {pillText}
                            </div>
                        )}
                    </div>

                    <div>
                        <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>Status</div>
                        <span className={`status-badge ${(prop.status || '').toLowerCase().includes('postpone') ? 'postponed' : ''} ${(prop.status || '').toLowerCase().includes('cancel') ? 'canceled' : ''}`}>
                            {prop.status || 'Active'}
                        </span>
                    </div>

                    <div>
                        <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>Opening Bid</div>
                        <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '1.3rem', color: 'var(--text-primary)' }}>
                            {prop.starting_bid > 0 ? `$${prop.starting_bid.toLocaleString()}` : 'TBD'}
                        </div>
                    </div>

                    <div>
                        <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>Estimated Market Value</div>
                        <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '1.3rem', color: prop.estimated_value ? '#059669' : 'var(--text-secondary)' }}>
                            {prop.estimated_value ? `$${prop.estimated_value.toLocaleString()}` : '—'}
                        </div>
                    </div>


                    <div style={{ gridColumn: '1 / -1', marginTop: '1rem' }}>
                        <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem' }}>
                            Property Details
                        </div>

                        <div className="property-details-grid" style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr 1fr',
                            gap: '0',
                            borderTop: '1px solid var(--border-color)',
                            fontSize: '0.95rem'
                        }}>
                            {/* Row 1 */}
                            <div style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', paddingRight: '1rem' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>Beds</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{prop.bedrooms ?? '—'}</span>
                            </div>
                            <div style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', paddingLeft: '1rem' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>Baths</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{prop.bathrooms ?? '—'}</span>
                            </div>

                            {/* Row 2 */}
                            <div style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', paddingRight: '1rem' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>Square Footage</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{prop.square_feet ? prop.square_feet.toLocaleString() : '—'}</span>
                            </div>
                            <div style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', paddingLeft: '1rem' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>Lot Size</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{prop.lot_size || '—'}</span>
                            </div>

                            {/* Row 3 */}
                            <div style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', paddingRight: '1rem' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>Property Type</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{prop.property_type || '—'}</span>
                            </div>
                            <div style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', paddingLeft: '1rem' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>Year Built</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{prop.year_built || '—'}</span>
                            </div>

                            {/* Row 4 */}
                            <div style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', paddingRight: '1rem' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>Trustee Sale Number</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{prop.tsn || '—'}</span>
                            </div>
                            <div style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', paddingLeft: '1rem' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>APN</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{prop.apn || '—'}</span>
                            </div>
                        </div>
                    </div>

                    {prop.zillow_url && (
                        <div>
                            <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>Zillow Listing</div>
                            <a href={prop.zillow_url} target="_blank" rel="noopener noreferrer"
                                style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 500 }}>
                                View on Zillow →
                            </a>
                        </div>
                    )}
                </div>

                {/* Sources */}
                <div style={{ padding: '1.5rem 2rem', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-color)' }}>
                    <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.75rem' }}>
                        Found on {sourcesList.length} source{sourcesList.length !== 1 ? 's' : ''}
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {sourcesList.map((src, i) => (
                            <a
                                key={src}
                                href={sourceUrls[i] || '#'}
                                target="_blank"
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
                            >
                                {src}
                            </a>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PropertyModal;
