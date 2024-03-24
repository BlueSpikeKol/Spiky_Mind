import requests
from requests.auth import HTTPDigestAuth
import re
import os
from owlready2 import get_ontology, Thing
# Assuming GPTManager and related classes are defined elsewhere in your project
from utils.openai_api.gpt_calling import GPTManager, GPTAgent
from utils.openai_api.models import ModelType

# Initialize the GPT manager
gpt_manager = GPTManager()


def download_ontology_from_graph(sparql_endpoint, graph_uri, save_path, auth=None):
    headers = {
        "Accept": "application/rdf+xml",  # Request RDF/XML response
        "Content-Type": "application/sparql-query"  # Indicate SPARQL query in the request body
    }
    # SPARQL CONSTRUCT query to retrieve all triples from the specified graph
    sparql_query = f"""
    CONSTRUCT {{
        ?s ?p ?o .
    }} WHERE {{
        GRAPH <{graph_uri}> {{
            ?s ?p ?o .
        }}
    }}
    """
    try:
        response = requests.post(sparql_endpoint, data=sparql_query, headers=headers, auth=auth)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"Ontology data successfully downloaded and saved to {save_path}.")
        else:
            print(f"Failed to download ontology data: {response.status_code} - {response.reason}")
    except Exception as e:
        print(f"Error downloading ontology data: {e}")


def upload_ontology_to_virtuoso(file_path, graph_uri, endpoint, auth):
    headers = {"Content-Type": "application/rdf+xml"}
    print(f"Reading ontology from file: {file_path}")
    with open(file_path, 'rb') as file:
        file_contents = file.read()

    print(f"Uploading ontology to Virtuoso at endpoint: {endpoint}")
    print(f"Graph URI: {graph_uri}")
    print(f"Using auth: {auth.username}")  # Be careful not to print passwords or sensitive information

    response = requests.put(f"{endpoint}?graph-uri={graph_uri}", data=file_contents, headers=headers, auth=auth)

    if response.status_code in [200, 201]:
        print("Ontology uploaded successfully.")
    else:
        print(f"Failed to upload ontology: {response.status_code} - {response.reason}")
        print(f"Response body: {response.text}")  # This may contain more details on the error


def construct_expected_elements_dict(code_to_exec):
    """
    Extracts expected elements from the agent-generated code using regular expressions.
    This version tries to capture all occurrences of each element type.
    """
    expected_elements = {
        'class': re.findall(r"class (\w+)\(", code_to_exec),
        'individual': re.findall(r"(\w+) = (\w+)\(", code_to_exec),
        'object_property': re.findall(r"class (\w+)\(ObjectProperty\):", code_to_exec),
        'data_property': re.findall(r"class (\w+)\(DataProperty\):", code_to_exec),
        'annotation_property': re.findall(r"class (\w+)\(AnnotationProperty\):", code_to_exec),
        # Datatypes are typically not defined with class syntax in Owlready2, so this remains empty
        'datatype': [],
        # Additional property types
        'functional_property': re.findall(r"class (\w+)\(FunctionalProperty\):", code_to_exec),
        'inverse_functional_property': re.findall(r"class (\w+)\(InverseFunctionalProperty\):", code_to_exec),
        'transitive_property': re.findall(r"class (\w+)\(TransitiveProperty\):", code_to_exec),
        'symmetric_property': re.findall(r"class (\w+)\(SymmetricProperty\):", code_to_exec),
        'asymmetric_property': re.findall(r"class (\w+)\(AsymmetricProperty\):", code_to_exec),
    }
    return expected_elements


