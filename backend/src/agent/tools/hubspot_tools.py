"""HubSpot tools for LangChain agent."""

from typing import Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.integrations.hubspot.client import HubSpotClient, HubSpotAPIError
from src.services.integration_service import IntegrationService
from src.agent.tools.base import handle_tool_error
from src.core.logging import logger


class ReadHubSpotContactInput(BaseModel):
    """Input for reading a HubSpot contact."""

    contact_id: str = Field(description="The HubSpot contact ID to read")


class ReadHubSpotContactTool(BaseTool):
    """Tool for reading a HubSpot contact by ID."""

    name: str = "read_hubspot_contact"
    description: str = (
        "Read a HubSpot contact by ID. Returns contact details including name, email, and properties."
    )
    args_schema: Type[BaseModel] = ReadHubSpotContactInput
    model_config = {"extra": "allow"}  # Allow extra fields like 'client'

    def __init__(self, client: HubSpotClient, **kwargs):
        """Initialize the tool with a HubSpot client."""
        super().__init__(**kwargs)
        # Use object.__setattr__ for Pydantic v2
        object.__setattr__(self, "client", client)

    def _run(self, contact_id: str) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, contact_id: str) -> str:
        """Read a contact from HubSpot."""
        try:
            result = await self.client.get_contact(contact_id)
            properties = result.get("properties", {})

            # Format response
            name = properties.get("firstname", "") + " " + \
                properties.get("lastname", "")
            email = properties.get("email", "N/A")

            return f"Contact: {name.strip() or 'N/A'} ({email})\nProperties: {properties}"
        except HubSpotAPIError as e:
            return handle_tool_error(e, "HubSpot")
        except Exception as e:
            logger.error(
                f"Unexpected error reading HubSpot contact: {e}", exc_info=True)
            return f"Error reading contact: {str(e)}"


class SearchHubSpotContactsInput(BaseModel):
    """Input for searching HubSpot contacts."""

    query: Optional[str] = Field(
        default=None, description="Search query (name, email, etc.). If empty, returns recent contacts."
    )
    limit: int = Field(
        default=10, description="Maximum number of contacts to return (1-100)")


class SearchHubSpotContactsTool(BaseTool):
    """Tool for searching HubSpot contacts."""

    name: str = "search_hubspot_contacts"
    description: str = (
        "Search for HubSpot contacts by name, email, or other properties. "
        "Returns a list of matching contacts with their details."
    )
    args_schema: Type[BaseModel] = SearchHubSpotContactsInput
    model_config = {"extra": "allow"}  # Allow extra fields like 'client'

    def __init__(self, client: HubSpotClient, **kwargs):
        """Initialize the tool with a HubSpot client."""
        super().__init__(**kwargs)
        # Use object.__setattr__ for Pydantic v2
        object.__setattr__(self, "client", client)

    def _run(self, query: Optional[str] = None, limit: int = 10) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, query: Optional[str] = None, limit: int = 10) -> str:
        """Search contacts in HubSpot."""
        try:
            result = await self.client.search_contacts(query=query, limit=min(limit, 100))
            contacts = result.get("results", [])

            if not contacts:
                return "No contacts found."

            # Format response
            formatted = []
            for contact in contacts:
                props = contact.get("properties", {})
                name = props.get("firstname", "") + " " + \
                    props.get("lastname", "")
                email = props.get("email", "N/A")
                formatted.append(
                    f"- {name.strip() or 'N/A'} ({email}) [ID: {contact.get('id')}]")

            return f"Found {len(contacts)} contact(s):\n" + "\n".join(formatted)
        except HubSpotAPIError as e:
            return handle_tool_error(e, "HubSpot")
        except Exception as e:
            logger.error(
                f"Unexpected error searching HubSpot contacts: {e}", exc_info=True)
            return f"Error searching contacts: {str(e)}"


class ReadHubSpotCompanyInput(BaseModel):
    """Input for reading a HubSpot company."""

    company_id: str = Field(description="The HubSpot company ID to read")


class ReadHubSpotCompanyTool(BaseTool):
    """Tool for reading a HubSpot company by ID."""

    name: str = "read_hubspot_company"
    description: str = (
        "Read a HubSpot company by ID. Returns company details including name, domain, and properties."
    )
    args_schema: Type[BaseModel] = ReadHubSpotCompanyInput
    model_config = {"extra": "allow"}  # Allow extra fields like 'client'

    def __init__(self, client: HubSpotClient, **kwargs):
        """Initialize the tool with a HubSpot client."""
        super().__init__(**kwargs)
        # Use object.__setattr__ for Pydantic v2
        object.__setattr__(self, "client", client)

    def _run(self, company_id: str) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, company_id: str) -> str:
        """Read a company from HubSpot."""
        try:
            result = await self.client.get_company(company_id)
            properties = result.get("properties", {})

            # Format response
            name = properties.get("name", "N/A")
            domain = properties.get("domain", "N/A")

            return f"Company: {name} (Domain: {domain})\nProperties: {properties}"
        except HubSpotAPIError as e:
            return handle_tool_error(e, "HubSpot")
        except Exception as e:
            logger.error(
                f"Unexpected error reading HubSpot company: {e}", exc_info=True)
            return f"Error reading company: {str(e)}"


class SearchHubSpotCompaniesInput(BaseModel):
    """Input for searching HubSpot companies."""

    query: Optional[str] = Field(
        default=None, description="Search query (name, domain, etc.). If empty, returns recent companies."
    )
    limit: int = Field(
        default=10, description="Maximum number of companies to return (1-100)")


