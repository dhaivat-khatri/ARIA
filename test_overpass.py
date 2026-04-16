import requests

city = "Grindelwald"
# 1. Geocode with Open-Meteo
geo_resp = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1})
if geo_resp.status_code == 200 and geo_resp.json().get("results"):
    lat = geo_resp.json()["results"][0]["latitude"]
    lon = geo_resp.json()["results"][0]["longitude"]
    print(f"Geocoded to {lat}, {lon}")
    
    # 2. Overpass query for tourism within 5000m
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:10];
    (
      node["tourism"~"museum|viewpoint|gallery|attraction"](around:5000,{lat},{lon});
      node["historic"](around:5000,{lat},{lon});
      node["amenity"~"restaurant|cafe"](around:2000,{lat},{lon});
    );
    out center 15;
    """
    resp = requests.post(overpass_url, data={'data': overpass_query})
    print(resp.status_code)
    try:
        data = resp.json()
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name")
            if name:
                print(name, "-", tags.get("tourism") or tags.get("amenity") or tags.get("historic"))
    except:
        print(resp.text[:500])