def verify_ontology_modifications(onto, expected_elements):
    """
    Verifies various modifications made to an ontology.

    :param onto: The ontology to verify.
    :param expected_elements: A dictionary with keys as element types (e.g., 'class', 'individual') and values as lists of names to check.
    """
    # Verify classes
    for cls_name in expected_elements.get('class', []):
        if not onto.search(iri="*" + cls_name):
            print(f"Error: Class '{cls_name}' not found in the ontology.")
        else:
            print(f"Class '{cls_name}' successfully verified.")

    # Verify individuals
    for ind_name in expected_elements.get('individual', []):
        if not onto.search(iri="*" + ind_name):
            print(f"Error: Individual '{ind_name}' not found in the ontology.")
        else:
            print(f"Individual '{ind_name}' successfully verified.")

    # Verify object properties
    for prop_name in expected_elements.get('object_property', []):
        if not onto.search(iri="*" + prop_name):
            print(f"Error: Object property '{prop_name}' not found in the ontology.")
        else:
            print(f"Object property '{prop_name}' successfully verified.")

    # Verify data properties
    for prop_name in expected_elements.get('data_property', []):
        if not onto.search(iri="*" + prop_name):
            print(f"Error: Data property '{prop_name}' not found in the ontology.")
        else:
            print(f"Data property '{prop_name}' successfully verified.")

    # Add more verification for other types like annotation properties
    for prop_name in expected_elements.get('annotation_property', []):
        if not onto.search(iri="*" + prop_name):
            print(f"Error: Annotation property '{prop_name}' not found in the ontology.")
        else:
            print(f"Annotation property '{prop_name}' successfully verified.")
    for prop_name in expected_elements.get('datatype', []):
        if not onto.search(iri="*" + prop_name):
            print(f"Error: Datatype '{prop_name}' not found in the ontology.")
        else:
            print(f"Datatype '{prop_name}' successfully verified.")


def use_agent_to_modify_onto(onto, modification_input=None, save_path=None):
    if modification_input:
        prompt = f"""listen to the user query and create python code to modify the ontology using owlready2 library.
    Example:
    Query: "Add a class named 'MyClass' as a subclass of Thing."
    Code:
    ```
    with onto:
        class MyClass(Thing):
            pass
    ```"""
        agent = gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=modification_input,
                                         system_prompt=prompt,
                                         temperature=0.1, max_tokens=500)
        agent.run_agent()
        code_response = agent.get_text()
        start = code_response.find("```") + 3
        end = code_response.rfind("```")
        code_to_exec = code_response[start:end].strip()

        # Prepare the namespace for exec, explicitly including 'onto' and necessary Owlready2 classes
        namespace = {
            'onto': onto,
            'Thing': Thing,  # Include Thing and any other Owlready2 elements used in the generated code
        }
        # Make existing classes available in the namespace
        for cls in onto.classes():
            namespace[cls.name] = cls

        try:
            exec(code_to_exec, namespace)
            print("Ontology modified successfully.")

            # Dynamically construct expected elements dictionary
            expected_elements = construct_expected_elements_dict(code_to_exec)

            # Verify modifications
            verify_ontology_modifications(onto, expected_elements)

        except Exception as e:
            print(f"Failed to modify ontology: {e}")

        # Save modifications to the specified path
        if save_path:
            onto.save(file=save_path)
            print(f"Ontology saved to {save_path}.")
        else:
            print("No save path provided. Ontology not saved.")
    else:
        print("No modification input provided. Skipping ontology modification.")


def add_intelligent_data_virtuoso(sparql_endpoint, local_ontology_path, graph_uri, virtuoso_endpoint, virtuoso_auth,
                                  modification_input=None):
    # Download the ontology from the given URL or create an empty file if not found
    download_ontology_from_graph(sparql_endpoint, graph_uri, local_ontology_path, auth=virtuoso_auth)

    # Modify the local_ontology_path to create a new path for the modified ontology
    # For example, append "_modified" before the file extension
    base, ext = os.path.splitext(local_ontology_path)
    modified_ontology_path = f"{base}_modified{ext}"

    # Load the ontology from the original or newly created file
    onto = get_ontology(f"file://{local_ontology_path}").load()

    # Use the agent to modify the ontology, saving the changes to the modified file path
    use_agent_to_modify_onto(onto, modification_input=modification_input, save_path=modified_ontology_path)

    # Upload the modified ontology back to Virtuoso using the modified file path
    upload_ontology_to_virtuoso(modified_ontology_path, graph_uri, virtuoso_endpoint, virtuoso_auth)


# Example usage
virtuoso_auth = HTTPDigestAuth('SPARQL_ADMIN', 'Bykrg8HNMR8SEhF3')
virtuoso_upload_endpoint = "http://localhost:8890/sparql-graph-crud"
sparql_endpoint = "http://localhost:8890/sparql"
local_ontology_path = r"C:\Users\philippe\PycharmProjects\Spiky_Mind\project_memory\ontologies\basic_ontology.rdf"
graph_uri = "http://spikymind.org/data/mygraph"
modification_input = "Add a new class named 'MyConcept' as a subclass of Thing. and 'MyMyConcept' as a subclass of MyConcept."

add_intelligent_data_virtuoso(sparql_endpoint, local_ontology_path, graph_uri, virtuoso_upload_endpoint, virtuoso_auth,
                              modification_input)
