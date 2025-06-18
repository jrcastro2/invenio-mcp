#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "mcp[cli]",
#   "requests",
# ]
# ///
import os
from enum import Enum

import requests
from mcp.server.fastmcp import FastMCP

INVENIO_API_URL = os.getenv("INVENIO_URL", "https://sandbox-cds-rdm.web.cern.ch/api")
INVENIO_TOKEN = os.getenv("INVENIO_TOKEN", "<or-your-token-here>")

mcp = FastMCP("InvenioRDM MCP Server")


def get_headers():
    return {
        "Authorization": f"Bearer {INVENIO_TOKEN}",
        "cookie": "session=1231dsa123dsa",
    }


@mcp.tool()
def get_records() -> list:
    """Fetch all records from InvenioRDM"""
    response = requests.get(f"{INVENIO_API_URL}/records", headers=get_headers())
    response.raise_for_status()
    return response.json()["hits"]["hits"]


@mcp.tool()
def create_draft() -> str:
    """Create a new empty draft in InvenioRDM"""
    response = requests.post(
        f"{INVENIO_API_URL}/records", json={}, headers=get_headers()
    )
    response.raise_for_status()
    record = response.json()
    return f"Draft {record['id']} created at {record['links']['self_html']}"


@mcp.tool()
def set_title(title: str, draft_id: str) -> str:
    """Set the title of a draft"""
    # Fetch the existing draft data
    draft_response = requests.get(
        f"{INVENIO_API_URL}/records/{draft_id}/draft", headers=get_headers()
    )
    draft_response.raise_for_status()
    draft_data = draft_response.json()

    # Update the title while preserving other metadata
    draft_data["metadata"]["title"] = title

    # Send the updated draft data
    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json=draft_data,
        headers=get_headers(),
    )
    response.raise_for_status()
    return f"Title set to '{title}' for draft {draft_id}"


@mcp.tool()
def set_description(description: str, draft_id: str) -> str:
    """Set the description of a draft"""
    draft_response = requests.get(
        f"{INVENIO_API_URL}/records/{draft_id}/draft", headers=get_headers()
    )
    draft_response.raise_for_status()
    metadata = draft_response.json()["metadata"]
    metadata["description"] = description

    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json={"metadata": metadata},
        headers=get_headers(),
    )
    response.raise_for_status()
    return f"Description set to '{description}' for draft {draft_id}"


@mcp.tool()
def set_publication_date(publication_date: str, draft_id: str = None) -> str:
    """Set the publication date of a draft."""
    draft_response = requests.get(
        f"{INVENIO_API_URL}/records/{draft_id}/draft", headers=get_headers()
    )
    draft_response.raise_for_status()
    metadata = draft_response.json()["metadata"]
    metadata["publication_date"] = publication_date

    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json={"metadata": metadata},
        headers=get_headers(),
    )
    response.raise_for_status()
    return f"Publication date set to '{publication_date}' for draft {draft_id}"


class ResourceType(str, Enum):
    PUBLICATION = "publication"
    PUBLICATION_BOOK = "publication-book"
    PUBLICATION_CONFERENCEPAPER = "publication-conferencepaper"
    PUBLICATION_CONFERENCEPROCEEDING = "publication-conferenceproceeding"
    PUBLICATION_ARTICLE = "publication-article"
    PUBLICATION_PREPRINT = "publication-preprint"
    PUBLICATION_REPORT = "publication-report"
    PUBLICATION_THESIS = "publication-thesis"
    PUBLICATION_WORKINGPAPER = "publication-workingpaper"
    PUBLICATION_DATAPAPER = "publication-datapaper"
    PUBLICATION_DISSERTATION = "publication-dissertation"
    POSTER = "poster"
    PRESENTATION = "presentation"
    DATASET = "dataset"
    IMAGE = "image"
    IMAGE_FIGURE = "image-figure"
    IMAGE_PHOTO = "image-photo"
    VIDEO = "video"
    AUDIO = "audio"
    SOFTWARE = "software"
    WORKFLOW = "workflow"


# # Uncomment this function if you want to use a query string for resource type (not working on cds-rdm sandbox, vocab are restrcited AFAIK)
# def set_resource_type(resource_type: str, draft_id: str) -> str:
#     """Set the resource type of a draft based on a query string."""
#     # Validate resource type by querying the vocabulary
#     response = requests.get(
#         f"{INVENIO_API_URL}/vocabularies/resourcetypes?q={resource_type}",
#         headers=get_headers()
#     )
#     response.raise_for_status()
#     resource_types = response.json()["hits"]["hits"]

