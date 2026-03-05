import re

texts = [
    "This 1466 square feet Single Family home has 3 bedrooms and 2 bathrooms. It is located at 1117 S Aspen Pl, Airway Heights, WA.",
    "View 34 photos for 1117 S Aspen Pl, Airway Heights, WA 99001, a 4 bed, 2 bath, 1,466 Sq. Ft. single family home built in 2004 that was last sold on 09/13/2004.",
    "1117 S Aspen Pl, Airway Heights, WA 99001 is a 1,466 sqft, 3 bed, 2 bath home.",
    "1117 South Aspen Place, Airway Heights, WA 99001 is a single family home listed for sale at $349,900. This is a 4-bed, 2-bath, 1,466 sqft property."
]

for combined in texts:
    print(f"--- {combined} ---")
    
    beds = re.findall(r'(\d+(?:\.\d+)?)\s*(?:bed|beds|bd|-bed)', combined, re.IGNORECASE)
    print(f"Beds: {beds}")
    
    baths = re.findall(r'(\d+(?:\.\d+)?)\s*(?:bath|baths|ba|-bath)', combined, re.IGNORECASE)
    print(f"Baths: {baths}")
    
    sqft = re.findall(r'([0-9,]+)\s*(?:sqft|sq\.?\s*ft\.?|square feet)', combined, re.IGNORECASE)
    print(f"Sqft: {sqft}")
