"""
Salesforce REST API Tools
Pure functions for Salesforce CRM operations - no business logic.
"""

import logging
import re
from typing import Optional

import requests

from src.config import get_salesforce_config

logger = logging.getLogger(__name__)

# ============================================================================
# Authentication
# ============================================================================

_access_token: Optional[str] = None
_instance_url: Optional[str] = None


def _sanitize_text(text: str) -> str:
    """
    Sanitize text input to prevent injection attacks.
    Removes potentially dangerous characters and limits length.
    """
    if not text:
        return ""
    # Remove any HTML/script tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove any SOQL injection patterns
    text = re.sub(r"['\";-]", '', text)
    # Limit length
    return text[:5000]


def _check_should_mock() -> bool:
    """
    Check if we should use mock mode based on configuration.
    This is called before _is_mock_mode is available.
    """
    config = get_salesforce_config()
    
    # Explicit mock mode in config
    if config.is_mock:
        return True
    
    # Check for placeholder/missing credentials
    placeholder_values = [
        "your_connected_app_client_id",
        "your_connected_app_client_secret",
        "your_salesforce_username",
        "your_salesforce_password",
        "your_security_token",
    ]

    # For client_credentials, only check client_id and client_secret
    if config.auth_type == "client_credentials":
        return (
            config.client_id in placeholder_values or
            config.client_id == "" or
            config.client_secret in placeholder_values or
            config.client_secret == ""
        )

    # For password flow, also check username and password
    return (
        config.client_id in placeholder_values or
        config.client_id == "" or
        config.client_secret in placeholder_values or
        config.client_secret == "" or
        config.username in placeholder_values or
        config.username == "" or
        config.password in placeholder_values or
        config.password == ""
    )


