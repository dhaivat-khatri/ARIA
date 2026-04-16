"""
Places Service — uses OpenStreetMap (Overpass API) and Open-Meteo Geocoding.
100% free, global coverage for any village/city, NO API keys required!
"""

import logging
import httpx

logger = logging.getLogger("mcp-server.places")

# Open-Meteo geocoding (no key required)
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
# Overpass API (no key required)
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

async def fetch_places(city: str) -> dict:
    """
    Fetch top tourist attractions and restaurants for any city/village using OSM.
    Pipeline: Geocode with Open-Meteo → Query Overpass API → Parse results.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Step 1: Geocode
            geo_resp = await client.get(
                GEOCODING_URL,
                params={"name": city, "count": 1, "language": "en", "format": "json"}
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            
            results = geo_data.get("results")
            if not results:
                logger.warning("Places geocode failed for: %s", city)
                return {"city": city, "error": "City not found"}
                
            loc = results[0]
            lat = loc["latitude"]
            lon = loc["longitude"]
            city_name = loc.get("name", city)
            country = loc.get("country", "")

            # Step 2: Overpass Query with multiple mirrors for reliability
            # We look for nodes & ways tagged with tourism/amenity/historic near the centre
            radius = 6000 # 6km
            query = f"""
            [out:json][timeout:12];
            (
              node["tourism"~"museum|gallery|viewpoint|attraction|theme_park|zoo"](around:{radius},{lat},{lon});
              way["tourism"~"museum|gallery|viewpoint|attraction|theme_park|zoo"](around:{radius},{lat},{lon});
              node["historic"~"castle|monument|ruins"](around:{radius},{lat},{lon});
              way["historic"~"castle|monument|ruins"](around:{radius},{lat},{lon});
              node["amenity"~"restaurant|cafe"](around:{radius},{lat},{lon});
            );
            out center 20;
            """
            
            op_data = None
            mirrors = [
                "https://overpass-api.de/api/interpreter",
                "https://lz4.overpass-api.de/api/interpreter",
                "https://z.overpass-api.de/api/interpreter",
                "https://overpass.kumi.systems/api/interpreter"
            ]
            
            for mirror in mirrors:
                try:
                    op_resp = await client.post(mirror, data={'data': query})
                    op_resp.raise_for_status()
                    op_data = op_resp.json()
                    logger.info("Overpass API success via %s", mirror)
                    break
                except Exception as e:
                    logger.warning("Overpass mirror %s failed: %s", mirror, e)
                    continue
                    
            if not op_data:
                raise ValueError("All Overpass API mirrors failed to respond.")
            
            # Step 3: Process results and pick a good mix
            elements = op_data.get("elements", [])
            places_list = []
            seen_names = set()
            
            for el in elements:
                tags = el.get("tags", {})
                name = tags.get("name") or tags.get("name:en")
                if not name or name in seen_names:
                    continue
                    
                tourism = tags.get("tourism")
                amenity = tags.get("amenity")
                historic = tags.get("historic")
                
                cat = "Attraction"
                if amenity == "restaurant": cat = "Restaurant"
                elif amenity == "cafe": cat = "Cafe"
                elif tourism == "museum": cat = "Museum"
                elif tourism == "viewpoint": cat = "Viewpoint"
                elif historic == "castle": cat = "Castle"
                elif historic: cat = "Historic Site"
                elif tourism == "gallery": cat = "Art Gallery"
                
                # Get web link if available
                website = tags.get("website") or tags.get("wikipedia") or ""
                
                places_list.append({
                    "name": name,
                    "category": cat,
                    "address": tags.get("addr:street", "Local area"),
                    "description": website if website else f"A notable {cat.lower()} in {city_name}.",
                    # sorting slightly by presence of a website/amenity
                    "_score": 1 if website else 0
                })
                seen_names.add(name)

            # Sort by score so cooler places with websites appear slightly higher, take top 8
            places_list.sort(key=lambda x: x["_score"], reverse=True)
            places_list = places_list[:8]
            
            for p in places_list:
                del p["_score"]

            logger.info("Places fetched for city=%s, count=%d via OSM", city_name, len(places_list))
            return {"city": city_name, "country": country, "places": places_list}
            
    except Exception as exc:
        logger.error("Places service error for %s: %s", city, exc)
        return {"city": city, "error": f"Failed to fetch places: {exc}"}
