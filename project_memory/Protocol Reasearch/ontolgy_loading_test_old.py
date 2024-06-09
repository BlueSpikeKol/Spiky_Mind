# from owlready2 import *
#
# # Load the Pizza ontology from a local file
# onto = get_ontology("file://C:/Users/philippe/Documents/Downloads/pizza_test.rdf").load()
#
# # Interact with the ontology
# print("Classes in the Pizza ontology:")
# print(list(onto.classes()))
#
# # Accessing the Pizza class by label search
# pizza_class = onto.search_one(label="Pizza")
# print("\nAccessing the Pizza class by label search:")
# print(pizza_class)
#
# # Interacting with the Pizza class
# if pizza_class:
#     print("\nDetails of the Pizza class:")
#     print(f"Name: {pizza_class.name}")
#     print(f"IRI: {pizza_class.iri}")
#     print(f"Label: {pizza_class.label}")
#
#     # List subclasses of Pizza
#     print("\nSubclasses of Pizza:")
#     for subclass in pizza_class.subclasses():
#         print(subclass)
#
#     # List instances of Pizza
#     print("\nInstances of Pizza:")
#     for instance in pizza_class.instances():
#         print(instance)
# else:
#     print("Pizza class not found.")

from owlready2 import *
import owlready2

# Set the path to the Java executable
owlready2.JAVA_EXE = "C:\\Program Files\\Java\\jdk-22\\bin\\java.exe"

# Create a new ontology
onto = get_ontology("http://test.org/onto.owl")

with onto:
    # Existing classes and properties
    class Drug(Thing):
        def take(self): print("I took a drug")


    class ActivePrinciple(Thing):
        pass
    class AdministrationRoute(Thing):
        pass
    class has_administration_route(Drug >> AdministrationRoute):
        python_name = "administration_routes"


    class has_for_active_principle(Drug >> ActivePrinciple):
        python_name = "active_principles"


    class Placebo(Drug):
        equivalent_to = [Drug & Not(has_for_active_principle.some(ActivePrinciple)) & has_administration_route.some(AdministrationRoute)]

        def take(self): print("I took a placebo")


    class SingleActivePrincipleDrug(Drug):
        equivalent_to = [Drug & has_for_active_principle.exactly(1, ActivePrinciple) & has_administration_route.some(AdministrationRoute)]

        def take(self): print("I took a drug with a single active principle")


    class DrugAssociation(Drug):
        equivalent_to = [Drug & has_for_active_principle.min(2, ActivePrinciple) & has_administration_route.some(AdministrationRoute)]

        def take(self): print("I took a drug with %s active principles" % len(self.active_principles))


    # Declare disjointness between Placebo, SingleActivePrincipleDrug, and DrugAssociation
    AllDisjoint([Placebo, SingleActivePrincipleDrug, DrugAssociation])
    oral_administration = AdministrationRoute("oral")
    topical_administration = AdministrationRoute("topical")

    # New classes with General Class Axioms
    class TopicalDrug(Drug):
        equivalent_to = [Drug & has_for_active_principle.some(ActivePrinciple) & has_administration_route.value(topical_administration)]

# Create instances
acetaminophen = ActivePrinciple("acetaminophen")
amoxicillin = ActivePrinciple("amoxicillin")
clavulanic_acid = ActivePrinciple("clavulanic_acid")



AllDifferent([acetaminophen, amoxicillin, clavulanic_acid])

drug1 = Drug(active_principles=[acetaminophen])
drug2 = Drug(active_principles=[amoxicillin, clavulanic_acid])
drug3 = Drug(active_principles=[])
drug4 = Drug(active_principles=[acetaminophen], administration_routes=[topical_administration])
drug5 = Drug(active_principles=[amoxicillin], administration_routes=[oral_administration])
drug6 = Drug(active_principles=[acetaminophen],
             administration_routes=[topical_administration])  # Both oral and topical

close_world(Drug)

# Run the reasoner to perform inference
# Save the ontology to the specified path
onto_path = "C:\\Users\\philippe\\PycharmProjects\\Spiky_Mind\\project_memory\\ontologies\\ontology_debug_test.owl"
onto.save(file=onto_path, format="rdfxml")

# Run the reasoner to perform inference
try:
    sync_reasoner()
