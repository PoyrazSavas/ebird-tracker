import requests
import json
from pathlib import Path

class EBirdClient:
    BASE_URL = "https://api.ebird.org/v2"
    CACHE_DIR = Path(".cache")
    TAXONOMY_CACHE = CACHE_DIR / "taxonomy.json"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"X-eBirdApiToken": self.api_key}
        self.CACHE_DIR.mkdir(exist_ok=True)
        self._taxonomy_map = None

    def load_taxonomy(self):
        """Tür isimlerini kodlara eşleyen sözlüğü yükler."""
        if self._taxonomy_map:
            return self._taxonomy_map

        if self.TAXONOMY_CACHE.exists():
            try:
                with open(self.TAXONOMY_CACHE, "r", encoding="utf-8") as f:
                    self._taxonomy_map = json.load(f)
                    # Eğer cache eski formatta ise (tek bir değer string ise) temizle
                    first_val = next(iter(self._taxonomy_map.values()))
                    if isinstance(first_val, str):
                        self._taxonomy_map = None
                    else:
                        return self._taxonomy_map
            except Exception:
                pass

        # API'den çek
        url = f"{self.BASE_URL}/ref/taxonomy/ebird?fmt=json"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        tax_map = {}
        for entry in data:
            code = entry["speciesCode"]
            com_name = entry["comName"].lower()
            sci_name = entry["sciName"].lower()
            tax_map[com_name] = {"code": code, "sciName": sci_name}
            tax_map[sci_name] = {"code": code, "sciName": sci_name}
            tax_map[code] = {"code": code, "sciName": sci_name}

        with open(self.TAXONOMY_CACHE, "w", encoding="utf-8") as f:
            json.dump(tax_map, f)
        
        self._taxonomy_map = tax_map
        return tax_map

    def get_species_data(self, query):
        """Türün kodunu ve bilimsel adını döner."""
        tax_map = self.load_taxonomy()
        query = query.strip().lower()
        return tax_map.get(query)

    def get_species_code(self, query):
        """Sadece tür kodunu döner."""
        data = self.get_species_data(query)
        return data["code"] if data else None

    def get_hotspot_details(self, loc_id):
        """Hotspot'un enlem, boylam ve isim bilgilerini çeker."""
        url = f"{self.BASE_URL}/ref/hotspot/info/{loc_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None

    def get_hotspot_observations(self, loc_id, species_code, back=30):
        """Gözlemleri getirir."""
        url = f"{self.BASE_URL}/data/obs/{loc_id}/recent/{species_code}"
        params = {"back": back, "detail": "full"}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_region_observations(self, region_code, species_code, back=30):
        """Bölge gözlemlerini getirir."""
        url = f"{self.BASE_URL}/data/obs/{region_code}/recent/{species_code}"
        params = {"back": back, "detail": "full"}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_hotspot_name(self, loc_id):
        """Hotspot ismini alır."""
        details = self.get_hotspot_details(loc_id)
        if details:
            return details.get("name", loc_id)
        return loc_id

    def get_recent_species_in_region(self, region_or_loc, back=30):
        """Belirli bir bölge veya hotspot'ta son günlerde görülen tüm türlerin listesini döner."""
        url = f"{self.BASE_URL}/data/obs/{region_or_loc}/recent"
        params = {"back": back}
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            obs_list = response.json()
            # Benzersiz türleri (comName) ayıkla
            species = {}
            for obs in obs_list:
                com_name = obs["comName"]
                species[com_name] = {
                    "code": obs["speciesCode"],
                    "sciName": obs["sciName"]
                }
            return species
        return {}
