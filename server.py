from mcp.server.fastmcp import FastMCP
import requests

INVENIO_API_URL = "https://sandbox-cds-rdm.web.cern.ch/api"
INVENIO_TOKEN = "ZldKFGAWAWqoPaDJDWGoWCw6JDRfWDiobBH52HoRaQf35tXuctImnXwl6hG2"  # ideally loaded from env
DRAFT_ID = None

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
    # Fetch the existing draft data
    draft_response = requests.get(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        headers=get_headers()
    )
    draft_response.raise_for_status()
    draft_data = draft_response.json()

    # Update the title while preserving other metadata
    draft_data["metadata"]["title"] = title

    # Send the updated draft data
    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json=draft_data,
        headers=get_headers()
    )
    response.raise_for_status()
    return f"Title set to '{title}' for draft {draft_id}"

@mcp.tool()
def set_description(description: str, draft_id: str) -> str:
    """Set the description of a draft"""
    if not draft_id:
        draft_id = DRAFT_ID
    draft_response = requests.get(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        headers=get_headers()
    )
    draft_response.raise_for_status()
    metadata = draft_response.json()["metadata"]
    metadata["description"] = description

    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json={"metadata": metadata},
        headers=get_headers()
    )
    response.raise_for_status()
    return f"Description set to '{description}' for draft {draft_id}"

@mcp.tool()
def set_publication_date(publication_date: str, draft_id: str = None) -> str:
    """Set the publication date of a draft"""
    if not draft_id:
        draft_id = DRAFT_ID
    draft_response = requests.get(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        headers=get_headers()
    )
    draft_response.raise_for_status()
    metadata = draft_response.json()["metadata"]
    metadata["publication_date"] = publication_date

    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json={"metadata": metadata},
        headers=get_headers()
    )
    response.raise_for_status()
    return f"Publication date set to '{publication_date}' for draft {draft_id}"

def set_resource_type(resource_type: str, draft_id: str) -> str:
    """Set the resource type of a draft based on a query string."""
    if not draft_id:
        draft_id = DRAFT_ID

    # Validate resource type by querying the vocabulary
    response = requests.get(
        f"{INVENIO_API_URL}/vocabularies/resourcetypes?q={resource_type}",
        headers=get_headers()
    )
    response.raise_for_status()
    resource_types = response.json()["hits"]["hits"]

    if not resource_types:
        raise ValueError(f"MCP Error: No matching resource type found for '{resource_type}'")

    # Use the first match
    matched_resource_type = resource_types[0]["id"]

    # Fetch the existing draft data
    draft_response = requests.get(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        headers=get_headers()
    )
    draft_response.raise_for_status()
    draft_data = draft_response.json()

    # Update the resource type while preserving other metadata
    draft_data["metadata"]["resource_type"] = {"id": matched_resource_type}

    # Send the updated draft data
    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json=draft_data,
        headers=get_headers()
    )
    response.raise_for_status()

    return f"Resource type set to '{matched_resource_type}' for draft {draft_id}"

@mcp.tool()
def set_creators(creators: list[dict], draft_id: str) -> str:
    """Simplified creators setter: expects name + optional ORCID."""

    if not draft_id:
        draft_id = DRAFT_ID

    parsed_creators = []
    for creator in creators:
        full_name = creator.get("name", "").strip()
        orcid = creator.get("orcid")

        # Simple name split (works for most western names)
        try:
            family_name, given_name = full_name.split(",", 1)
            family_name = family_name.strip()
            given_name = given_name.strip()
        except ValueError:
            # Fallback: entire string as family_name
            family_name = full_name
            given_name = ""

        # Build identifiers list: ORCID is fully optional
        identifiers = [{"scheme": "orcid", "identifier": orcid}] if orcid else []

        parsed_creators.append({
            "person_or_org": {
                "name": full_name,
                "type": "personal",
                "given_name": given_name,
                "family_name": family_name,
                "identifiers": identifiers
            }
        })

    # Fetch draft
    draft_response = requests.get(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        headers=get_headers()
    )
    draft_response.raise_for_status()
    draft_data = draft_response.json()

    # Update creators
    draft_data["metadata"]["creators"] = parsed_creators

    # Push update
    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json=draft_data,
        headers=get_headers()
    )
    response.raise_for_status()

    return f"Creators set for draft {draft_id}"

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

