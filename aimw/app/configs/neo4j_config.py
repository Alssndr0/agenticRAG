from functools import lru_cache

from app.configs.base_config import BaseConfig, get_base_config


class Neo4jConfig(BaseConfig):
    model_config = {"env_file": get_base_config().NEO4J_CONFIG_FILE}


class Neo4jSettings(Neo4jConfig):
    """
    Defines the configuration settings for file paths used in the application.
    Attributes:
        INPUT_PATH (Path): The directory path for input resources.
    """

    NEO4J_URI: str = "neo4j+s://f606a67d.databases.neo4j.io"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "Sl6dxPP83b58ozff6J2ZHN0sq1JDH1--S3avYSviz7Y"
    NEO4J_FULLTEXT_INDEX_NAME: str = "entityNames"


@lru_cache()
def get_path_settings() -> Neo4jSettings:
    return Neo4jSettings()
