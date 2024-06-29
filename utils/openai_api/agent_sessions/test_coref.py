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


def test1(t):
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
    Same results as test3 with 'complete_text' as input argument. But it is significantly faster.
    """
    nlp = spacy.load("en_core_web_trf")
    nlp_coref = spacy.load("en_coreference_web_trf", vocab=nlp.vocab)

    doc = nlp(t)

    # note that here you're passing in the doc rather than the text
    doc = nlp_coref(doc)

    print(doc.spans)
    print([(t.i, t.text, t.pos_, t.dep_) for t in doc])


if __name__ == "__main__":
    print(complete_text)

    t = time.time()
    test3(complete_text)
    print(time.time() - t)
