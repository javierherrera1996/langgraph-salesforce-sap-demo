"""
SAP OData API Tools
Pure functions for SAP operations - supports real and mock modes.
Follows SAP OData conventions and response formats.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
import random

import requests

from src.config import get_sap_config

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration and Authentication
# ============================================================================

_csrf_token: Optional[str] = None
_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    """Get or create an authenticated session."""
    global _session, _csrf_token
    
    config = get_sap_config()
    
    if config.is_mock:
        logger.info("SAP running in MOCK mode")
        return requests.Session()
    
    if _session is None:
        _session = requests.Session()
        _session.auth = (config.username, config.password)
        _session.headers.update({
            "sap-client": config.client,
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        # Fetch CSRF token
        response = _session.head(
            f"{config.base_url}/API_BUSINESS_PARTNER",
            headers={"X-CSRF-Token": "Fetch"},
            timeout=30
        )
        _csrf_token = response.headers.get("X-CSRF-Token")
        _session.headers["X-CSRF-Token"] = _csrf_token
        
        logger.info("SAP session established")
    
    return _session


def _get_base_url() -> str:
    """Get SAP OData base URL."""
    return get_sap_config().base_url


def _is_mock_mode() -> bool:
    """Check if running in mock mode."""
    return get_sap_config().is_mock


# ============================================================================
# Mock Data Generator
# ============================================================================

def _generate_mock_business_partner(company_name: str) -> dict:
    """Generate SAP-like business partner response."""
    bp_id = f"BP{abs(hash(company_name)) % 10000000:07d}"
    
    return {
        "d": {
            "__metadata": {
                "uri": f"/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_BusinessPartner('{bp_id}')",
                "type": "API_BUSINESS_PARTNER.A_BusinessPartnerType"
            },
            "BusinessPartner": bp_id,
            "BusinessPartnerFullName": company_name,
            "BusinessPartnerCategory": "2",  # Organization
            "BusinessPartnerGrouping": "BP01",
            "CreationDate": "/Date(1609459200000)/",
            "Industry": "TECH",
            "LegalForm": "0002",
            "OrganizationBPName1": company_name,
            "SearchTerm1": company_name[:20].upper(),
            "CreditRating": random.choice(["A", "A+", "B", "B+", "C"]),
            "PaymentTerms": random.choice(["NET30", "NET60", "NET90"]),
            "CustomerSince": "/Date(1577836800000)/",
            "AccountStatus": random.choice(["Active", "Active", "Active", "Review"]),
            "TotalRevenue": round(random.uniform(100000, 5000000), 2)
        }
    }


def _generate_mock_sales_orders(business_partner_id: str, count: int = 3) -> dict:
    """Generate SAP-like sales orders response."""
    orders = []
    base_date = datetime.now()
    
    for i in range(count):
        order_date = base_date - timedelta(days=random.randint(1, 365))
        order_id = f"SO{abs(hash(business_partner_id + str(i))) % 10000000:07d}"
        
        orders.append({
            "__metadata": {
                "uri": f"/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder('{order_id}')",
                "type": "API_SALES_ORDER_SRV.A_SalesOrderType"
            },
            "SalesOrder": order_id,
            "SalesOrderType": "OR",
            "SoldToParty": business_partner_id,
            "CreationDate": f"/Date({int(order_date.timestamp() * 1000)})/",
            "TotalNetAmount": str(round(random.uniform(1000, 100000), 2)),
            "TransactionCurrency": "USD",
            "OverallSDProcessStatus": random.choice(["A", "B", "C"]),
            "TotalBlockStatus": "",
            "OverallDeliveryStatus": random.choice(["A", "B", "C"]),
            "OverallBillingStatus": random.choice(["A", "B", "C"]),
            "RequestedDeliveryDate": f"/Date({int((order_date + timedelta(days=14)).timestamp() * 1000)})/"
        })
    
    return {
        "d": {
            "results": orders
        }
    }


def _generate_mock_service_orders(reference_id: str, count: int = 2) -> dict:
    """Generate SAP-like service orders response."""
    orders = []
    base_date = datetime.now()
    
    for i in range(count):
        order_date = base_date - timedelta(days=random.randint(1, 180))
        order_id = f"SVO{abs(hash(reference_id + str(i))) % 1000000:06d}"
        
        orders.append({
            "__metadata": {
                "uri": f"/sap/opu/odata/sap/API_SERVICE_ORDER_SRV/A_ServiceOrder('{order_id}')",
                "type": "API_SERVICE_ORDER_SRV.A_ServiceOrderType"
            },
            "ServiceOrder": order_id,
            "ServiceOrderType": "SM01",
            "ServiceOrderDescription": f"Service request #{i+1} for {reference_id}",
            "SoldToParty": reference_id,
            "ServiceOrderDate": f"/Date({int(order_date.timestamp() * 1000)})/",
            "ServiceOrderPriority": random.choice(["1", "2", "3"]),
            "ServiceObjectType": "EQUIPMENT",
            "ServiceOrderStatus": random.choice(["OPEN", "IN_PROCESS", "COMPLETED"]),
            "PlannedStartDateTime": f"/Date({int(order_date.timestamp() * 1000)})/",
            "PlannedEndDateTime": f"/Date({int((order_date + timedelta(hours=4)).timestamp() * 1000)})/"
        })
    
    return {
        "d": {
            "results": orders
        }
    }


# ============================================================================
# Business Partner Operations
# ============================================================================

def get_business_partner(company_name: str) -> Optional[dict]:
    """
    Retrieve business partner by company name.
    
    Args:
        company_name: Company name to search for
        
    Returns:
        SAP Business Partner data or None
    """
    logger.info(f"Fetching SAP business partner: {company_name}")
    
    if _is_mock_mode():
        bp_data = _generate_mock_business_partner(company_name)
        logger.info(f"[MOCK] Found BP: {bp_data['d']['BusinessPartner']}")
        return bp_data["d"]
    
    session = _get_session()
    url = f"{_get_base_url()}/API_BUSINESS_PARTNER/A_BusinessPartner"
    
    response = session.get(
        url,
        params={
            "$filter": f"startswith(BusinessPartnerFullName,'{company_name}')",
            "$top": 1,
            "$format": "json"
        },
        timeout=30
    )
    
    if response.status_code == 404:
        logger.warning(f"Business partner not found: {company_name}")
        return None
    
    response.raise_for_status()
    data = response.json()
    
    results = data.get("d", {}).get("results", [])
    if results:
        logger.info(f"Found BP: {results[0]['BusinessPartner']}")
        return results[0]
    
    return None


def get_sales_orders(business_partner_id: str, limit: int = 10) -> list[dict]:
    """
    Retrieve sales orders for a business partner.
    
    Args:
        business_partner_id: SAP Business Partner ID
        limit: Maximum orders to return
        
    Returns:
        List of sales orders
    """
    logger.info(f"Fetching sales orders for BP: {business_partner_id}")
    
    if _is_mock_mode():
        orders_data = _generate_mock_sales_orders(business_partner_id, min(limit, 5))
        orders = orders_data["d"]["results"]
        logger.info(f"[MOCK] Found {len(orders)} sales orders")
        return orders
    
    session = _get_session()
    url = f"{_get_base_url()}/API_SALES_ORDER_SRV/A_SalesOrder"
    
    response = session.get(
        url,
        params={
            "$filter": f"SoldToParty eq '{business_partner_id}'",
            "$top": limit,
            "$orderby": "CreationDate desc",
            "$format": "json"
        },
        timeout=30
    )
    response.raise_for_status()
    
    data = response.json()
    orders = data.get("d", {}).get("results", [])
    logger.info(f"Found {len(orders)} sales orders")
    return orders


def get_service_orders(reference_id: str, limit: int = 10) -> list[dict]:
    """
    Retrieve service orders by reference ID.
    
    Args:
        reference_id: Reference ID (can be BP ID or external reference)
        limit: Maximum orders to return
        
    Returns:
        List of service orders
    """
    logger.info(f"Fetching service orders for: {reference_id}")
    
    if _is_mock_mode():
        orders_data = _generate_mock_service_orders(reference_id, min(limit, 3))
        orders = orders_data["d"]["results"]
        logger.info(f"[MOCK] Found {len(orders)} service orders")
        return orders
    
    session = _get_session()
    url = f"{_get_base_url()}/API_SERVICE_ORDER_SRV/A_ServiceOrder"
    
    response = session.get(
        url,
        params={
            "$filter": f"SoldToParty eq '{reference_id}'",
            "$top": limit,
            "$orderby": "ServiceOrderDate desc",
            "$format": "json"
        },
        timeout=30
    )
    response.raise_for_status()
    
    data = response.json()
    orders = data.get("d", {}).get("results", [])
    logger.info(f"Found {len(orders)} service orders")
    return orders


def create_note(object_id: str, text: str, note_type: str = "GENERAL") -> dict:
    """
    Create a note/text on an SAP object.
    
    Args:
        object_id: SAP Object ID (BP, Sales Order, etc.)
        text: Note content
        note_type: Type of note (GENERAL, INTERNAL, EXTERNAL)
        
    Returns:
        Created note details
    """
    # Sanitize text
    text = text[:2000] if text else ""
    logger.info(f"Creating SAP note on {object_id}: {note_type}")
    
    if _is_mock_mode():
        note_id = f"NOTE{abs(hash(object_id + text)) % 100000:05d}"
        logger.info(f"[MOCK] Created note: {note_id}")
        return {
            "success": True,
            "note_id": note_id,
            "object_id": object_id,
            "note_type": note_type
        }
    
    session = _get_session()
    url = f"{_get_base_url()}/API_BUSINESS_PARTNER/A_BPContactToFuncAndDept"
    
    note_data = {
        "BusinessPartner": object_id,
        "NoteType": note_type,
        "NoteText": text,
        "CreatedByUser": get_sap_config().username,
        "CreationDateTime": f"/Date({int(datetime.now().timestamp() * 1000)})/"
    }
    
    response = session.post(
        url,
        json=note_data,
        timeout=30
    )
    response.raise_for_status()
    
    result = response.json()
    return {
        "success": True,
        "note_id": result.get("d", {}).get("NoteId"),
        "object_id": object_id,
        "note_type": note_type
    }


# ============================================================================
# Helper Functions for Data Extraction
# ============================================================================

def extract_enrichment_data(bp_data: Optional[dict], orders: list[dict]) -> dict:
    """
    Extract enrichment data from SAP responses for use in state.
    
    Args:
        bp_data: Business partner data
        orders: List of sales orders
        
    Returns:
        Enrichment dictionary compatible with EnrichedData type
    """
    if not bp_data:
        return {}
    
    # Calculate totals from orders
    total_revenue = 0.0
    for order in orders:
        try:
            amount = float(order.get("TotalNetAmount", 0))
            total_revenue += amount
        except (ValueError, TypeError):
            pass
    
    open_orders = sum(
        1 for o in orders 
        if o.get("OverallSDProcessStatus") in ("A", "B")  # In process
    )
    
    last_order_date = ""
    if orders:
        # SAP dates are in /Date(milliseconds)/ format
        try:
            date_str = orders[0].get("CreationDate", "")
            if "/Date(" in date_str:
                ms = int(date_str.replace("/Date(", "").replace(")/", ""))
                last_order_date = datetime.fromtimestamp(ms / 1000).isoformat()
        except (ValueError, TypeError):
            pass
    
    return {
        "business_partner_id": bp_data.get("BusinessPartner", ""),
        "business_partner_name": bp_data.get("BusinessPartnerFullName", ""),
        "credit_rating": bp_data.get("CreditRating", ""),
        "payment_terms": bp_data.get("PaymentTerms", ""),
        "total_orders": len(orders),
        "total_revenue": total_revenue,
        "last_order_date": last_order_date,
        "open_orders": open_orders,
        "customer_since": bp_data.get("CustomerSince", ""),
        "industry_segment": bp_data.get("Industry", ""),
        "account_status": bp_data.get("AccountStatus", "")
    }


def extract_order_context(sales_orders: list[dict], service_orders: list[dict]) -> dict:
    """
    Extract order context for ticket enrichment.
    
    Args:
        sales_orders: List of sales orders
        service_orders: List of service orders
        
    Returns:
        Order context dictionary compatible with SAPOrderContext type
    """
    total_value = 0.0
    for order in sales_orders:
        try:
            amount = float(order.get("TotalNetAmount", 0))
            total_value += amount
        except (ValueError, TypeError):
            pass
    
    has_open = any(
        o.get("OverallSDProcessStatus") in ("A", "B")
        for o in sales_orders
    ) or any(
        o.get("ServiceOrderStatus") in ("OPEN", "IN_PROCESS")
        for o in service_orders
    )
    
    bp_id = ""
    if sales_orders:
        bp_id = sales_orders[0].get("SoldToParty", "")
    elif service_orders:
        bp_id = service_orders[0].get("SoldToParty", "")
    
    return {
        "sales_orders": sales_orders,
        "service_orders": service_orders,
        "business_partner_id": bp_id,
        "has_open_orders": has_open,
        "total_order_value": total_value
    }
