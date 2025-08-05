def delete_all_objects(client: weaviate.Client, classes: list):
    for class_name in classes:
        while True:
            results = client.query.get(class_name, ["_additional { id }"]).with_limit(100).do()
            objects = results.get("data", {}).get("Get", {}).get(class_name, [])
            if not objects:
                break
            for obj in objects:
                obj_id = obj["_additional"]["id"]
                client.data_object.delete(obj_id, class_name)
delete_all_objects(client, ["Chunk", "Document"])
