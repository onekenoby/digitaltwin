# neo4j_utils.py
from neo4j import GraphDatabase
from config import NEO4J_URI, USERNAME, PASSWORD

# Single, pooled driver
driver = GraphDatabase.driver(
    NEO4J_URI, auth=(USERNAME, PASSWORD),
    max_connection_pool_size=20,
    connection_timeout=30
)

def get_country_codes():
    """
    Return sorted list of distinct country codes
    from the NAMED relationship.
    """
    with driver.session() as ses:
        result = ses.run(
            """
            MATCH ()-[r:NAMED]->()
            RETURN DISTINCT r.country AS country
            ORDER BY r.country
            """
        )
        return [rec["country"] or "Unknown" for rec in result]

def get_tracks_for_country(country_code: str):
    """
    Return list of track segments (a→b) for OperationPoints
    whose 'id' STARTS WITH the given country_code.
    Each record includes geo coords and distance.
    """
    q = """
    MATCH (a:OperationPoint)-[r:SECTION]-(b:OperationPoint)
    WHERE a.id STARTS WITH $cc AND b.id STARTS WITH $cc
    RETURN
      a.id   AS a_id,
      a.geolocation.longitude AS lon1,
      a.geolocation.latitude  AS lat1,
      b.id   AS b_id,
      b.geolocation.longitude AS lon2,
      b.geolocation.latitude  AS lat2,
      r.sectionlength        AS distance
    """
    segments = []
    with driver.session() as ses:
        for rec in ses.run(q, cc=country_code):
            segments.append({
                "a_id":    rec["a_id"],
                "lon1":    rec["lon1"],
                "lat1":    rec["lat1"],
                "b_id":    rec["b_id"],
                "lon2":    rec["lon2"],
                "lat2":    rec["lat2"],
                "distance": rec["distance"]
            })
    return segments

def close_driver():
    driver.close()