except OwlReadyInconsistentOntologyError:
    print("The ontology is inconsistent!")

# Check the classifications
print("Classifications after reasoning:")
print(f"drug1: {drug1.is_a}")
print(f"drug2: {drug2.is_a}")
print(f"drug3: {drug3.is_a}")
print(f"drug4: {drug4.is_a}")
print(f"drug5: {drug5.is_a}")
print(f"drug6: {drug6.is_a}")

# Check if the new instances are inferred correctly
print("drug4 is a TopicalDrug:", drug4 in TopicalDrug.instances())
print("drug6 is a TopicalDrug:", drug6 in TopicalDrug.instances())

# Take actions to verify method overrides
drug1.take()
drug2.take()
drug3.take()
drug4.take()
drug5.take()
drug6.take()

"""
Classes in the Pizza ontology: [pizza.Pizza, pizza.PizzaBase, pizza.Food, pizza.Spiciness, pizza.PizzaTopping, 
pizza.American, pizza.NamedPizza, pizza.MozzarellaTopping, pizza.PeperoniSausageTopping, pizza.TomatoTopping, 
pizza.AmericanHot, pizza.HotGreenPepperTopping, pizza.JalapenoPepperTopping, pizza.AnchoviesTopping, 
pizza.FishTopping, pizza.ArtichokeTopping, pizza.VegetableTopping, pizza.Mild, pizza.AsparagusTopping, pizza.Cajun, 
pizza.OnionTopping, pizza.PeperonataTopping, pizza.PrawnsTopping, pizza.TobascoPepperSauce, pizza.CajunSpiceTopping, 
pizza.HerbSpiceTopping, pizza.Hot, pizza.RosemaryTopping, pizza.CaperTopping, pizza.Capricciosa, pizza.HamTopping, 
pizza.OliveTopping, pizza.Caprina, pizza.GoatsCheeseTopping, pizza.SundriedTomatoTopping, pizza.CheeseTopping, 
pizza.CheeseyPizza, pizza.CheeseyVegetableTopping, pizza.ChickenTopping, pizza.MeatTopping, pizza.Country, 
pizza.DomainConcept, pizza.DeepPanBase, pizza.ThinAndCrispyBase, pizza.ValuePartition, pizza.Fiorentina, 
pizza.GarlicTopping, pizza.ParmesanTopping, pizza.SpinachTopping, pizza.FourCheesesTopping, pizza.FourSeasons, 
pizza.MushroomTopping, pizza.FruitTopping, pizza.FruttiDiMare, pizza.MixedSeafoodTopping, pizza.Medium, 
pizza.Giardiniera, pizza.LeekTopping, pizza.PetitPoisTopping, pizza.SlicedTomatoTopping, pizza.GorgonzolaTopping, 
pizza.GreenPepperTopping, pizza.PepperTopping, pizza.HotSpicedBeefTopping, pizza.IceCream, pizza.InterestingPizza, 
pizza.LaReine, pizza.Margherita, pizza.MeatyPizza, pizza.Mushroom, pizza.Napoletana, pizza.NonVegetarianPizza, 
pizza.VegetarianPizza, pizza.NutTopping, pizza.ParmaHamTopping, pizza.Parmense, pizza.PineKernels, 
pizza.PolloAdAstra, pizza.RedOnionTopping, pizza.SweetPepperTopping, pizza.PrinceCarlo, pizza.QuattroFormaggi, 
pizza.RealItalianPizza, pizza.RocketTopping, pizza.Rosa, pizza.SauceTopping, pizza.Siciliana, pizza.SloppyGiuseppe, 
pizza.Soho, pizza.SpicyPizza, pizza.SpicyTopping, pizza.SpicyPizzaEquivalent, pizza.SultanaTopping, 
pizza.ThinAndCrispyPizza, pizza.UnclosedPizza, pizza.VegetarianPizzaEquivalent1, pizza.VegetarianTopping, 
pizza.VegetarianPizzaEquivalent2, pizza.Veneziana]
"""

