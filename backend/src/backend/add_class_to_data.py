import weaviate
from weaviate.classes.config import Property, ReferenceProperty, DataType, Configure

def setup_schema(client: weaviate.WeaviateClient):
    
  
    if not client.collections.exists("Document"):
        print("Création de la collection 'Document'...")
        client.collections.create(
            name="Document",
            description="Métadonnées des documents",
            vector_config=Configure.Vectors.self_provided(),
            properties=[
                Property(name="title",         data_type=DataType.TEXT),
                Property(name="document_type", data_type=DataType.TEXT),
                Property(name="summary",       data_type=DataType.TEXT),
                Property(name="keywords",      data_type=DataType.TEXT_ARRAY),
                Property(name="client",        data_type=DataType.TEXT),
                Property(name="sector",        data_type=DataType.TEXT_ARRAY),  
                Property(name="attachments",   data_type=DataType.TEXT),
                Property(name="budget",        data_type=DataType.NUMBER),
                Property(name="date",          data_type=DataType.TEXT),
                Property(name="docid",         data_type=DataType.TEXT),
                Property(name="userid",        data_type=DataType.TEXT),
            ]
        )
        print("Collection 'Document' créée. ")
    else:
        print("Collection 'Document' déjà existante.")
    

    if not client.collections.exists("Chunk"):
        print("Création de la collection 'Chunk'...")
        client.collections.create(
            name="Chunk",
            description="Contenu découpé (chunk) lié à un document",
            vector_config=Configure.Vectors.self_provided(),
            properties=[
                Property(name="indexchunk", data_type=DataType.NUMBER),
                Property(name="contenu",    data_type=DataType.TEXT),
                Property(name="page",       data_type=DataType.NUMBER),
            ],
            references=[
                ReferenceProperty(name="ofDocument", target_collection="Document")
            ]
        )
        print("Collection 'Chunk' créée. ")
    else:
        print("Collection 'Chunk' déjà existante.")