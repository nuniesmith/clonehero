import requests
from loguru import logger
from functools import lru_cache

def clear_service_cache():
    """Clears the cached service checks."""
    check_service.cache_clear()

@lru_cache(maxsize=4)  # Cache up to 4 service checks
def check_service(service_url, retries=1):
    """Check the health of a service with retry logic."""
    for attempt in range(retries + 1):
        try:
            logger.info(f"Checking service health: {service_url} (Attempt {attempt + 1})")
            resp = requests.get(f"{service_url}/health", timeout=5)
            if resp.status_code == 200:
                logger.info(f"✅ {service_url} is Online")
                return "🟢 Online"
            elif resp.status_code == 404:
                logger.warning(f"🚫 {service_url} returned 404 Not Found")
                return "🔴 404 Not Found"
            elif resp.status_code >= 500:
                logger.warning(f"🔥 {service_url} returned {resp.status_code} (Server Error)")
                return "🔴 Server Error"
            logger.warning(f"⚠️ {service_url} returned status code {resp.status_code}")
            return f"🔴 {resp.status_code} Error"
        except requests.ConnectionError:
            logger.error(f"❌ Connection error: {service_url} is unreachable")
        except requests.Timeout:
            logger.error(f"⏳ Timeout error: {service_url} took too long to respond")
        except requests.RequestException as e:
            logger.error(f"❌ {service_url} check failed: {e}")

        # Retry before failing
        if attempt < retries:
            logger.info(f"Retrying {service_url}...")
    return "🔴 Offline"

def get_service_statuses(api_url, database_url):
    services = {
        "API": api_url,
        "Database": database_url,
    }
    
    statuses = {}
    for name, url in services.items():
        statuses[name] = check_service(url)
    
    logger.info(f"Service statuses: {statuses}")
    return statuses