"""
An ontology has the following attributes:

.base_iri : base IRI for the ontology

.imported_ontologies : the list of imported ontologies (see below)

and the following methods:

.classes() : returns a generator for the Classes defined in the ontology (see Classes and Individuals (Instances))

.individuals() : returns a generator for the individuals (or instances) defined in the ontology (see Classes and Individuals (Instances))

.object_properties() : returns a generator for ObjectProperties defined in the ontology (see Properties)

.data_properties() : returns a generator for DataProperties defined in the ontology (see Properties)

.annotation_properties() : returns a generator for AnnotationProperties defined in the ontology (see Annotations)

.properties() : returns a generator for all Properties (object-, data- and annotation-) defined in the ontology

.disjoint_classes() : returns a generator for AllDisjoint constructs for Classes defined in the ontology (see Disjointness, open and local closed world reasoning)

.disjoint_properties() : returns a generator for AllDisjoint constructs for Properties defined in the ontology (see Disjointness, open and local closed world reasoning)

.disjoints() : returns a generator for AllDisjoint constructs (for Classes and Properties) defined in the ontology

.different_individuals() : returns a generator for AllDifferent constructs for individuals defined in the ontology (see Disjointness, open and local closed world reasoning)

.get_namepace(base_iri) : returns a namespace for the ontology and the given base IRI (see namespaces below, in the next section)
"""

"""
class NonPlaceboDrug(Drug):
    equivalent_to = [Drug & has_for_active_principle.some(ActivePrinciple)]

class Placebo(Drug):
    equivalent_to = [Drug & Not(has_for_active_principle.some(ActivePrinciple))]
"""

"""
some : Property.some(Range_Class)

only : Property.only(Range_Class)

min : Property.min(cardinality, Range_Class)

max : Property.max(cardinality, Range_Class)

exactly : Property.exactly(cardinality, Range_Class)

value : Property.value(Range_Individual / Literal value)

has_self : Property.has_self(Boolean value)
"""

"""
‘&’ : And operator (intersection). For example: Class1 & Class2. It can also be written: And([Class1, Class2])

‘|’ : Or operator (union). For example: Class1 | Class2. It can also be written: Or([Class1, Class2])

Not() : Not operator (negation or complement). For example: Not(Class1)
"""

"""
integer_between_0_and_20 = ConstrainedDatatype(int, min_inclusive=0, max_inclusive=20)
short_string = ConstrainedDatatype(str, max_length=100)

with onto:
    # Define classes
    class Person(Thing):
        pass

    # Define properties with constrained datatypes
    class age(DataProperty, FunctionalProperty):
        domain = [Person]
        range = [integer_between_0_and_20]
"""

"""
class hasParent(Person >> Person):
        pass

    class hasBrother(Person >> Person):
        pass

    # Create a property chain for hasUncle
    hasUncle = PropertyChain([hasParent, hasBrother])

# Create instances to demonstrate the property chain
with onto:
    john = Person("John")
    mary = Person("Mary")
    robert = Person("Robert")
    mike = Person("Mike")

    # Define relationships
    john.hasParent.append(robert)
    robert.hasBrother.append(mike)

    # The property chain should infer that John has an uncle Mike
    # However, owlready2 does not perform inference, so this is more for illustrative purposes.

# Verify the property chain setup
print("Property chain for hasUncle:", hasUncle.properties)
"""

# Loads Gene Ontology (~ 170 Mb), can take a moment!
# go = get_ontology("http://purl.obolibrary.org/obo/go.owl").load()
#
# # Get the number of OWL Class in GO
# list(default_world.sparql("""
#            SELECT (COUNT(?x) AS ?nb)
#            { ?x a owl:Class . }
#     """))

# insertion = get_ontology("http://test.org/insertion.owl")
# with insertion:
#     default_world.sparql("""
#            INSERT { ?x rdfs:label "héritage mitochondrial"@fr }
#            WHERE  { ?x rdfs:label "mitochondrion inheritance" . }
#            """)

# default_world.set_backend(filename = "/path/to/your/file.sqlite3")

"By default, Owlready2 opens the SQLite3 database in exclusive mode. "
"This mode is faster, but it does not allow several programs to use the same database simultaneously. "
"If you need to have several Python programs that access simultaneously the same Owlready2 quadstore, "
"you can disable the exclusive mode as follows:"

"""default_world.set_backend(filename = "/path/to/your/file.sqlite3", exclusive = False)"""
