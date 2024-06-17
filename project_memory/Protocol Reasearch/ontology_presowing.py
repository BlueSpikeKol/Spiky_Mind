"""
in order to enable the next step, we will load an already made ontology and sow inside of it metadata that will be
vectorized for the listener bot to be able to match it with the questions of the explorer bot.
"""

"""
the listener bot will be more complex. He will have to look at the question from the explorer bot
(Natural Language Query or NLQ) and transform it into a SPARQL query that is applicable to the ontology
(Accurate Sparql Query or ASQ). to do this he will have to:
parse the NLQ(the goal is to use clusters to separate different subjects, testing will be required) vectorize the 
relevent clusters of information into multiple NLQs, vectorize the parsed NLQs, compare them to the ontology using
vector comparison, find a match, either directly or with a traversal algorithm and finally transform the NLQS with the 
information matched to transform them into ASQs.
"""
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


def class_to_dict(owl_class):
    class_dict = {
        "label": owl_class.label.first() if owl_class.label else str(owl_class),
        "subclasses": [],
        "annotations": {}
    }

    # Extract annotations
    for prop in annotation_properties:
        if hasattr(owl_class, prop) and getattr(owl_class, prop):
            class_dict["annotations"][prop] = [str(value) for value in getattr(owl_class, prop)]

    # Recursively process subclasses
    for subclass in owl_class.subclasses():
        class_dict["subclasses"].append(class_to_dict(subclass))

    return class_dict


def process_class_for_pinecone(owl_class):
    # Collect the label and synonyms
    class_name = owl_class.label.first() if owl_class.label else str(owl_class)
    synonyms = owl_class.has_exact_synonym if hasattr(owl_class, "has_exact_synonym") else []
    name_with_synonyms = f"[{class_name}]\{'|'.join(synonyms)}"

    # Collect the annotations
    annotations = []
    for prop in annotation_properties:
        if hasattr(owl_class, prop) and getattr(owl_class, prop):
            annotations.append('|'.join([str(value) for value in getattr(owl_class, prop)]))

    # Combine the name and annotations into a single string
    combined_text = f"{name_with_synonyms}|{'|'.join(annotations)}"

    # Create the vector name
    vector_name = f"{class_name}_simple"

    # Add to Pinecone using the memory stream
    memory_stream.add_to_pinecone(vector_name, combined_text)


# Process the root class and its subclasses recursively
def process_ontology(owl_class):
    process_class_for_pinecone(owl_class)
    for subclass in owl_class.subclasses():
        process_ontology(subclass)


# Start processing from the root class
process_ontology(root_class)

print("Ontology processing and vector creation completed.")