def authenticate() -> tuple[str, str]:
    """
    Authenticate with Salesforce OAuth2.
    Returns (access_token, instance_url).
    
    For demo/mock mode, returns placeholder values.
    """
    global _access_token, _instance_url
    
    # Check for mock/demo mode
    if _check_should_mock():
        logger.info("🔶 Running in MOCK mode - using demo Salesforce data")
        _access_token = "mock_access_token"
        _instance_url = "https://mock.salesforce.com"
        return _access_token, _instance_url
    
    config = get_salesforce_config()

    # Real authentication
    try:
        # Build OAuth payload based on auth type
        if config.auth_type == "client_credentials":
            # OAuth2 Client Credentials flow (more secure, no user credentials needed)
            payload = {
                "grant_type": "client_credentials",
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
            logger.info("🔐 Using OAuth2 Client Credentials flow")
        else:
            # OAuth2 Password flow (requires username + password + security token)
            payload = {
                "grant_type": "password",
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "username": config.username,
                "password": f"{config.password}{config.security_token}"
            }
            logger.info("🔐 Using OAuth2 Password flow")

        response = requests.post(config.login_url, data=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        _access_token = data["access_token"]
        _instance_url = data.get("instance_url") or config.instance_url

        logger.info(f"✅ Authenticated with Salesforce: {_instance_url}")
        logger.info(f"   Auth type: {config.auth_type}")
        logger.info(f"   Token: {_access_token[:20]}...")
        return _access_token, _instance_url

    except Exception as e:
        logger.warning(f"⚠️ Salesforce auth failed, falling back to MOCK mode: {e}")
        _access_token = "mock_access_token"
        _instance_url = "https://mock.salesforce.com"
        return _access_token, _instance_url


def _get_headers() -> dict:
    """Get authorization headers for API calls."""
    if not _access_token:
        authenticate()
    return {
        "Authorization": f"Bearer {_access_token}",
        "Content-Type": "application/json"
    }


def _get_api_url() -> str:
    """Get the Salesforce API base URL."""
    if not _instance_url:
        authenticate()
    config = get_salesforce_config()
    return f"{_instance_url}/services/data/{config.api_version}"


def _is_mock_mode() -> bool:
    """Check if running in mock mode."""
    # Use the same logic as authentication check
    if _check_should_mock():
        return True
    # Also check if we authenticated in mock mode (fallback)
    return _access_token == "mock_access_token"


# ============================================================================
# Mock Data
# ============================================================================

MOCK_LEADS = [
    {
        "Id": "00Q5g00000MockLd1",
        "Name": "John Smith",
        "FirstName": "John",
        "LastName": "Smith",
        "Company": "Acme Corporation",
        "Email": "john.smith@acme.com",
        "Phone": "+1-555-0100",
        "Title": "VP of Engineering",
        "Industry": "Technology",
        "LeadSource": "Web",
        "Status": "New",
        "Rating": "Hot",
        "AnnualRevenue": 5000000,
        "NumberOfEmployees": 250,
        "Website": "https://acme.com",
        "Description": "Interested in enterprise solution",
        "OwnerId": "005UNASSIGNED0001",
        "CreatedDate": "2026-01-20T10:00:00.000+0000"
    },
    {
        "Id": "00Q5g00000MockLd2",
        "Name": "Jane Doe",
        "FirstName": "Jane",
        "LastName": "Doe",
        "Company": "TechStart Inc",
        "Email": "jane.doe@techstart.io",
        "Phone": "+1-555-0101",
        "Title": "Founder",
        "Industry": "Software",
        "LeadSource": "Partner",
        "Status": "New",
        "Rating": "Warm",
        "AnnualRevenue": 500000,
        "NumberOfEmployees": 15,
        "Website": "https://techstart.io",
        "Description": "Early stage evaluation",
        "OwnerId": "005UNASSIGNED0001",
        "CreatedDate": "2026-01-20T09:30:00.000+0000"
    },
    {
        "Id": "00Q5g00000MockLd3",
        "Name": "Bob Wilson",
        "FirstName": "Bob",
        "LastName": "Wilson",
        "Company": "Small Shop LLC",
        "Email": "bob@smallshop.com",
        "Phone": "+1-555-0102",
        "Title": "Owner",
        "Industry": "Retail",
        "LeadSource": "Cold Call",
        "Status": "New",
        "Rating": "Cold",
        "AnnualRevenue": 100000,
        "NumberOfEmployees": 5,
        "Website": "",
        "Description": "Just browsing",
        "OwnerId": "005UNASSIGNED0001",
        "CreatedDate": "2026-01-20T08:00:00.000+0000"
    }
]

MOCK_CASES = [
    {
        "Id": "5005g00000MockCs1",
        "CaseNumber": "00001234",
        "Subject": "How do I reset my password?",
        "Description": "I forgot my password and cannot log in to the system. Please help me reset it.",
        "Status": "New",
        "Priority": "Medium",
        "Origin": "Email",
        "Type": "Question",
        "Reason": "User Education",
        "ContactId": "0035g00000MockCn1",
        "AccountId": "0015g00000MockAc1",
        "OwnerId": "005UNASSIGNED0001",
        "CreatedDate": "2026-01-20T10:15:00.000+0000",
        "IsClosed": False,
        "IsEscalated": False
    },
    {
        "Id": "5005g00000MockCs2",
        "CaseNumber": "00001235",
        "Subject": "System is down - URGENT",
        "Description": "Our entire production system is not responding. Multiple users affected. Need immediate assistance!",
        "Status": "New",
        "Priority": "High",
        "Origin": "Phone",
        "Type": "Problem",
        "Reason": "Performance",
        "ContactId": "0035g00000MockCn2",
        "AccountId": "0015g00000MockAc2",
        "OwnerId": "005UNASSIGNED0001",
        "CreatedDate": "2026-01-20T10:30:00.000+0000",
        "IsClosed": False,
        "IsEscalated": False
    },
    {
        "Id": "5005g00000MockCs3",
        "CaseNumber": "00001236",
        "Subject": "Invoice discrepancy - billing issue",
        "Description": "We were charged $500 extra on our last invoice. Order #SAP-2024-1234. Please investigate.",
        "Status": "New",
        "Priority": "Medium",
        "Origin": "Web",
        "Type": "Problem",
        "Reason": "Billing",
        "ContactId": "0035g00000MockCn3",
        "AccountId": "0015g00000MockAc3",
        "OwnerId": "005UNASSIGNED0001",
        "CreatedDate": "2026-01-20T09:45:00.000+0000",
        "IsClosed": False,
        "IsEscalated": False
    },
    {
        "Id": "5005g00000MockCs4",
        "CaseNumber": "00001237",
        "Subject": "Security concern - unauthorized access attempt",
        "Description": "We noticed suspicious login attempts from unknown IP addresses. Please investigate immediately.",
        "Status": "New",
        "Priority": "High",
        "Origin": "Email",
        "Type": "Problem",
        "Reason": "Security",
        "ContactId": "0035g00000MockCn4",
        "AccountId": "0015g00000MockAc4",
        "OwnerId": "005UNASSIGNED0001",
        "CreatedDate": "2026-01-20T10:00:00.000+0000",
        "IsClosed": False,
        "IsEscalated": False
    }
]


# ============================================================================
# Lead Operations
# ============================================================================

def get_new_leads(limit: int = 10) -> list[dict]:
    """
    Fetch new leads from Salesforce.
    
    Args:
        limit: Maximum number of leads to return
        
    Returns:
        List of Lead records
    """
    logger.info(f"Fetching new leads (limit={limit})")
    
    if _is_mock_mode():
        logger.info(f"[MOCK] Returning {len(MOCK_LEADS)} mock leads")
        return MOCK_LEADS[:limit]
    
    query = f"""
        SELECT Id, Name, FirstName, LastName, Company, Email, Phone, 
               Title, Industry, LeadSource, Status, Rating, 
               AnnualRevenue, NumberOfEmployees, Website, Description,
               OwnerId, CreatedDate
        FROM Lead 
        WHERE Status = 'New' 
        ORDER BY CreatedDate DESC 
        LIMIT {limit}
    """
    
    url = f"{_get_api_url()}/query"
    response = requests.get(
        url,
        headers=_get_headers(),
        params={"q": query},
        timeout=30
    )
    response.raise_for_status()
    
    records = response.json().get("records", [])
    logger.info(f"Retrieved {len(records)} new leads")
    return records


def get_lead_by_id(lead_id: str) -> Optional[dict]:
    """
    Fetch a specific lead by ID.
    
    Args:
        lead_id: Salesforce Lead ID
        
    Returns:
        Lead record or None
    """
    logger.info(f"Fetching lead: {lead_id}")
    
    if _is_mock_mode():
        for lead in MOCK_LEADS:
            if lead["Id"] == lead_id:
                return lead
        return MOCK_LEADS[0] if MOCK_LEADS else None
    
    url = f"{_get_api_url()}/sobjects/Lead/{lead_id}"
    response = requests.get(url, headers=_get_headers(), timeout=30)
    
    if response.status_code == 404:
        return None
    response.raise_for_status()
    
    return response.json()


def update_lead_status(lead_id: str, status: str) -> dict:
    """
    Update a lead's status.
    
    Args:
        lead_id: Salesforce Lead ID
        status: New status value
        
    Returns:
        Operation result
    """
    status = _sanitize_text(status)
    logger.info(f"Updating lead {lead_id} status to: {status}")
    
    if _is_mock_mode():
        logger.info(f"[MOCK] Lead {lead_id} status updated to {status}")
        return {"success": True, "id": lead_id, "status": status}
    
    url = f"{_get_api_url()}/sobjects/Lead/{lead_id}"
    response = requests.patch(
        url,
        headers=_get_headers(),
        json={"Status": status},
        timeout=30
    )
    response.raise_for_status()
    
    return {"success": True, "id": lead_id, "status": status}


def update_lead(lead_id: str, fields: dict) -> dict:
    """
    Update a lead with arbitrary fields.

    Args:
        lead_id: Salesforce Lead ID
        fields: Dictionary of field names and values to update

    Returns:
        Operation result
    """
    logger.info(f"Updating lead {lead_id} with fields: {list(fields.keys())}")

    if _is_mock_mode():
        logger.info(f"[MOCK] Lead {lead_id} updated with {len(fields)} fields")
        return {"success": True, "id": lead_id, "fields_updated": list(fields.keys())}

    # Sanitize text fields
    sanitized_fields = {}
    for key, value in fields.items():
        if isinstance(value, str):
            sanitized_fields[key] = _sanitize_text(value)
        else:
            sanitized_fields[key] = value

    url = f"{_get_api_url()}/sobjects/Lead/{lead_id}"
    response = requests.patch(
        url,
        headers=_get_headers(),
        json=sanitized_fields,
        timeout=30
    )
    response.raise_for_status()

    return {"success": True, "id": lead_id, "fields_updated": list(fields.keys())}


def create_lead(lead_data: dict) -> dict:
    """
    Create a new Lead in Salesforce.

    Args:
        lead_data: Dictionary with lead fields. Required: LastName, Company.
                   Optional: FirstName, Email, Phone, Title, Industry, etc.

    Returns:
        Created lead with Id
    """
    logger.info(f"Creating new lead: {lead_data.get('LastName', 'Unknown')} at {lead_data.get('Company', 'Unknown')}")

    if _is_mock_mode():
        import random
        mock_id = f"00Q{random.randint(100000000000, 999999999999)}MOCK"
        logger.info(f"[MOCK] Created lead {mock_id}")
        return {"success": True, "id": mock_id, "created": True, **lead_data, "Id": mock_id}

    # Sanitize text fields
    sanitized_data = {}
    for key, value in lead_data.items():
        if key == "Id":  # Skip Id field for creation
            continue
        if isinstance(value, str):
            sanitized_data[key] = _sanitize_text(value)
        else:
            sanitized_data[key] = value

    # Ensure required fields
    if "LastName" not in sanitized_data:
        sanitized_data["LastName"] = "Unknown"
    if "Company" not in sanitized_data:
        sanitized_data["Company"] = "Unknown Company"

    url = f"{_get_api_url()}/sobjects/Lead"
    response = requests.post(
        url,
        headers=_get_headers(),
        json=sanitized_data,
        timeout=30
    )
    response.raise_for_status()

    result = response.json()
    new_id = result.get("id")
    logger.info(f"Created lead with ID: {new_id}")

    return {"success": True, "id": new_id, "created": True, **lead_data, "Id": new_id}


def lead_exists(lead_id: str) -> bool:
    """
    Check if a Lead exists in Salesforce.

    Args:
        lead_id: Salesforce Lead ID

    Returns:
        True if lead exists, False otherwise
    """
    if _is_mock_mode():
        # In mock mode, assume lead exists if ID looks valid
        return lead_id and lead_id.startswith("00Q") and "MOCK" not in lead_id

    try:
        url = f"{_get_api_url()}/sobjects/Lead/{lead_id}"
        response = requests.get(url, headers=_get_headers(), timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Error checking if lead exists: {e}")
        return False


def assign_owner(object_id: str, owner_id: str, object_type: str = "Lead") -> dict:
    """
    Assign an owner to a Salesforce object.
    
    Args:
        object_id: Salesforce object ID
        owner_id: New owner User ID
        object_type: Object type (Lead, Case, etc.)
        
    Returns:
        Operation result
    """
    logger.info(f"Assigning {object_type} {object_id} to owner: {owner_id}")
    
    if _is_mock_mode():
        logger.info(f"[MOCK] {object_type} {object_id} assigned to {owner_id}")
        return {"success": True, "id": object_id, "owner_id": owner_id}
    
    url = f"{_get_api_url()}/sobjects/{object_type}/{object_id}"
    response = requests.patch(
        url,
        headers=_get_headers(),
        json={"OwnerId": owner_id},
        timeout=30
    )
    response.raise_for_status()
    
    return {"success": True, "id": object_id, "owner_id": owner_id}


def create_task(related_id: str, description: str, subject: str = "Follow-up Task") -> dict:
    """
    Create a task related to a lead or other object.
    
    Args:
        related_id: ID of the related object (Lead, Contact, etc.)
        description: Task description
        subject: Task subject
        
    Returns:
        Created task details
    """
    description = _sanitize_text(description)
    subject = _sanitize_text(subject)
    logger.info(f"Creating task for {related_id}: {subject}")
    
    if _is_mock_mode():
        task_id = f"00T5g00000Mock{related_id[-4:]}"
        logger.info(f"[MOCK] Created task {task_id}")
        return {"success": True, "id": task_id, "subject": subject}
    
    task_data = {
        "Subject": subject,
        "Description": description,
        "WhoId": related_id if related_id.startswith("00Q") else None,  # Lead
        "WhatId": related_id if not related_id.startswith("00Q") else None,  # Other
        "Status": "Not Started",
        "Priority": "Normal"
    }
    # Remove None values
    task_data = {k: v for k, v in task_data.items() if v is not None}
    
    url = f"{_get_api_url()}/sobjects/Task"
    response = requests.post(
        url,
        headers=_get_headers(),
        json=task_data,
        timeout=30
    )
    response.raise_for_status()
    
    result = response.json()
    return {"success": True, "id": result.get("id"), "subject": subject}


# ============================================================================
# Case Operations
# ============================================================================

def get_new_cases(limit: int = 10) -> list[dict]:
    """
    Fetch new cases from Salesforce.
    
    Args:
        limit: Maximum number of cases to return
        
    Returns:
        List of Case records
    """
    logger.info(f"Fetching new cases (limit={limit})")
    
    if _is_mock_mode():
        logger.info(f"[MOCK] Returning {len(MOCK_CASES)} mock cases")
        return MOCK_CASES[:limit]
    
    query = f"""
        SELECT Id, CaseNumber, Subject, Description, Status, Priority,
               Origin, Type, Reason, ContactId, AccountId, OwnerId,
               CreatedDate, ClosedDate, IsClosed, IsEscalated
        FROM Case 
        WHERE Status = 'New' 
        ORDER BY CreatedDate DESC 
        LIMIT {limit}
    """
    
    url = f"{_get_api_url()}/query"
    response = requests.get(
        url,
        headers=_get_headers(),
        params={"q": query},
        timeout=30
    )
    response.raise_for_status()
    
    records = response.json().get("records", [])
    logger.info(f"Retrieved {len(records)} new cases")
    return records


def get_case_by_id(case_id: str) -> Optional[dict]:
    """
    Fetch a specific case by ID.
    
    Args:
        case_id: Salesforce Case ID
        
    Returns:
        Case record or None
    """
    logger.info(f"Fetching case: {case_id}")
    
    if _is_mock_mode():
        for case in MOCK_CASES:
            if case["Id"] == case_id:
                return case
        return MOCK_CASES[0] if MOCK_CASES else None
    
    url = f"{_get_api_url()}/sobjects/Case/{case_id}"
    response = requests.get(url, headers=_get_headers(), timeout=30)
    
    if response.status_code == 404:
        return None
    response.raise_for_status()
    
    return response.json()


def post_case_comment(case_id: str, text: str) -> dict:
    """
    Post a comment to a case.

    Args:
        case_id: Salesforce Case ID
        text: Comment text

    Returns:
        Created comment details (or error info if case doesn't exist)
    """
    text = _sanitize_text(text)
    logger.info(f"Posting comment to case {case_id}")

    if _is_mock_mode():
        comment_id = f"00a5g00000Mock{case_id[-4:]}"
        logger.info(f"[MOCK] Posted comment {comment_id}")
        return {"success": True, "id": comment_id, "case_id": case_id}

    try:
        url = f"{_get_api_url()}/sobjects/CaseComment"
        response = requests.post(
            url,
            headers=_get_headers(),
            json={
                "ParentId": case_id,
                "CommentBody": text,
                "IsPublished": True
            },
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        return {"success": True, "id": result.get("id"), "case_id": case_id}

    except requests.exceptions.HTTPError as e:
        # Case might not exist in Salesforce - log but don't fail
        logger.warning(f"⚠️ Failed to post comment to case {case_id}: {e}")
        logger.warning(f"   This is OK if the case was created externally (not in Salesforce)")
        return {
            "success": False,
            "error": str(e),
            "case_id": case_id,
            "message": "Case may not exist in Salesforce - comment not posted"
        }


def update_case(case_id: str, fields: dict) -> dict:
    """
    Update case fields.
    
    Args:
        case_id: Salesforce Case ID
        fields: Dictionary of fields to update
        
    Returns:
        Operation result
    """
    # Sanitize text fields
    sanitized = {}
    for key, value in fields.items():
        if isinstance(value, str):
            sanitized[key] = _sanitize_text(value)
        else:
            sanitized[key] = value
    
    logger.info(f"Updating case {case_id}: {list(sanitized.keys())}")
    
    if _is_mock_mode():
        logger.info(f"[MOCK] Case {case_id} updated: {sanitized}")
        return {"success": True, "id": case_id, "updated_fields": list(sanitized.keys())}
    
    url = f"{_get_api_url()}/sobjects/Case/{case_id}"
    response = requests.patch(
        url,
        headers=_get_headers(),
        json=sanitized,
        timeout=30
    )
    response.raise_for_status()
    
    return {"success": True, "id": case_id, "updated_fields": list(sanitized.keys())}
