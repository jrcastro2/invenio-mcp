from mcp.server.fastmcp import FastMCP
import requests

INVENIO_API_URL = "https://sandbox-cds-rdm.web.cern.ch/api"
INVENIO_TOKEN = "eHvDeB4sjlW99nRZEwblBcvU3NY0IlwzdxK1P6Jr5v2PvPWqv6sDALOC484Q"  # ideally loaded from env
DRAFT_ID = None
RESOURCE_TYPES = [
    "thesis",
    "thesis-bachelor_thesis",
    "thesis-doctoral_thesis",
    "publication"
]

mcp = FastMCP("InvenioRDM MCP Server")

def get_headers():
    return {"Authorization": f"Bearer {INVENIO_TOKEN}", "cookie": "session=1231dsa123dsa"}

@mcp.tool()
def get_records() -> list:
    """Fetch all records from InvenioRDM"""
    response = requests.get(f"{INVENIO_API_URL}/records", headers=get_headers())
    response.raise_for_status()
    return response.json()["hits"]["hits"]

@mcp.tool()
def set_draft_id(draft_id: str) -> str:
    """Set the draft ID for subsequent operations"""
    DRAFT_ID = draft_id
    return f"Draft ID set to {DRAFT_ID}"

@mcp.tool()
def create_draft() -> str:
    """Create a new empty draft in InvenioRDM"""
    response = requests.post(
        f"{INVENIO_API_URL}/records",
        json={},
        headers=get_headers()
    )
    response.raise_for_status()
    record = response.json()
    return record["links"]["self"]

@mcp.tool()
def set_title(title: str, draft_id: str) -> str:
    """Set the title of a draft"""
    if not draft_id:
        draft_id = DRAFT_ID
    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json={"metadata": {"title": title}},
        headers=get_headers()
    )
    response.raise_for_status()
    return f"Title set to '{title}' for draft {draft_id}"





@mcp.tool()
def upload_file(draft_id: str, file_path: str) -> str:
    """Upload a file to an existing draft"""
    # 1. Initialize file upload
    filename = file_path.split("/")[-1]
    init_response = requests.post(
        f"{INVENIO_API_URL}/records/{draft_id}/files",
        json={"key": filename},
        headers=get_headers()
    )
    init_response.raise_for_status()

    # 2. Upload content
    with open(file_path, "rb") as f:
        upload_response = requests.put(
            f"{INVENIO_API_URL}/records/{draft_id}/files/{filename}/content",
            data=f,
            headers=get_headers()
        )
        upload_response.raise_for_status()

    # 3. Commit upload
    commit_response = requests.post(
        f"{INVENIO_API_URL}/records/{draft_id}/files/{filename}/commit",
        headers=get_headers()
    )
    commit_response.raise_for_status()

    return f"File {filename} uploaded"

@mcp.tool()
def publish_draft(draft_id: str) -> str:
    """Publish a draft"""
    response = requests.post(
        f"{INVENIO_API_URL}/records/{draft_id}/draft/actions/publish",
        headers=get_headers()
    )
    response.raise_for_status()
    return f"Draft {draft_id} published"

