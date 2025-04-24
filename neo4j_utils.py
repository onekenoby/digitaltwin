# neo4j_utils.py
from neo4j import GraphDatabase
from config import NEO4J_URI, USERNAME, PASSWORD, GDS_GRAPH_NAME

driver = GraphDatabase.driver(NEO4J_URI, auth=(USERNAME, PASSWORD))

def get_country_codes():
    with driver.session() as ses:
        q = """
        MATCH ()-[r:NAMED]->()
        RETURN DISTINCT r.country AS country ORDER BY country
        """
        return [rec["country"] or "Unknown" for rec in ses.run(q)]

def get_tracks_for_country(cc: str):
    with driver.session() as ses:
        q = """
        MATCH (a:OperationPoint)-[r:SECTION]-(b:OperationPoint)
        WHERE a.id STARTS WITH $cc AND b.id STARTS WITH $cc
        RETURN a.id AS a_id, a.geolocation.longitude AS lon1,
               a.geolocation.latitude  AS lat1,
               b.id AS b_id, b.geolocation.longitude AS lon2,
               b.geolocation.latitude  AS lat2,
               r.sectionlength AS distance
        """
        return [dict(rec) for rec in ses.run(q, cc=cc)]

def get_operationpoint_counts(cc: str):
    with driver.session() as ses:
        base = "MATCH (op:OperationPoint) WHERE op.id STARTS WITH $cc"
        def count_label(labels):
            q = f"{base} AND labels(op)[1] IN {labels} RETURN count(op) AS cnt"
            return ses.run(q, cc=cc).single()["cnt"]
        return {
            "Stations": count_label(["Station","SmallStation"]),
            "Switches": count_label(["Switch","Junction"]),
            "StopPoints": count_label(["PassengerStop","PassengerTerminal"])
        }

def get_station_list(cc: str):
    with driver.session() as ses:
        q = """
        MATCH (op:OperationPoint)-[:NAMED]->(pn:OperationPointName)
        WHERE op.id STARTS WITH $cc AND labels(op)[1] IN ['Station','SmallStation']
        RETURN pn.name AS name ORDER BY name
        """
        return [rec["name"] for rec in ses.run(q, cc=cc)]

def get_point_names(label_param: str, limit=5):
    with driver.session() as ses:
        q = """
        MATCH (pn:OperationPointName)
        WHERE toLower(pn.name) CONTAINS toLower($input)
        RETURN DISTINCT pn.name AS value
        ORDER BY size(pn.name) ASC
        LIMIT $lim
        """
        return [rec["value"] for rec in ses.run(q, input=label_param, lim=limit)]

def get_minimal_path(start_name: str, end_name: str, weight: str = "sectionlength"):
    """
    Finds the minimal path between two OperationPoints (by name) using GDS Dijkstra.
    Automatically projects the graph if missing, and catches weight‐property errors.
    """
    from config import GDS_GRAPH_NAME
    with driver.session() as ses:
        # 1) lookup internal node IDs via the name parameter
        rec1 = ses.run(
            "MATCH (s:OperationPoint)-[:NAMED]->(pn) WHERE pn.name=$src RETURN id(s) AS sid",
            src=start_name
        ).single()
        rec2 = ses.run(
            "MATCH (t:OperationPoint)-[:NAMED]->(pn) WHERE pn.name=$dst RETURN id(t) AS tid",
            dst=end_name
        ).single()
        if not rec1 or not rec2:
            return []

        sid, tid = rec1["sid"], rec2["tid"]

        # 2) ensure the GDS graph exists, project if missing
        exists_rec = ses.run(
            "CALL gds.graph.exists($name) YIELD exists RETURN exists",
            name=GDS_GRAPH_NAME
        ).single()
        if not exists_rec or not exists_rec["exists"]:
            ses.run(f"""
                CALL gds.graph.project(
                  '{GDS_GRAPH_NAME}',
                  'OperationPoint',
                  {{ SECTION: {{ type: 'SECTION', properties: '{weight}', orientation: 'UNDIRECTED' }} }}
                )
            """)

        # 3) run Dijkstra, catching any procedure errors
        try:
            path_rec = ses.run(f"""
                CALL gds.shortestPath.dijkstra.stream(
                  '{GDS_GRAPH_NAME}',
                  {{
                    sourceNode: $sid,
                    targetNode: $tid,
                    relationshipWeightProperty: '{weight}'
                  }}
                )
                YIELD nodeIds, costs
                RETURN nodeIds AS nodes, costs AS dist
            """, sid=sid, tid=tid).single()
        except Exception as e:
            # Log to console and return empty so UI can show a warning
            print(f"[neo4j_utils] Dijkstra failed: {e}")
            return []

        if not path_rec:
            return []

        node_ids = path_rec["nodes"]
        total    = path_rec["dist"]

        # 4) rehydrate the path into cities
        cities = []
        for nid in node_ids:
            row = ses.run("""
                MATCH (o:OperationPoint)-[:NAMED]->(pn)
                WHERE id(o) = $nid
                RETURN o.id     AS id,
                       pn.name   AS label,
                       o.geolocation.latitude  AS lat,
                       o.geolocation.longitude AS lon
            """, nid=nid).single()
            cities.append({
                "id":    row["id"],
                "label": row["label"],
                "lat":   row["lat"],
                "lon":   row["lon"]
            })

        return [{"cities": cities, "total_distance": total}]


def get_poi_on_route(src, dst, weight='sectionlength'):
    with driver.session() as ses:
        q = """
        MATCH (start:OperationPoint)-[:NAMED]->(pn1) WHERE pn1.name=$src
        WITH start
        MATCH (end:OperationPoint)-[:NAMED]->(pn2) WHERE pn2.name=$dst
        CALL apoc.algo.dijkstra(start,end,'SECTION','$weight') YIELD path
        WITH nodes(path) AS ns
        UNWIND ns AS n
        MATCH (n)-[:IS_NEAR]->(p:POI)
        RETURN p.city AS City, p.description AS Description, p.linkFoto AS Foto, p.linkWebSite AS Website
        """
        return [dict(rec) for rec in ses.run(q, src=src, dst=dst, weight=weight)]

# at the bottom of neo4j_utils.py, just above close_driver():

def get_all_pois():
    """
    Return list of all POIs with city, description, foto URL and website.
    """
    with driver.session() as ses:
        q = """
        MATCH (p:POI)
        RETURN p.city        AS city,
               p.description AS description,
               p.linkFoto    AS foto,
               p.linkWebSite AS website
        """
        return [ dict(rec) for rec in ses.run(q) ]



def close_driver(): driver.close()