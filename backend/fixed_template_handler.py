#!/usr/bin/env python3

def create_compatible_template():
    """Template that supports both 'amount' and 'total' fields"""
    return {
        "source_filename": None, 
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
        "campaign_name": None,  # Added for Facebook
        "total": None,          # Original field
        "amount": None,         # Alternative field
        "description": None,
        "quantity": None,       # Added for Google
        "filename": None        # Added for compatibility
    }

def normalize_record(record):
    """Normalize record to ensure amount is in the right field"""
    
    # Create compatible template
    template = create_compatible_template()
    
    # Apply record data to template
    for key, value in record.items():
        if key in template:
            template[key] = value
    
    # Normalize amount fields
    if template["amount"] is not None and template["total"] is None:
        template["total"] = template["amount"]
    elif template["total"] is not None and template["amount"] is None:
        template["amount"] = template["total"]
    
    # Ensure we have a numeric amount
    amount_value = template["amount"] or template["total"] or 0
    try:
        amount_value = float(amount_value)
        template["amount"] = amount_value
        template["total"] = amount_value
    except (ValueError, TypeError):
        template["amount"] = 0
        template["total"] = 0
    
    # Set filename if not present
    if template["filename"] is None and template["source_filename"] is not None:
        template["filename"] = template["source_filename"]
    
    return template

def test_record_normalization():
    """Test the record normalization"""
    
    # Test Google record format
    google_record = {
        "platform": "Google",
        "invoice_type": "Non-AP", 
        "campaign_id": "pkABC_123",
        "description": "การคลิก",
        "quantity": 902,
        "amount": 17991.76,  # Google uses 'amount'
        "filename": "test.pdf"
    }
    
    # Test Facebook record format
    facebook_record = {
        "platform": "Facebook",
        "invoice_type": "Non-AP",
        "campaign_name": "Test Campaign",
        "description": "Test Description", 
        "total": 18000.0,  # Facebook uses 'total'
        "filename": "test.pdf"
    }
    
    print("TESTING RECORD NORMALIZATION")
    print("=" * 40)
    
    # Test Google
    normalized_google = normalize_record(google_record)
    print(f"Google record:")
    print(f"  Original amount: {google_record.get('amount')}")
    print(f"  Normalized amount: {normalized_google['amount']}")
    print(f"  Normalized total: {normalized_google['total']}")
    
    # Test Facebook  
    normalized_facebook = normalize_record(facebook_record)
    print(f"\nFacebook record:")
    print(f"  Original total: {facebook_record.get('total')}")
    print(f"  Normalized amount: {normalized_facebook['amount']}")
    print(f"  Normalized total: {normalized_facebook['total']}")

if __name__ == "__main__":
    test_record_normalization()