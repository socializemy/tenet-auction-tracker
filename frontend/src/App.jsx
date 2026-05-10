import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { fetchProperties, triggerScrape, fetchScrapeStatus, exportCsv } from './utils/api';
import { parseAuctionDate } from './utils/helpers';
import { Search, PanelLeft, List, LayoutGrid } from 'lucide-react';
import PropertyList from './components/PropertyList';
import PropertyCard from './components/PropertyCard';
import PropertyListView from './components/PropertyListView';
import PropertyMap from './components/PropertyMap';
import PropertyModal from './components/PropertyModal';

function App() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [selectedProp, setSelectedProp] = useState(null);
  const [scrapeMsg, setScrapeMsg] = useState('');
  const [progressPercent, setProgressPercent] = useState(0);

  // View mode: 'split' (default on desktop) | 'list' | 'grid'
  // Default to 'grid' on mobile since split view doesn't work on small screens
  const [viewMode, setViewMode] = useState(() => window.innerWidth < 768 ? 'grid' : 'split');

  const [filters, setFilters] = useState({
    county: '',
    sort_by: 'auction_date',
  });

  // Extra filters shown in List view
  const [listFilters, setListFilters] = useState({
    status: '',
    minBeds: '',
  });

  const [searchTerm, setSearchTerm] = useState('');

  const loadProperties = useCallback(async (silent = false) => {
    if (silent !== true) setLoading(true);
    try {
      const data = await fetchProperties(filters);
      setProperties(data);
    } catch (e) {
      console.error(e);
    } finally {
      if (silent !== true) setLoading(false);
    }
  }, [filters]);

  useEffect(() => { loadProperties(); }, [loadProperties]);

  // Check initial scrape status on mount
  useEffect(() => {
    fetchScrapeStatus().then(status => {
      if (status && status.running) {
        setScraping(true);
        setScrapeMsg(status.status_text || 'Scraping in progress (loading live data)...');
        setProgressPercent(status.progress_percent || 0);
      }
    }).catch(e => console.error(e));
  }, []);

  // Poll scrape status to sync across tabs/refreshes and dynamically load enriched properties
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const status = await fetchScrapeStatus();
        if (status.running) {
          loadProperties(true);
          setProgressPercent(status.progress_percent || 0);
          setScrapeMsg(status.status_text || 'Scraping in progress...');
        }
        if (status.running && !scraping) {
          setScraping(true);
        } else if (!status.running && scraping) {
          setScraping(false);
          setProgressPercent(100);
          setScrapeMsg(`Done! ${status.total_scraped ?? 0} properties loaded.`);
          loadProperties(true);
          setTimeout(() => { setScrapeMsg(''); setProgressPercent(0); }, 6000);
        }
      } catch (e) { /* ignore */ }
    }, 4000);
    return () => clearInterval(interval);
  }, [scraping, loadProperties]);

  const handleRefresh = async () => {
    setScraping(true);
    setProgressPercent(0);
    setScrapeMsg('Initializing connection to backend...');
    try {
      await triggerScrape();
    } catch (e) {
      setScraping(false);
      setProgressPercent(0);
      setScrapeMsg('Scrape trigger failed. Is the backend running?');
      setTimeout(() => setScrapeMsg(''), 5000);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(f => ({ ...f, [key]: value }));
  };

  // Text search filter
  const filteredProperties = useMemo(() => {
    if (!searchTerm.trim()) return properties;
    const lowerTerm = searchTerm.toLowerCase().trim();
    return properties.filter(p =>
      p.address?.toLowerCase().includes(lowerTerm) ||
      p.city?.toLowerCase().includes(lowerTerm) ||
      p.zip_code?.toLowerCase().includes(lowerTerm) ||
      p.tsn?.toLowerCase().includes(lowerTerm)
    );
  }, [properties, searchTerm]);

  // Additional list-view filters (applied in all views once set, but controls only show in list view)
  const displayedProperties = useMemo(() => {
    let result = filteredProperties;
    if (listFilters.status) {
      result = result.filter(p => {
        const s = (p.status || '').toLowerCase();
        if (listFilters.status === 'active') return !s.includes('postpone') && !s.includes('cancel');
        if (listFilters.status === 'postponed') return s.includes('postpone');
        if (listFilters.status === 'canceled') return s.includes('cancel');
        return true;
      });
    }
    if (listFilters.minBeds) {
      result = result.filter(p => (p.bedrooms || 0) >= parseInt(listFilters.minBeds));
    }
    result = [...result].sort((a, b) => parseAuctionDate(a.auction_date) - parseAuctionDate(b.auction_date));
    return result;
  }, [filteredProperties, listFilters]);

  const isMobile = window.innerWidth < 768;

  const VIEW_TABS = [
    ...(!isMobile ? [{ id: 'split', label: 'Split', Icon: PanelLeft, title: 'Split view — cards + map' }] : []),
    { id: 'list',  label: 'List',  Icon: List,       title: 'List view — sortable table' },
    { id: 'grid',  label: 'Grid',  Icon: LayoutGrid, title: 'Grid view — 3-column cards' },
  ];

  return (
    <div className="app-container-split">
      {selectedProp && (
        <PropertyModal property={selectedProp} onClose={() => setSelectedProp(null)} />
      )}

      {/* ── Header ── */}
      <header className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', zIndex: 100 }}>
        <div className="header-logo">
          <div style={{ width: '36px', height: '36px', background: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
          </div>
          <span>TENET <span className="text-gradient">AUCTION </span>TRACKER</span>
        </div>
        <div className="header-source-links" style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end', maxWidth: '60%' }}>
          <a href="https://search.nationwideposting.com/SearchTerms.aspx" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textDecoration: 'none', fontFamily: 'var(--font-body)' }}>Nationwide Posting ↗</a>
          <a href="https://www.qualityloan.com/QLSPortal/PagesPublic/Login.aspx" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textDecoration: 'none', fontFamily: 'var(--font-body)' }}>Quality Loan ↗</a>
          <a href="https://clearrecon-wa.com/washington-listings/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textDecoration: 'none', fontFamily: 'var(--font-body)' }}>Clear Recon WA ↗</a>
          <a href="https://www.auction.com/residential/wa/spokane-county/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textDecoration: 'none', fontFamily: 'var(--font-body)' }}>Auction.com ↗</a>
          <a href="https://www.xome.com/auctions/listing/WA/Spokane" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textDecoration: 'none', fontFamily: 'var(--font-body)' }}>Xome ↗</a>
          <a href="https://elitepostandpub.com/index.php" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textDecoration: 'none', fontFamily: 'var(--font-body)' }}>Elite Post &amp; Pub ↗</a>
          <a href="https://www.aztectrustee-wa.com/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textDecoration: 'none', fontFamily: 'var(--font-body)' }}>Aztec Trustee WA ↗</a>
          <a href="https://www.stoxposting.com/" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textDecoration: 'none', fontFamily: 'var(--font-body)' }}>Stox Posting ↗</a>
          <a href="https://www.servicelinkasap.com/quicksearch.aspx" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textDecoration: 'none', fontFamily: 'var(--font-body)' }}>ServiceLink ASAP ↗</a>
          <a href="https://insourcelogic.com/SalesSearch.aspx" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textDecoration: 'none', fontFamily: 'var(--font-body)' }}>Insource Logic ↗</a>
        </div>
      </header>

      {/* ── Global Filter Bar ── */}
      <div className="filter-bar">

        {/* Search */}
        <div className="omnibar-container">
          <Search className="omnibar-icon" size={18} />
          <input
            type="text"
            className="omnibar-input"
            placeholder="Search by Address, City, Zip, or Asset ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Sort */}
        <select value={filters.sort_by} onChange={e => handleFilterChange('sort_by', e.target.value)}>
          <option value="auction_date">Sort: Date</option>
          <option value="starting_bid">Sort: Lowest Bid</option>
          <option value="estimated_value">Sort: Highest Value</option>
        </select>

        {/* List-view extra filters */}
        {viewMode === 'list' && (
          <>
            <select
              value={listFilters.status}
              onChange={e => setListFilters(f => ({ ...f, status: e.target.value }))}
              title="Filter by status"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="postponed">Postponed</option>
              <option value="canceled">Canceled</option>
            </select>
            <select
              value={listFilters.minBeds}
              onChange={e => setListFilters(f => ({ ...f, minBeds: e.target.value }))}
              title="Minimum bedrooms"
            >
              <option value="">Any Beds</option>
              <option value="1">1+ Bed</option>
              <option value="2">2+ Beds</option>
              <option value="3">3+ Beds</option>
              <option value="4">4+ Beds</option>
            </select>
          </>
        )}

        {/* Spacer */}
        <div style={{ flex: 1, minWidth: '0.5rem' }} />

        {/* View mode tabs */}
        <div className="view-tabs">
          {VIEW_TABS.map(({ id, label, Icon, title }) => (
            <button
              key={id}
              title={title}
              className={`view-tab-btn${viewMode === id ? ' active' : ''}`}
              onClick={() => setViewMode(id)}
            >
              <Icon size={14} />
              <span>{label}</span>
            </button>
          ))}
        </div>

        {/* Refresh */}
        <button
          className="btn"
          onClick={handleRefresh}
          disabled={scraping}
          style={{
            background: scraping ? 'var(--bg-tertiary)' : 'var(--bg-primary)',
            color: scraping ? 'var(--text-secondary)' : 'var(--text-primary)',
            border: '1px solid var(--border-color)',
            padding: '0.5rem 1rem',
            fontSize: '0.85rem',
          }}
        >
          {scraping ? '⟳ Scraping...' : '↺ Refresh Data'}
        </button>
      </div>

      {/* ── Scrape Progress Banner ── */}
      {scrapeMsg && (
        <div style={{
          padding: '0.6rem 1.5rem',
          background: scraping ? 'rgba(37, 99, 235, 0.06)' : 'rgba(5, 150, 105, 0.06)',
          borderBottom: '1px solid var(--border-color)',
          fontSize: '0.8rem',
          color: scraping ? '#2563EB' : '#059669',
          fontWeight: 500,
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
          flexShrink: 0,
        }}>
          <div>{scrapeMsg}</div>
          {scraping && (
            <div style={{ width: '100%', height: '4px', background: 'rgba(37, 99, 235, 0.2)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ width: `${progressPercent}%`, height: '100%', background: '#2563EB', transition: 'width 0.5s ease-in-out' }} />
            </div>
          )}
        </div>
      )}

      {/* ── Main Content Area ── */}

      {/* SPLIT VIEW (default) */}
      {viewMode === 'split' && (
        <div className="split-view-container">
          <div className="list-pane">
            <PropertyList
              properties={displayedProperties}
              loading={loading}
              selectedProperty={selectedProp}
              onPropertySelect={setSelectedProp}
            />
          </div>
          <div className="map-pane">
            <PropertyMap
              properties={displayedProperties}
              selectedProperty={selectedProp}
              onPropertySelect={setSelectedProp}
            />
          </div>
        </div>
      )}

      {/* LIST VIEW */}
      {viewMode === 'list' && (
        <div className="full-view-container">
          <PropertyListView
            properties={displayedProperties}
            loading={loading}
            onPropertySelect={setSelectedProp}
          />
        </div>
      )}

      {/* GRID VIEW */}
      {viewMode === 'grid' && (
        <div className="full-view-container">
          {loading ? (
            <div className="list-loader"><div className="spinner" /><p>Loading properties…</p></div>
          ) : displayedProperties.length === 0 ? (
            <div className="list-empty"><p>No properties found matching your criteria.</p></div>
          ) : (
            <div className="property-list-scroller">
              <div className="list-header-info">
                <span>{displayedProperties.length} properties</span>
                <span className="text-muted">Grid view</span>
              </div>
              <div className="cards-grid-3col">
                {displayedProperties.map(prop => (
                  <PropertyCard
                    key={prop.id}
                    property={prop}
                    onClick={() => setSelectedProp(prop)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
}

export default App;
