const fs = require('fs');

let appJsx = fs.readFileSync('src/App.jsx', 'utf8');
appJsx = appJsx.replace(
  `            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
              <polyline points="9 22 9 12 15 12 15 22"></polyline>
            </svg>`,
  `            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="12" y1="8" x2="12" y2="16"></line>
              <line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>`
);
// Make the logo container have sharp corners to match Tenetcap
appJsx = appJsx.replace("borderRadius: '8px'", "borderRadius: '0px'");
// Fix App header title size
appJsx = appJsx.replace("fontSize: '2.5rem', marginBottom: '0.5rem'", "fontSize: '4rem', marginBottom: '1rem', letterSpacing: '0.05em'");

fs.writeFileSync('src/App.jsx', appJsx);

let gridJsx = fs.readFileSync('src/components/PropertyGrid.jsx', 'utf8');
// Fix select dropdown styling in property grid
gridJsx = gridJsx.replace(
  "borderRadius: '6px',", 
  "borderRadius: '0px', padding: '0.4rem 0.8rem',"
);
fs.writeFileSync('src/components/PropertyGrid.jsx', gridJsx);
