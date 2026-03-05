import React from 'react';
import { MapPin, Calendar, Tag, Home, Bed, Bath, Square } from 'lucide-react';

import { formatAuctionDateInfo } from '../utils/helpers';

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

const StatusBadge = ({ status }) => {
    const lower = status?.toLowerCase() || '';
    let cls = 'status-badge';
    if (lower.includes('postpone')) cls += ' postponed';
    else if (lower.includes('cancel')) cls += ' canceled';
    return <span className={cls}>{status || 'Active'}</span>;
};

const PropertyCard = ({ property, onClick }) => {
    let sourcesList = [];
    try { sourcesList = JSON.parse(property.sources_list || '[]'); } catch { sourcesList = [property.source]; }

    const { pillText, bottomDate } = formatAuctionDateInfo(property.auction_date, property.auction_time);

    return (
        <div className="property-card" onClick={() => onClick && onClick(property)}>
            <div className="property-card-image">
                {property.image_url ? (
                    <img src={property.image_url} alt={property.address} />
                ) : (
                    <div className="image-placeholder">
                        <Home size={32} opacity={0.3} />
                        <span>No Image Available</span>
                    </div>
                )}
                <div className="status-overlay">
                    <StatusBadge status={property.status} />
                </div>
            </div>

            <div className="property-card-content">
                <div className="price-row">
                    <div className="price-column-left" style={{ gap: '6px' }}>
                        {property.starting_bid > 0 ? (
                            <div className="price-group">
                                <div className="value" style={{ fontSize: '1.6rem', lineHeight: '1' }}>
                                    ${property.starting_bid.toLocaleString()}
                                </div>
                                <div className="est-value-text" style={{ fontSize: '0.75rem', marginTop: '2px' }}>Opening Bid</div>
                            </div>
                        ) : null}

                        {property.estimated_value ? (
                            <div className="price-group">
                                <div className="value" style={{
                                    fontSize: property.starting_bid > 0 ? '1.1rem' : '1.6rem',
                                    lineHeight: '1',
                                    color: property.starting_bid > 0 ? '#059669' : 'var(--text-primary)'
                                }}>
                                    ${property.estimated_value.toLocaleString()}
                                </div>
                                <div className="est-value-text" style={{ fontSize: '0.75rem', marginTop: '2px' }}>Est. Market Value</div>
                            </div>
                        ) : null}

                        {(!property.starting_bid && !property.estimated_value) && (
                            <div className="price-group">
                                <div className="value" style={{ fontSize: '1.6rem', lineHeight: '1' }}>TBD</div>
                                <div className="est-value-text" style={{ fontSize: '0.75rem', marginTop: '2px' }}>Opening Bid</div>
                            </div>
                        )}
                    </div>
                    <div className="price-column-right">
                        {pillText && (
                            <span className="countdown-pill-inline">{pillText}</span>
                        )}
                    </div>
                </div>

                <div className="stats-row">
                    <span><strong>{property.bedrooms || '—'}</strong> bd</span>
                    <span className="stat-divider">|</span>
                    <span><strong>{property.bathrooms || '—'}</strong> ba</span>
                    <span className="stat-divider">|</span>
                    <span><strong>{property.square_feet ? property.square_feet.toLocaleString() : '—'}</strong> sq. ft.</span>
                </div>

                <div className="address-row" style={{ marginTop: '8px' }}>
                    <MapPin size={16} className="text-muted" />
                    <span className="address-text">{property.address}, {property.city}</span>
                </div>

                <div className="meta-row">
                    <div className="meta-item">
                        <Calendar size={14} className="text-muted" />
                        <span>{bottomDate}</span>
                    </div>
                    {property.tsn && (
                        <div className="meta-item">
                            <Tag size={14} className="text-muted" />
                            <span>TSN: {property.tsn}</span>
                        </div>
                    )}
                </div>

                <div className="sources-row">
                    {sourcesList.slice(0, 3).map(s => {
                        const color = SOURCE_COLORS[s] || "#7A7A7A";
                        return (
                            <span key={s} className="source-pill" style={{ '--source-color': color, '--source-bg': `${color}18` }}>
                                {s}
                            </span>
                        );
                    })}
                    {sourcesList.length > 3 && (
                        <span className="source-pill more">+{sourcesList.length - 3}</span>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PropertyCard;
