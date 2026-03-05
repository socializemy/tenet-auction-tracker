import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { fetchProperties, triggerScrape, fetchScrapeStatus, exportCsv } from './utils/api';
import { Search } from 'lucide-react';
import PropertyList from './components/PropertyList';
import PropertyMap from './components/PropertyMap';
import PropertyModal from './components/PropertyModal';

function App() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [selectedProp, setSelectedProp] = useState(null);
  const [scrapeMsg, setScrapeMsg] = useState('');

  const [filters, setFilters] = useState({
    county: '',
    sort_by: 'auction_date',
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
        setScrapeMsg('Scraping in progress (loading live data)...');
      }
    }).catch(e => console.error(e));
  }, []);

  // Poll scrape status continuously to sync across tabs/refreshes and dynamically load enriched properties
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const status = await fetchScrapeStatus();

        // If it's running, dynamically pull new properties so the user sees real-time Zillow images loading
        if (status.running) {
          loadProperties(true);
        }

        if (status.running && !scraping) {
          setScraping(true);
          setScrapeMsg('Scraping in progress (loading live data)...');
        } else if (!status.running && scraping) {
          setScraping(false);
          setScrapeMsg(`Done! ${status.total_scraped ?? 0} scraped`);
          loadProperties(true);
          setTimeout(() => setScrapeMsg(''), 6000);
        }
      } catch (e) { /* ignore */ }
    }, 4000);
    return () => clearInterval(interval);
  }, [scraping, loadProperties]);

  const handleRefresh = async () => {
    setScraping(true);
    setScrapeMsg('Scraping all sources — this takes 2–5 minutes...');
    try {
      await triggerScrape();
    } catch (e) {
      setScraping(false);
      setScrapeMsg('Scrape trigger failed. Is the backend running?');
      setTimeout(() => setScrapeMsg(''), 5000);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(f => ({ ...f, [key]: value }));
  };

  const filteredProperties = useMemo(() => {
    if (!searchTerm.trim()) return properties;

    const lowerTerm = searchTerm.toLowerCase().trim();
    return properties.filter(p => {
      const matchAddress = p.address?.toLowerCase().includes(lowerTerm);
      const matchCity = p.city?.toLowerCase().includes(lowerTerm);
      const matchZip = p.zip_code?.toLowerCase().includes(lowerTerm);
      const matchTsn = p.tsn?.toLowerCase().includes(lowerTerm);
      return matchAddress || matchCity || matchZip || matchTsn;
    });
  }, [properties, searchTerm]);

  return (
    <div className="app-container-split">
      {selectedProp && (
        <PropertyModal
          property={selectedProp}
          onClose={() => setSelectedProp(null)}
        />
      )}

      <header className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', zIndex: 100 }}>
        <div className="header-logo">
          <div style={{
            width: '36px', height: '36px',
            background: 'var(--accent-primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
          </div>
          <span>
            TENET <span className="text-gradient">AUCTION </span>TRACKER
          </span>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end', maxWidth: '60%' }}>
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

      <main className="split-view-container">
        <div className="list-pane">
          <div className="filter-bar">
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
            <select value={filters.sort_by} onChange={e => handleFilterChange('sort_by', e.target.value)} style={{ marginLeft: 'auto' }}>
              <option value="auction_date">Sort: Date</option>
              <option value="starting_bid">Sort: Lowest Bid</option>
              <option value="estimated_value">Sort: Highest Value</option>
            </select>
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

          {scrapeMsg && (
            <div style={{
              padding: '0.6rem 1.5rem',
              background: scraping ? 'rgba(37, 99, 235, 0.06)' : 'rgba(5, 150, 105, 0.06)',
              borderBottom: '1px solid var(--border-color)',
              fontSize: '0.8rem',
              color: scraping ? '#2563EB' : '#059669',
              fontWeight: 500
            }}>
              {scrapeMsg}
            </div>
          )}

          <PropertyList
            properties={filteredProperties}
            loading={loading}
            selectedProperty={selectedProp}
            onPropertySelect={setSelectedProp}
          />
        </div>

        <div className="map-pane">
          {/* The map stays alive even during loading to prevent jank */}
          <PropertyMap
            properties={filteredProperties}
            selectedProperty={selectedProp}
            onPropertySelect={setSelectedProp}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
