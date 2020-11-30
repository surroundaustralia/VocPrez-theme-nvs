from os import path

APP_DIR = path.dirname(path.dirname(path.realpath(__file__)))
SKIN_DIR = path.join(APP_DIR, "view")
TEMPLATES_DIR = path.join(SKIN_DIR, "templates")
STATIC_DIR = path.join(SKIN_DIR, "style")
LOGFILE = APP_DIR + "/vocprez.log"
CACHE_FILE = path.join(APP_DIR, "cache", "DATA.p")
CACHE_HOURS = 1
DEFAULT_LANGUAGE = "en"
SPARQL_QUERY_LIMIT = 2000  # Maximum number of results to return per SPARQL query
MAX_RETRIES = 2
RETRY_SLEEP_SECONDS = 10
SPARQL_TIMEOUT = 60
PORT = 5000

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
SYSTEM_URI_BASE = "$SYSTEM_URI_BASE"
ABSOLUTE_URI_BASE = "$ABSOLUTE_URI_BASE"
ABS_URI_BASE_IN_DATA = "$ABS_URI_BASE_IN_DATA"
USE_SYSTEM_URIS = True
DEBUG = False
SPARQL_ENDPOINT = "$SPARQL_ENDPOINT"
SPARQL_USERNAME = None
SPARQL_PASSWORD = None
SOURCE_NAME = "nvs"
# END Instance Vars

DATA_SOURCES = {
    SOURCE_NAME: {
        "source": VocabSource.NvsSPARQL,
        "sparql_endpoint": SPARQL_ENDPOINT,
        "sparql_username": SPARQL_USERNAME,
        "sparql_password": SPARQL_PASSWORD,
    },
}

# BEGIN Vocabs list info
VOCS_URI = "https://vocab.nerc.ac.uk/"
VOCS_TITLE = "NVS Vocabularies"
VOCS_DESC = "Vocabularies managed by the National Vocabulary System (NVS)"
# END Vocabs list info
