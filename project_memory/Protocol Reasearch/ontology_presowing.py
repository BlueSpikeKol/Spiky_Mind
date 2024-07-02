from owlready2 import *
import json
import os
import uuid

from project_memory.persistance_access import MemoryStreamAccess

# Initialize the MemoryStreamAccess
memory_stream = MemoryStreamAccess()

# Load the ontology
onto = get_ontology(
    r"C:\Users\philippe\PycharmProjects\Spiky_Mind\project_memory\ontologies\foodon_ontology.rdf").load()

# Specify the root class IRI
root_class_iri = "http://purl.obolibrary.org/obo/FOODON_00001242"
root_class = onto.search(iri=root_class_iri)[0]

# List of annotation properties to extract
annotation_properties = [
    "rdfs:comment",
    "IAO_0000115",  # textual definition
    "has_exact_synonym"
]

# Configuration flags
wipe_database_before_insertion = True  # Set to True to wipe the database before insertion
include_object_properties = False  # Set to True to include object properties in the insertion

# Lists to track data for bulk insertion
class_data = []
property_data = []
processed_properties = set()

# Wipe the database if the flag is set
if wipe_database_before_insertion:
    memory_stream.delete_from_pinecone(delete_all=True)

def get_applicable_object_properties(owl_class):
    applicable_properties = set()
    # Check properties where the domain is this class or any superclass
    for prop in onto.object_properties():
        if any(domain == owl_class or owl_class in domain.ancestors() for domain in prop.domain):
            applicable_properties.add(prop)
    return applicable_properties

def process_class_for_pinecone(owl_class):
    class_name = owl_class.label.first() if owl_class.label else str(owl_class)
    synonyms = getattr(owl_class, "has_exact_synonym", [])
    name_with_synonyms = f"[{class_name}]{'|'.join(synonyms)}"

    annotations = []
    for prop in annotation_properties:
        if hasattr(owl_class, prop):
            annotations.extend([str(value) for value in getattr(owl_class, prop)])

    combined_text = f"{name_with_synonyms}|{'|'.join(annotations)}"
    vector_name = f"{class_name}_simple"
    class_data.append((vector_name, combined_text))

    if include_object_properties:
        object_properties = get_applicable_object_properties(owl_class)
        for obj_prop in object_properties:
            if obj_prop not in processed_properties:
                prop_name = obj_prop.name
                vector_name = f"{prop_name}_vector"
                prop_description = f"Object property {prop_name} relates {obj_prop.domain[0]} to {obj_prop.range[0]}"
                property_data.append((vector_name, prop_description))
                processed_properties.add(obj_prop)

def upsert_to_memory_stream(data_list):
    for vector_name, description in data_list:
        memory_stream.add_to_pinecone(vector_name, description)

def process_ontology(owl_class, total_classes, processed_classes):
    process_class_for_pinecone(owl_class)
    processed_classes += 1
    print(f"Processed {processed_classes} out of {total_classes} classes")
    for subclass in owl_class.subclasses():
        processed_classes = process_ontology(subclass, total_classes, processed_classes)
    return processed_classes

def count_classes(owl_class):
    count = 1  # Include the current class
    for subclass in owl_class.subclasses():
        count += count_classes(subclass)
    return count

total_classes = count_classes(root_class)
print(f"Total classes to process: {total_classes}")
processed_classes = process_ontology(root_class, total_classes, 0)
print("Ontology processing completed. Now updating the database...")

upsert_to_memory_stream(class_data)
if include_object_properties:
    upsert_to_memory_stream(property_data)

print("Vector creation and upserting completed.")
