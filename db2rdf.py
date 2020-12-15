from pathlib import Path
import vocprez._config as config
from SPARQLWrapper import SPARQLWrapper
from rdflib import Namespace
from rdflib.namespace import DCTERMS
DUMP_DIR = Path(config.APP_DIR).parent


def dump_collections():
    q = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    CONSTRUCT {
        ?voc ?p ?o ;
    }
    WHERE {
      ?voc ?p ?o ;
           a skos:Collection ;
    
      MINUS {
        ?voc skos:member ?o .
      }
    }
    ORDER BY ?voc
    """
    q2 = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    CONSTRUCT {
      <http://vocab.nerc.ac.uk/collection/C67/current/> ?p ?o
    }
    WHERE {
      <http://vocab.nerc.ac.uk/collection/C67/current/> ?p ?o ;
           a skos:Collection .
    
      MINUS {
        <http://vocab.nerc.ac.uk/collection/C67/current/> <http://www.w3.org/2004/02/skos/core#member> ?o .
      }
    }
    """

    sparql = SPARQLWrapper(config.SPARQL_ENDPOINT)
    sparql.setQuery(q)
    g = sparql.query().convert()
    g.bind("dcterms", DCTERMS)
    g.bind("grg", Namespace("http://www.isotc211.org/schemas/grg/"))

    g.serialize(destination=str(DUMP_DIR / "db2rdf_collections.ttl"), format="turtle")


def dump_schemes():
    q = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    CONSTRUCT {
        ?voc ?p ?o ;
    }
    WHERE {
      ?voc ?p ?o ;
           a skos:ConceptScheme ;

      MINUS {
        ?voc skos:hasTopConcept ?o
      }
    }
    ORDER BY ?voc
    """

    sparql = SPARQLWrapper(config.SPARQL_ENDPOINT)
    sparql.setQuery(q)
    g = sparql.query().convert()
    g.bind("dcterms", DCTERMS)
    g.bind("grg", Namespace("http://www.isotc211.org/schemas/grg/"))

    g.serialize(destination=str(DUMP_DIR / "db2rdf_schemes.ttl"), format="turtle")


if __name__ == "__main__":
    # dump_collections()
    dump_schemes()