#     if not resource_types:
#         raise ValueError(f"MCP Error: No matching resource type found for '{resource_type}'")

#     # Use the first match
#     matched_resource_type = resource_types[0]["id"]

#     # Fetch the existing draft data
#     draft_response = requests.get(
#         f"{INVENIO_API_URL}/records/{draft_id}/draft",
#         headers=get_headers()
#     )
#     draft_response.raise_for_status()
#     draft_data = draft_response.json()

#     # Update the resource type while preserving other metadata
#     draft_data["metadata"]["resource_type"] = {"id": matched_resource_type}

#     # Send the updated draft data
#     response = requests.put(
#         f"{INVENIO_API_URL}/records/{draft_id}/draft",
#         json=draft_data,
#         headers=get_headers()
#     )
#     response.raise_for_status()

#     return f"Resource type set to '{matched_resource_type}' for draft {draft_id}"


@mcp.tool()
def set_resource_type(resource_type: str, draft_id: str) -> str:
    """Set the resource type using predefined enum.

    Valid resource types:
    - publication
    - publication-book
    - publication-conferencepaper
    - publication-conferenceproceeding
    - publication-article
    - publication-preprint
    - publication-report
    - publication-thesis
    - publication-workingpaper
    - publication-datapaper
    - publication-dissertation
    - poster
    - presentation
    - dataset
    - image
    - image-figure
    - image-photo
    - video
    - audio
    - software
    - workflow
    """
    # Fetch draft
    draft_response = requests.get(
        f"{INVENIO_API_URL}/records/{draft_id}/draft", headers=get_headers()
    )
    draft_response.raise_for_status()
    draft_data = draft_response.json()
    # Validate resource type
    try:
        resource_type = ResourceType(resource_type)
    except ValueError:
        raise ValueError(
            f"MCP Error: Invalid resource type '{resource_type}'. Must be one of {list(ResourceType)}"
        )

    # Update resource type
    draft_data["metadata"]["resource_type"] = {"id": resource_type.value}

    # Push update
    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json=draft_data,
        headers=get_headers(),
    )
    response.raise_for_status()

    return f"Resource type set to '{resource_type.value}' for draft {draft_id}"


@mcp.tool()
def set_creators(creators: list[dict], draft_id: str) -> str:
    """Set the creators/authors of a draft.

    Expects a list of dictionaries with:
    - 'name' in a 'family_name, given_name' format (e.g. "Smith, John")
    - optional 'orcid' key for ORCID identifiers (e.g. "0000-0001-2345-6789")
    """
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

        parsed_creators.append(
            {
                "person_or_org": {
                    "name": full_name,
                    "type": "personal",
                    "given_name": given_name,
                    "family_name": family_name,
                    "identifiers": identifiers,
                }
            }
        )

    # Fetch draft
    draft_response = requests.get(
        f"{INVENIO_API_URL}/records/{draft_id}/draft", headers=get_headers()
    )
    draft_response.raise_for_status()
    draft_data = draft_response.json()

    # Update creators
    draft_data["metadata"]["creators"] = parsed_creators

    # Push update
    response = requests.put(
        f"{INVENIO_API_URL}/records/{draft_id}/draft",
        json=draft_data,
        headers=get_headers(),
    )
    response.raise_for_status()

    return f"Creators set for draft {draft_id}"


# @mcp.tool()
# def upload_file(draft_id: str, file_path: str) -> str:
#     """Upload a file to an existing draft"""
#     # 1. Initialize file upload
#     filename = file_path.split("/")[-1]
#     init_response = requests.post(
#         f"{INVENIO_API_URL}/records/{draft_id}/files",
#         json={"key": filename},
#         headers=get_headers(),
#     )
#     init_response.raise_for_status()
#
#     # 2. Upload content
#     with open(file_path, "rb") as f:
#         upload_response = requests.put(
#             f"{INVENIO_API_URL}/records/{draft_id}/files/{filename}/content",
#             data=f,
#             headers=get_headers(),
#         )
#         upload_response.raise_for_status()
#
#     # 3. Commit upload
#     commit_response = requests.post(
#         f"{INVENIO_API_URL}/records/{draft_id}/files/{filename}/commit",
#         headers=get_headers(),
#     )
#     commit_response.raise_for_status()
#
#     return f"File {filename} uploaded"


@mcp.tool()
def publish_draft(draft_id: str) -> str:
    """Publish a draft."""
    response = requests.post(
        f"{INVENIO_API_URL}/records/{draft_id}/draft/actions/publish",
        headers=get_headers(),
    )
    response.raise_for_status()
    return f"Draft {draft_id} published at {response.json()['links']['self_html']}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
