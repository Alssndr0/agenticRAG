import configparser
import json
import os
from typing import Any, Dict

from neo4j import GraphDatabase


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
        print(f"❌ Error loading data from {filepath}: {str(e)}")
        raise


def create_neo4j_database(data: Dict[str, Any], clear_database: bool = False):
    """
    Create a Neo4j database from the provided entities and relationships.

    Parameters:
    - data (Dict[str, Any]): Data containing entities and relationships
    - clear_database (bool): Whether to clear the database before importing
    """
    # Read config
    config = configparser.ConfigParser()
    config.read("config.ini", encoding="utf-8")

    uri = os.environ.get("NEO4J_URI", config.get("neo4j", "NEO4J_URI", fallback=None))
    username = os.environ.get(
        "NEO4J_USERNAME", config.get("neo4j", "NEO4J_USERNAME", fallback=None)
    )
    password = os.environ.get(
        "NEO4J_PASSWORD", config.get("neo4j", "NEO4J_PASSWORD", fallback=None)
    )

    if not uri or not username or not password:
        raise ValueError(
            "Neo4j connection details not found. Please check your config.ini file or environment variables."
        )

    # Connect to Neo4j
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        print(f"🔄 Connecting to Neo4j at {uri}")

        with driver.session() as session:
            # Clear the database if requested
            if clear_database:
                print("🧹 Clearing existing database...")
                session.run("MATCH (n) DETACH DELETE n")

            # Create constraints for faster lookups and uniqueness
            print("🔧 Creating constraints...")
            try:
                session.run(
                    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE"
                )
            except Exception as e:
                print(f"⚠️ Could not create constraint (may already exist): {str(e)}")

            # Import entities
            entities = data.get("entities", [])
            print(f"📥 Importing {len(entities)} entities...")

            entity_count = 0
            for entity in entities:
                # Prepare entity properties
                props = {
                    "id": entity["id"],
                    "name": entity["name"],
                    "entity_type": entity["type"],
                }

                # Add all attributes as properties
                for key, value in entity.get("attributes", {}).items():
                    # Convert any non-string values to strings to ensure Neo4j compatibility
                    if isinstance(value, (list, dict)):
                        props[key] = json.dumps(value)
                    else:
                        props[key] = value

                # Create the entity node with appropriate labels
                query = """
                MERGE (e:Entity {id: $id})
                SET e = $props
                SET e:`{entity_type}`
                RETURN e.id
                """.replace("{entity_type}", entity["type"])

                result = session.run(query, id=entity["id"], props=props)
                if result.single():
                    entity_count += 1

                # Print progress
                if entity_count % 50 == 0 or entity_count == len(entities):
                    print(
                        f"   Progress: {entity_count}/{len(entities)} entities imported"
                    )

            # Import relationships
            relationships = data.get("relationships", [])
            print(f"🔗 Importing {len(relationships)} relationships...")

            rel_count = 0
            for rel in relationships:
                # Prepare relationship properties
                props = {}

                # Add all attributes as properties
                for key, value in rel.get("attributes", {}).items():
                    # Convert any non-string values to strings to ensure Neo4j compatibility
                    if isinstance(value, (list, dict)):
                        props[key] = json.dumps(value)
                    else:
                        props[key] = value

                # Add strength property if available
                if "strength" in rel:
                    props["strength"] = rel["strength"]

                # Create the relationship between entities
                query = """
                MATCH (source:Entity {id: $source_id})
                MATCH (target:Entity {id: $target_id})
                MERGE (source)-[r:`{rel_type}`]->(target)
                SET r = $props
                RETURN type(r) as type
                """.replace("{rel_type}", rel["type"])

                result = session.run(
                    query,
                    source_id=rel["source_id"],
                    target_id=rel["target_id"],
                    props=props,
                )
                if result.single():
                    rel_count += 1

                # Print progress
                if rel_count % 50 == 0 or rel_count == len(relationships):
                    print(
                        f"   Progress: {rel_count}/{len(relationships)} relationships imported"
                    )

            print(
                f"✅ Database creation complete: {entity_count} entities and {rel_count} relationships imported"
            )

            # Add context as a special node
            if "context" in data:
                context = data["context"]
                props = {
                    "id": "context",
                    "domain": context.get("domain", ""),
                    "themes": json.dumps(context.get("themes", [])),
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


def main(json_file_path: str = "data/graph/neo4j_data.json", clear_db: bool = False):
    """
    Main function to load data and create Neo4j database.

    Parameters:
    - json_file_path (str): Path to the JSON file with Neo4j data
    - clear_db (bool): Whether to clear the database before importing
    """
    try:
        # Load data from file
        data = load_neo4j_data(json_file_path)

        # Create Neo4j database
        create_neo4j_database(data, clear_database=clear_db)

        print("🎉 Neo4j database creation completed successfully!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
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
        "--clear", action="store_true", help="Clear the database before importing data"
    )

    args = parser.parse_args()

    main(json_file_path=args.input, clear_db=args.clear)
