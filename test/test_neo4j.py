import configparser
import os

from neo4j import GraphDatabase

from utils import get_device


def create_nodes_with_edge():
    """
    Create two nodes and an edge between them in Neo4j using the sync driver.
    """

    # Read config
    config = configparser.ConfigParser()
    config.read("config.ini", "utf-8")

    uri = os.environ.get("NEO4J_URI", config.get("neo4j", "NEO4J_URI", fallback=None))
    username = os.environ.get(
        "NEO4J_USERNAME", config.get("neo4j", "NEO4J_USERNAME", fallback=None)
    )
    password = os.environ.get(
        "NEO4J_PASSWORD", config.get("neo4j", "NEO4J_PASSWORD", fallback=None)
    )

    # Define the two nodes
    node_a = {
        "entity_id": "test_node_1",
        "entity_type": "Person",
        "name": "John Doe",
        "age": "30",
        "device": get_device(),
    }

    node_b = {
        "entity_id": "test_node_2",
        "entity_type": "Company",
        "name": "Neo4j Inc.",
        "founded": "2007",
    }

    # Define edge properties
    edge_properties = {
        "relationship": "EMPLOYED_AT",
        "since": "2021",
        "source_id": node_a["entity_id"],
        "target_id": node_b["entity_id"],
    }

    # Connect and execute Cypher queries
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        print(f"Connecting to Neo4j at {uri}")

        with driver.session() as session:
            # Cypher query to merge nodes and edge
            query = """
            MERGE (a:base {entity_id: $node_a.entity_id})
            SET a += $node_a
            SET a:`{node_a_type}`

            MERGE (b:base {entity_id: $node_b.entity_id})
            SET b += $node_b
            SET b:`{node_b_type}`

            MERGE (a)-[r:EMPLOYED_AT]->(b)
            SET r += $edge_properties

            RETURN a.entity_id AS source, type(r) AS relation, b.entity_id AS target
            """.replace("{node_a_type}", node_a["entity_type"]).replace(
                "{node_b_type}", node_b["entity_type"]
            )

            # Run query
            result = session.run(
                query, node_a=node_a, node_b=node_b, edge_properties=edge_properties
            )
            record = result.single()

            if record:
                print(
                    f"Created edge: {record['source']} -[{record['relation']}]-> {record['target']}"
                )
            else:
                print("Failed to create nodes or edge.")


if __name__ == "__main__":
    create_nodes_with_edge()

if __name__ == "__main__":
    create_nodes_with_edge()
