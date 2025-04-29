import json
from typing import Any, Dict
import os
import sys
# allow module imports when run as script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from neo4j import GraphDatabase
from utils.load_env import get_env_vars


def load_neo4j_data(filepath: str) -> Dict[str, Any]:
    """
    Load the extracted entity and relationship data from JSON file.

    Parameters:
    - filepath (str): Path to the JSON file containing Neo4j data

    Returns:
    - Dict[str, Any]: The loaded data with entities and relationships
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"✅ Successfully loaded data from {filepath}")
        print(f"   - Total entities: {len(data.get('entities', []))}")
        print(f"   - Total relationships: {len(data.get('relationships', []))}")
        return data
    except Exception as e:
        print(f"❌ Error loading data from {filepath}: {e}")
        raise


def create_neo4j_database(data: Dict[str, Any], clear_database: bool = False):
    """
    Create a Neo4j database from the provided entities and relationships,
    and automatically create a fulltext index for Entity.name.
    """
    # Load connection info and index name from .env
    env      = get_env_vars()
    uri      = env.get("NEO4J_URI")
    username = env.get("NEO4J_USERNAME")
    password = env.get("NEO4J_PASSWORD")
    index_name = env.get("NEO4J_FULLTEXT_INDEX_NAME", "entityNames")

    if not (uri and username and password):
        raise ValueError(
            "Missing Neo4j credentials in environment. "
            "Please set NEO4J_URI, NEO4J_USERNAME and NEO4J_PASSWORD in your .env."
        )

    # Connect to Neo4j
    driver = GraphDatabase.driver(uri, auth=(username, password))
    print(f"🔄 Connecting to Neo4j at {uri}")

    with driver.session() as session:
        # 1) Optionally clear the DB
        if clear_database:
            print("🧹 Clearing existing database...")
            session.run("MATCH (n) DETACH DELETE n")

        # 2) Create uniqueness constraint for Entity.id
        print("🔧 Creating constraints...")
        try:
            session.run(
                "CREATE CONSTRAINT entity_id IF NOT EXISTS "
                "FOR (n:Entity) REQUIRE n.id IS UNIQUE"
            )
        except Exception as e:
            print(f"⚠️ Could not create constraint (may already exist): {e}")

        # 3) Import entities
        entities = data.get("entities", [])
        print(f"📥 Importing {len(entities)} entities...")
        for i, entity in enumerate(entities, start=1):
            props = {
                "id":          entity["id"],
                "name":        entity["name"],
                "entity_type": entity["type"],
            }
            for k, v in entity.get("attributes", {}).items():
                props[k] = json.dumps(v) if isinstance(v, (list, dict)) else v

            cypher = f"""
            MERGE (e:Entity {{id: $id}})
            SET e = $props
            SET e:`{entity['type']}`
            """
            session.run(cypher, id=entity["id"], props=props)
            if i % 50 == 0 or i == len(entities):
                print(f"   Progress: {i}/{len(entities)} entities imported")

        # 4) Import relationships
        relationships = data.get("relationships", [])
        print(f"🔗 Importing {len(relationships)} relationships...")
        for i, rel in enumerate(relationships, start=1):
            props = {}
            for k, v in rel.get("attributes", {}).items():
                props[k] = json.dumps(v) if isinstance(v, (list, dict)) else v
            if "strength" in rel:
                props["strength"] = rel["strength"]

            cypher = f"""
            MATCH (src:Entity {{id: $source}})
            MATCH (tgt:Entity {{id: $target}})
            MERGE (src)-[r:`{rel['type']}`]->(tgt)
            SET r = $props
            """
            session.run(
                cypher,
                source=rel["source_id"],
                target=rel["target_id"],
                props=props,
            )
            if i % 50 == 0 or i == len(relationships):
                print(f"   Progress: {i}/{len(relationships)} relationships imported")

        print(f"✅ Database creation complete: {len(entities)} entities "
              f"and {len(relationships)} relationships imported")

        # 5) Add context node if present
        if "context" in data:
            ctx = data["context"]
            props = {
                "id":     "context",
                "domain": ctx.get("domain", ""),
                "themes": json.dumps(ctx.get("themes", [])),
            }
            session.run(
                """
                MERGE (c:Context {id: $id})
                SET c = $props
                """,
                id="context",
                props=props,
            )
            print("✅ Context information added")

        # 6) Create (or ensure) fulltext index on Entity.name
        print(f"🔍 Creating fulltext index '{index_name}' on :Entity(name)...")
        try:
            session.run(
                f"CREATE FULLTEXT INDEX {index_name} "
                f"FOR (e:Entity) ON EACH [e.name]"
            )
            print(f"✅ Fulltext index '{index_name}' created.")
        except Exception as e:
            # will error if it already exists or if fulltext isn't supported — safe to ignore
            print(f"⚠️ Fulltext index creation skipped: {e}")

    driver.close()


def main(json_file_path: str = "data/graph/neo4j_data.json", clear_db: bool = False):
    """
    Main function to load data and create Neo4j database.

    Parameters:
    - json_file_path (str): Path to the JSON file with Neo4j data
    - clear_db (bool): Whether to clear the database before importing
    """
    try:
        data = load_neo4j_data(json_file_path)
        create_neo4j_database(data, clear_database=clear_db)
        print("🎉 Neo4j database creation completed successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create Neo4j database from extracted data"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/graph/neo4j_data.json",
        help="Path to the input JSON file",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the database before importing data",
    )

    args = parser.parse_args()
    main(json_file_path=args.input, clear_db=args.clear)
