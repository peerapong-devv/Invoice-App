#!/usr/bin/env python3
"""
Fixed template handler for normalizing invoice records
Ensures all parsers return consistent data structure
"""

from typing import Dict, Any, Optional


def create_unified_template() -> Dict[str, Optional[Any]]:
    """Create the unified template structure for all invoice records"""
    return {
        "platform": None,
        "invoice_type": None,
        "invoice_id": None,
        "line_number": None,
        "agency": None,
        "project_id": None,
        "project_name": None,
        "objective": None,
        "period": None,
        "campaign_id": None,
        "total": None,
        "description": None,
        "amount": None,  # Added for consistency
        "filename": None,
        "invoice_number": None
    }


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a record to ensure it has all required fields
    
    Args:
        record: Raw record from any parser
        
    Returns:
        Normalized record with all template fields
    """
    # Start with the template
    normalized = create_unified_template()
    
    # Map common field variations
    field_mappings = {
        # Handle different naming conventions
        'amount': ['amount', 'total', 'line_amount', 'item_amount'],
        'total': ['total', 'amount', 'total_amount', 'invoice_total'],
        'invoice_id': ['invoice_id', 'invoice_number', 'invoice_no'],
        'invoice_number': ['invoice_number', 'invoice_id', 'invoice_no'],
        'description': ['description', 'desc', 'item_description', 'line_description'],
        'platform': ['platform', 'source', 'provider'],
        'invoice_type': ['invoice_type', 'type', 'inv_type'],
        'line_number': ['line_number', 'line_no', 'row_number', 'item_number'],
        'agency': ['agency', 'agency_name', 'agency_code'],
        'project_id': ['project_id', 'proj_id', 'project_code'],
        'project_name': ['project_name', 'proj_name', 'project'],
        'objective': ['objective', 'campaign_objective', 'goal'],
        'period': ['period', 'billing_period', 'date_range'],
        'campaign_id': ['campaign_id', 'camp_id', 'campaign_code'],
        'filename': ['filename', 'file_name', 'source_file']
    }
    
    # Copy values from record to normalized structure
    for target_field, source_fields in field_mappings.items():
        for source_field in source_fields:
            if source_field in record and record[source_field] is not None:
                normalized[target_field] = record[source_field]
                break
    
    # Handle any fields not in mappings (direct copy)
    for key, value in record.items():
        if key in normalized and normalized[key] is None:
            normalized[key] = value
    
    # Ensure numeric fields are properly typed
    if normalized['amount'] is not None:
        try:
            normalized['amount'] = float(normalized['amount'])
        except (ValueError, TypeError):
            normalized['amount'] = 0.0
            
    if normalized['total'] is not None:
        try:
            normalized['total'] = float(normalized['total'])
        except (ValueError, TypeError):
            normalized['total'] = 0.0
    
    # If total is missing but amount exists, use amount as total
    if normalized['total'] is None and normalized['amount'] is not None:
        normalized['total'] = normalized['amount']
    
    # If amount is missing but total exists, use total as amount
    if normalized['amount'] is None and normalized['total'] is not None:
        normalized['amount'] = normalized['total']
    
    # Ensure line_number is an integer if present
    if normalized['line_number'] is not None:
        try:
            normalized['line_number'] = int(normalized['line_number'])
        except (ValueError, TypeError):
            normalized['line_number'] = None
    
    # Clean up None values for string fields (replace with empty string)
    string_fields = ['description', 'platform', 'invoice_type', 'agency', 
                     'project_name', 'objective', 'period', 'filename']
    for field in string_fields:
        if normalized[field] is None:
            normalized[field] = ''
    
    # Ensure platform is set
    if not normalized['platform']:
        # Try to detect from filename or other fields
        if normalized['filename']:
            filename_lower = normalized['filename'].lower()
            if 'thtt' in filename_lower or 'tiktok' in filename_lower:
                normalized['platform'] = 'TikTok'
            elif filename_lower.startswith('5') or 'google' in filename_lower:
                normalized['platform'] = 'Google'
            elif filename_lower.startswith('24') or 'facebook' in filename_lower:
                normalized['platform'] = 'Facebook'
            else:
                normalized['platform'] = 'Unknown'
        else:
            normalized['platform'] = 'Unknown'
    
    return normalized


def normalize_records(records: list) -> list:
    """
    Normalize a list of records
    
    Args:
        records: List of raw records from parser
        
    Returns:
        List of normalized records
    """
    if not records:
        return []
        
    return [normalize_record(record) for record in records]


if __name__ == "__main__":
    # Test the normalizer
    test_record = {
        'amount': 1234.56,
        'desc': 'Test campaign',
        'invoice_no': 'INV001',
        'line_no': '1'
    }
    
    normalized = normalize_record(test_record)
    print("Test normalization:")
    for key, value in normalized.items():
        if value:
            print(f"  {key}: {value}")