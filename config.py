from os import path

APP_DIR = path.dirname(path.dirname(path.realpath(__file__)))
SKIN_DIR = path.join(APP_DIR, "view")
TEMPLATES_DIR = path.join(SKIN_DIR, "templates")
STATIC_DIR = path.join(SKIN_DIR, "style")
LOGFILE = APP_DIR + "/flask.log"
CACHE_FILE = path.join(APP_DIR, "cache", "DATA.p")
CACHE_HOURS = 1
DEFAULT_LANGUAGE = "en"
SPARQL_QUERY_LIMIT = 2000  # Maximum number of results to return per SPARQL query
MAX_RETRIES = 2
RETRY_SLEEP_SECONDS = 10
SPARQL_TIMEOUT = 60
LOCAL_URLS = False  # Parameter governing whether URLs shown are local or external
ABSOLUTE_URI_BASE = "http://vocabdev.nerc.ac.uk"
ABSOLUTE_URI_BASE_IN_DATA = "http://vocab.nerc.ac.uk"
SYSTEM_URI_BASE = "http://localhost:5000"

#
#   Vocabulary data sources
#
# Here is the list of vocabulary sources that this instance uses. FILE, SPARQL, RVA & VOCBENCH are implemented already
# and are on by default (e.g. VOCBENCH = None) but other sources, such as GitHub can be added. To enable them, add a new
# like like VocBench.XXX = None
class VocabSource:
    FILE = "FILE"
    SPARQL = "SPARQL"
    RVA = "RVA"
    VOCBENCH = "VOCBENCH"
    GITHUB = "GITHUB"
    NvsSPARQL = "NvsSPARQL"

# Main cache (SPARQL DB) variables
# BEGIN Instance Vars
DEBUG = False
SPARQL_ENDPOINT = "$SPARQL_ENDPOINT"
SPARQL_USERNAME = ""
SPARQL_PASSWORD = ""
SOURCE_NAME = "nvs"
# END Instance Vars

DATA_SOURCES = {
    # example SPARQL source configured using variables in "Instance Vars" above
    SOURCE_NAME: {
        "source": VocabSource.NvsSPARQL,
        "sparql_endpoint": SPARQL_ENDPOINT,
        "sparql_username": SPARQL_USERNAME,
        "sparql_password": SPARQL_PASSWORD,
    },
}

# Details for the main vocabulary list. Can be overridden in the vocabularies.html template
# BEGIN Vocabs list info
VOCS_URI = "https://vocab.nerc.ac.uk/"
VOCS_TITLE = "NVS Vocabularies"
VOCS_DESC = "Vocabularies managed by the National Vocabulary System (NVS)"
# END Vocabs list info
