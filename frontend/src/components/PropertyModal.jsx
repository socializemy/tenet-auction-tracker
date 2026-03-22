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
                {/* Hero Image */}
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
                <div style={{ padding: '0 2rem 2rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem 2rem' }}>

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
                            {auditorUrl && (
                                prop.apn ? (
                                    // Direct deep-link when we have the parcel number
                                    <LinkButton href={auditorUrl}>County Assessor →</LinkButton>
                                ) : (
                                    // No APN yet — open search page and copy address to clipboard
                                    <LinkButton
                                        href={auditorUrl}
                                        onClick={() => {
                                            const addr = `${prop.address}, ${prop.city || 'Spokane'}, WA`;
                                            navigator.clipboard.writeText(addr).catch(() => {});
                                        }}
                                        title={`Address copied to clipboard — paste into SCOUT's search box`}
                                    >
                                        County Assessor (copy address) →
                                    </LinkButton>
                                )
                            )}
                            {streetViewUrl && (
                                <LinkButton href={streetViewUrl}>Street View →</LinkButton>
                            )}
                        </div>
                    </div>

                </div>

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
