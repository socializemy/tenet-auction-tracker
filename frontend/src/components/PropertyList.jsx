import React from 'react';
import PropertyCard from './PropertyCard';

const PropertyList = ({ properties, loading, onPropertySelect, selectedProperty }) => {
    if (loading) {
        return (
            <div className="list-loader">
                <div className="spinner"></div>
                <p>Loading properties...</p>
            </div>
        );
    }

    if (properties.length === 0) {
        return (
            <div className="list-empty">
                <p>No properties found matching your criteria.</p>
            </div>
        );
    }

    return (
        <div className="property-list-scroller">
            <div className="list-header-info">
                <span>{properties.length} homes</span>
                <span className="text-muted">Sorted by Auction Date</span>
            </div>
            <div className="cards-grid">
                {properties.map(prop => (
                    <PropertyCard
                        key={prop.id}
                        property={prop}
                        onClick={() => onPropertySelect(prop)}
                    />
                ))}
            </div>
        </div>
    );
};

export default PropertyList;