class SearchHubSpotCompaniesTool(BaseTool):
    """Tool for searching HubSpot companies."""

    name: str = "search_hubspot_companies"
    description: str = (
        "Search for HubSpot companies by name, domain, or other properties. "
        "Returns a list of matching companies with their details."
    )
    args_schema: Type[BaseModel] = SearchHubSpotCompaniesInput
    model_config = {"extra": "allow"}  # Allow extra fields like 'client'

    def __init__(self, client: HubSpotClient, **kwargs):
        """Initialize the tool with a HubSpot client."""
        super().__init__(**kwargs)
        # Use object.__setattr__ for Pydantic v2
        object.__setattr__(self, "client", client)

    def _run(self, query: Optional[str] = None, limit: int = 10) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, query: Optional[str] = None, limit: int = 10) -> str:
        """Search companies in HubSpot."""
        try:
            result = await self.client.search_companies(query=query, limit=min(limit, 100))
            companies = result.get("results", [])

            if not companies:
                return "No companies found."

            # Format response
            formatted = []
            for company in companies:
                props = company.get("properties", {})
                name = props.get("name", "N/A")
                domain = props.get("domain", "N/A")
                formatted.append(
                    f"- {name} (Domain: {domain}) [ID: {company.get('id')}]")

            return f"Found {len(companies)} company(ies):\n" + "\n".join(formatted)
        except HubSpotAPIError as e:
            return handle_tool_error(e, "HubSpot")
        except Exception as e:
            logger.error(
                f"Unexpected error searching HubSpot companies: {e}", exc_info=True)
            return f"Error searching companies: {str(e)}"


class UpdateHubSpotContactInput(BaseModel):
    """Input for updating a HubSpot contact."""

    contact_id: str = Field(description="The HubSpot contact ID to update")
    properties: dict = Field(
        description="Dictionary of properties to update (e.g., {'email': 'new@example.com', 'firstname': 'John'})")


class UpdateHubSpotContactTool(BaseTool):
    """Tool for updating a HubSpot contact."""

    name: str = "update_hubspot_contact"
    description: str = (
        "Update a HubSpot contact's properties. Provide contact_id and a dictionary of properties to update. "
        "Example: To update email, use {'email': 'new@example.com'}. "
        "Common properties: email, firstname, lastname, phone, company, etc."
    )
    args_schema: Type[BaseModel] = UpdateHubSpotContactInput
    model_config = {"extra": "allow"}

    def __init__(self, client: HubSpotClient, **kwargs):
        """Initialize the tool with a HubSpot client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "client", client)

    def _run(self, contact_id: str, properties: dict) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, contact_id: str, properties: dict) -> str:
        """Update a contact in HubSpot."""
        try:
            # Validate properties are not empty
            if not properties:
                return "Error: No properties provided to update. Please specify at least one property (e.g., {'email': 'new@example.com'})."
            
            result = await self.client.update_contact(contact_id, properties)
            updated_props = list(properties.keys())
            return f"Contact {contact_id} updated successfully. Properties updated: {', '.join(updated_props)}"
        except HubSpotAPIError as e:
            error_msg = handle_tool_error(e, "HubSpot")
            # Add helpful suggestions for common errors
            if "not found" in str(e).lower():
                error_msg += " You can use the search_hubspot_contacts tool to find valid contact IDs."
            return error_msg
        except Exception as e:
            logger.error(
                f"Unexpected error updating HubSpot contact: {e}", exc_info=True)
            return f"Error updating contact: {str(e)}"


class CreateHubSpotNoteInput(BaseModel):
    """Input for creating a HubSpot note."""

    note: str = Field(description="The note content")
    contact_id: Optional[str] = Field(
        default=None, description="Optional: Associate note with a contact ID")
    company_id: Optional[str] = Field(
        default=None, description="Optional: Associate note with a company ID")


class CreateHubSpotNoteTool(BaseTool):
    """Tool for creating a HubSpot note."""

    name: str = "create_hubspot_note"
    description: str = (
        "Create a note in HubSpot. Can be associated with a contact or company. "
        "Provide the note content and optionally a contact_id or company_id."
    )
    args_schema: Type[BaseModel] = CreateHubSpotNoteInput
    model_config = {"extra": "allow"}

    def __init__(self, client: HubSpotClient, **kwargs):
        """Initialize the tool with a HubSpot client."""
        super().__init__(**kwargs)
        object.__setattr__(self, "client", client)

    def _run(self, note: str, contact_id: Optional[str] = None, company_id: Optional[str] = None) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError(
            "This tool is async-only. Use _arun instead.")

    async def _arun(self, note: str, contact_id: Optional[str] = None, company_id: Optional[str] = None) -> str:
        """Create a note in HubSpot."""
        try:
            result = await self.client.create_note(contact_id=contact_id, company_id=company_id, note=note)
            note_id = result.get("id", "unknown")
            association = []
            if contact_id:
                association.append(f"contact {contact_id}")
            if company_id:
                association.append(f"company {company_id}")
            assoc_text = f" associated with {', '.join(association)}" if association else ""
            return f"Note created successfully (ID: {note_id}){assoc_text}."
        except HubSpotAPIError as e:
            return handle_tool_error(e, "HubSpot")
        except Exception as e:
            logger.error(
                f"Unexpected error creating HubSpot note: {e}", exc_info=True)
            return f"Error creating note: {str(e)}"


async def get_hubspot_tools(db, user_id: str) -> list[BaseTool]:
    """Get all HubSpot tools for a user."""
    client = await IntegrationService.get_hubspot_client(db, user_id)

    if not client:
        return []  # No HubSpot integration connected

    return [
        ReadHubSpotContactTool(client=client),
        SearchHubSpotContactsTool(client=client),
        ReadHubSpotCompanyTool(client=client),
        SearchHubSpotCompaniesTool(client=client),
        UpdateHubSpotContactTool(client=client),
        CreateHubSpotNoteTool(client=client),
    ]
