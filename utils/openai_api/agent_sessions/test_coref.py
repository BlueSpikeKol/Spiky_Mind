import time

import spacy_experimental as spacyE
import spacy
from spacy.lang.en import English

text = "Philip plays helldivers2 because he loves it."

complete_text = """Given the recent changes in tax legislation, reviewing our budget allocations is crucial,
especially for our R&D department. This department will see the new law, effective from next quarter,
imposing stricter regulations on capital expenditure. It will significantly impact the team,
which consists of more than 25 people. How do you think this affects our planned investment in 
new technology and personnel over the next fiscal year?"""

response_to_legislation_changes = """
As head of R&D, I recognize the impact of recent tax legislation on our strategy.
The new law introduces strict regulations on capital expenditure effective next quarter, directly affecting 
our advanced robotics initiative and lab expansion. This necessitates a shift towards software innovation and remote 
collaboration tools, less affected by these constraints. To support our team of over 25, we're seeking grants and 
partnerships to sustain our technology and personnel investments. Our department's agility will be key in leveraging 
these changes to continue leading in innovation.
"""

test_text1 = "What biological methods have been successful in eradicating invasive fish and mushroom species?"
test_text2 = "How would the global climate be affected if deforestation rates were reduced by 50% over the next 10 years?"
test_text3 = "What are the primary survival strategies of desert flora during prolonged drought conditions?"

modified_test_text1 = "Invasive species like fish and mushrooms can disrupt local ecosystems. " \
                      "What methods have been successful in eradicating them? Have any biological approaches proven effective?"

modified_test_text2 = "Deforestation is a major environmental concern. " \
                      "How would the global climate change if the rates of deforestation were reduced by 50% over the next 10 years?" \
                      " Would this reduction have a significant impact?"

modified_test_text3 = "Desert flora face extreme conditions during droughts. " \
                      "What are their primary survival strategies during such prolonged periods?" \
                      " How do these plants manage to sustain themselves?"


def test1(t):
    """
    Loads separate spaCy models for core language processing and coreference resolution,
    combines their pipelines while explicitly excluding certain pipes from the coreference model,
    and processes text to check coreference resolution output.

    This test illustrates an attempt to merge core linguistic features with coreference capabilities,
    but may face issues with incompatible or missing annotations due to excluded pipes.

    Parameters:
    - t (str): Text to be processed.

    Outputs:
    - Prints spans detected by the coreference resolution, highlighting potential clustering issues.
    """
    # NLP = spacy.load("en_core_web_trf")
    COREF = spacy.load("en_coreference_web_trf")
    COREF.disable_pipes("span_resolver", "span_cleaner")
    CORE = spacy.load("en_core_web_trf")

    NLP = English()
    for pipe in CORE.pipe_names:
        NLP.add_pipe(pipe, source=CORE)
    for pipe in COREF.pipe_names:
        if pipe in NLP.pipe_names:
            continue
        NLP.add_pipe(pipe, source=COREF)

    doc = NLP(t)
    print(doc.spans)
    # OUTPUT: {'coref_head_clusters_1': [bass, it]}
    # 'Philip' and 'he' are not clustered


def test2(t):
    """
    Loads coreference and core language processing models separately and merges them by adding coreference pipes first,
    then core language pipes. This order ensures coreference annotations are preserved and then supplemented by core linguistic annotations.

    However, this may lead to incomplete linguistic annotations as the core language model's pipes are added
    after coreference pipes, which might not fully integrate.

    Parameters:
    - t (str): Text to be processed.

    Outputs:
    - Prints spans showing successful coreference clustering.
    - Prints token indices, texts, parts of speech, and dependency labels, indicating potentially incorrect or missing linguistic annotations.
    """
    COREF = spacy.load("en_coreference_web_trf")
    COREF.disable_pipes("span_resolver", "span_cleaner")
    CORE = spacy.load("en_core_web_trf")

    NLP = English()
    for pipe in COREF.pipe_names:
        NLP.add_pipe(pipe, source=COREF)
    for pipe in CORE.pipe_names:
        if pipe in NLP.pipe_names:
            continue
        NLP.add_pipe(pipe, source=CORE)

    doc = NLP(t)
    print(doc.spans)
    # OUTPUT: {'coref_head_clusters_1': [Philip, he], 'coref_head_clusters_2': [bass, it]}
    # Now clusters are okay
    # But linguistic annotations do not make sense
    print([(t.i, t.text, t.pos_, t.dep_) for t in doc])


def test3(t):
    """
    Demonstrates an advanced integration technique by loading a coreference model, replacing its transformer listener
    with core language model components, and then removing the original transformer to optimize performance.

    This approach is intended to fully integrate core linguistic processing with coreference resolution without
    maintaining redundant transformers, potentially improving processing efficiency and annotation coherence.

    Parameters:
    - t (str): Text to be processed.

    Outputs:
    - Prints detected coreference spans.
    - Prints detailed linguistic annotations for each token, showing effective integration of language processing.
    """
    # move the 'transformer' from the coref pipeline to each component, then remove it
    nlp = spacy.load("en_coreference_web_trf")
    nlp.replace_listeners("transformer", "coref", ["model.tok2vec"])
    nlp.replace_listeners("transformer", "span_resolver", ["model.tok2vec"])
    nlp.remove_pipe("transformer")

    # copy all core components (including the transformer) as is
    CORE = spacy.load("en_core_web_trf")
    for pipe in CORE.pipe_names:
        nlp.add_pipe(pipe, source=CORE)

    doc = nlp(t)
    print(doc.spans)
    print([(t.i, t.text, t.pos_, t.dep_) for t in doc])


def test4(t):
    """
    Optimizes processing by loading both the core language and coreference models with a shared vocabulary,
    and by processing the text first through the core model then passing the Doc object to the coreference model.

    This method reduces overhead from duplicate tokenization and vocabulary management, leading to faster processing
    while maintaining the integrity of both coreference and linguistic annotations.

    Parameters:
    - t (str): Text to be processed.

    Outputs:
    - Prints coreference spans.
    - Prints detailed linguistic annotations, reflecting efficient and coherent processing of text.
    """
    nlp = spacy.load("en_core_web_trf")
    nlp_coref = spacy.load("en_coreference_web_trf", vocab=nlp.vocab)

    doc = nlp(t)

    # note that here you're passing in the doc rather than the text
    doc = nlp_coref(doc)

    print(doc.spans)
    for key in doc.spans:
        if key.startswith('coref_clusters'):
            print(f"Cluster ({key}):")
            for mention in doc.spans[key]:
                print(f" - Mention: {mention.text}, [Start: {mention.start}, End: {mention.end}]")

    print([(t.i, t.text, t.pos_, t.dep_) for t in doc])


if __name__ == "__main__":
    print(complete_text)

    t = time.time()
    test4(complete_text)
    print(time.time() - t)
