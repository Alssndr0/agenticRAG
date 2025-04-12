from typing import Any

GRAPH_FIELD_SEP = "<SEP>"

PROMPTS: dict[str, Any] = {}

PROMPTS["DEFAULT_LANGUAGE"] = "English"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

PROMPTS["DEFAULT_ENTITY_TYPES"] = [
    "organization",
    "person",
    "market",
    "product/service",
    "deals/transactions",
    "event",
    "financial/performance metric",
    "trend",
]

PROMPTS["entity_extraction"] = """---Goal---
Given a text document, identify all the relevant entities and their relationships only in its --Context Summary-- and --Target Text--.
Use {language} as output language.

---Steps---
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity. Capitalize the name.
- entity_type: One of the following types: [{entity_types}]
- entity_description: Description of the entity, as per text provided. Don't make up any information.
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why the source entity and the target entity are related to each other.
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity.
- relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details.
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}

---Example Output For Entities, Relationships and Keywords---
("entity"{tuple_delimiter}"Innovix"{tuple_delimiter}"organization"{tuple_delimiter}"Innovix is a major technology company specializing in cloud solutions, actively expanding through acquisitions."){record_delimiter}
("relationship"{tuple_delimiter}"Innovix"{tuple_delimiter}"BrightAI"{tuple_delimiter}"Innovix acquired BrightAI to expand its AI-driven analytics capabilities."{tuple_delimiter}"acquisition, strategic expansion"{tuple_delimiter}10){record_delimiter}
("content_keywords"{tuple_delimiter}"acquisition, AI analytics, competitive market, strategic expansion, stock performance"){completion_delimiter}

---Real Data---

Entity_types: [{entity_types}]
Text:
{input_text}

Output:"""


PROMPTS[
    "summarize_entity_descriptions"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or more entities and a list of descriptions all related to the same entity or group of entities, please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so to have full context.
Use {language} as output language.

#######
---Data---
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""