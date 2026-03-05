import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Home } from 'lucide-react';

// Fix for default marker icon in leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const getMarkerIcon = (status) => {
    let dotColor = '#ef4444'; // Red (Active)
    const s = (status || '').toLowerCase();

    if (s.includes('cancel')) {
        dotColor = '#9ca3af'; // Gray (so it's visible on the white pin)
    } else if (s.includes('postpone')) {
        dotColor = '#f97316'; // Orange
    }

    const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="-4 -4 32 32" width="36" height="36">
        <defs>
            <filter id="pin-shadow" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="0.3"/>
            </filter>
        </defs>
        <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" fill="#ffffff" filter="url(#pin-shadow)" stroke="#e5e7eb" stroke-width="0.5"/>
        <circle cx="12" cy="10" r="4" fill="${dotColor}"/>
    </svg>`;

    return L.divIcon({
        className: "custom-svg-pin",
        html: svg,
        iconSize: [36, 36],
        iconAnchor: [18, 29],
        popupAnchor: [0, -29]
    });
};

// A custom map controller to fly to a selected property
const MapController = ({ center }) => {
    const map = useMap();
    useEffect(() => {
        // Disabled per user request to not auto-zoom on pin click
        // if (center && center !== DEFAULT_CENTER) {
        //     map.flyTo(center, 14, { duration: 1.5 });
        // }
    }, [center, map]);
    return null;
};

// Spokane center
const DEFAULT_CENTER = [47.6588, -117.4260];

const PropertyMap = ({ properties, selectedProperty, onPropertySelect }) => {
    const [markers, setMarkers] = useState([]);

    // MVP: In a real app, properties would have `lat` and `lng` from the backend.
    // Here we'll just mock random scatter around Spokane for visual demo if missing.
    // Alternatively, we could geocode, but let's just use mock data to ensure it renders immediately.
    useEffect(() => {
        const generated = properties.map((prop, idx) => {
            // Pseudo-random spread based on index to mock pins
            const latOffset = (Math.sin(idx * 13.5) * 0.15);
            const lngOffset = (Math.cos(idx * 17.2) * 0.2);
            return {
                ...prop,
                lat: prop.lat || (DEFAULT_CENTER[0] + latOffset),
                lng: prop.lng || (DEFAULT_CENTER[1] + lngOffset)
            };
        });
        setMarkers(generated);
    }, [properties]);

    // Determine current center
    const activeCenter = selectedProperty
        ? markers.find(m => m.id === selectedProperty.id)
            ? [markers.find(m => m.id === selectedProperty.id).lat, markers.find(m => m.id === selectedProperty.id).lng]
            : DEFAULT_CENTER
        : DEFAULT_CENTER;

    return (
        <MapContainer center={DEFAULT_CENTER} zoom={11} style={{ height: '100%', width: '100%', zIndex: 1 }}>
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            />
            <MapController center={activeCenter} />

            {markers.map((marker) => (
                <Marker
                    key={marker.id}
                    position={[marker.lat, marker.lng]}
                    icon={getMarkerIcon(marker.status)}
                    eventHandlers={{
                        mouseover: (e) => e.target.openPopup(),
                        click: (e) => {
                            e.target.openPopup();
                            if (onPropertySelect) onPropertySelect(marker);
                        },
                    }}
                >
                    <Popup className="custom-popup">
                        <div style={{ padding: '4px', minWidth: '180px' }}>
                            <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '4px' }}>
                                {marker.starting_bid > 0 ? `$${marker.starting_bid.toLocaleString()}` : (marker.estimated_value ? `$${marker.estimated_value.toLocaleString()}` : "TBD")}
                            </div>
                            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                                {marker.address}
                            </div>
                            <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                                <strong>Est. Value:</strong> {marker.estimated_value ? `$${marker.estimated_value.toLocaleString()}` : "NA"}
                            </div>
                            <button
                                style={{ width: '100%', padding: '4px 8px', background: 'var(--accent-primary)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                                onClick={(e) => { e.stopPropagation(); onPropertySelect && onPropertySelect(marker); }}
                            >
                                View Details
                            </button>
                        </div>
                    </Popup>
                </Marker>
            ))}
        </MapContainer>
    );
};

export default PropertyMap;
