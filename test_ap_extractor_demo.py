#!/usr/bin/env python3
"""
Demo script to test the AP invoice extractor with real Facebook invoice data
"""
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class APInvoiceData:
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    campaign_id: Optional[str] = None
    objective: Optional[str] = None
    period: Optional[str] = None
    platform: Optional[str] = None
    ad_type: Optional[str] = None
    targeting: Optional[str] = None
    creative_type: Optional[str] = None
    description: str = ""
    total: float = 0.0
    confidence: float = 0.0

class FacebookAPExtractor:
    
    OBJECTIVES = ['Awareness', 'Conversion', 'Traffic', 'LeadAd', 'Reach']
    PLATFORMS = ['Instagram', 'Facebook', 'Messenger']
    AD_TYPES = ['VDO', 'carousel', 'video', 'stories', 'reels', 'static']
    
    # Period patterns
    PERIOD_PATTERNS = [
        r'Q[1-4]Y\d{2}',  # Q2Y25
        r'[A-Z]{3,4}Y?\d{2}',  # MAYY25, MAY25
        r'\d{1,2}-?\w{3}-?\d{2,4}',  # 16-May, 1MAY25
        r'\d{8}',  # 20250225
    ]
    
    def extract_ap_data(self, description: str, total: float = 0.0) -> APInvoiceData:
        """Extract structured data from AP invoice description"""
        
        # Initialize result
        result = APInvoiceData(description=description, total=total)
        
        # Check if this is an AP invoice (contains [ST])
        if '[ST]' not in description:
            result.confidence = 0.0
            return result
        
        # Extract platform
        result.platform = self._extract_platform(description)
        
        # Main AP pattern: pk|{project_id}|{complex_part}[ST]|{campaign_id}
        ap_pattern = r'pk\|([^|]+)\|([^[]+)\[ST\]\|([^|\s]+)'
        match = re.search(ap_pattern, description)
        
        if not match:
            result.confidence = 0.1
            return result
        
        project_id, complex_part, campaign_id = match.groups()
        result.project_id = project_id.strip()
        result.campaign_id = campaign_id.strip()
        
        # Parse complex middle part
        self._parse_complex_part(complex_part, result)
        
        # Calculate confidence score
        result.confidence = self._calculate_confidence(result)
        
        return result
    
    def _extract_platform(self, description: str) -> Optional[str]:
        """Extract platform from description"""
        desc_lower = description.lower()
        for platform in self.PLATFORMS:
            if platform.lower() in desc_lower:
                return platform
        return None
    
    def _parse_complex_part(self, complex_part: str, result: APInvoiceData):
        """Parse the complex middle part of AP invoice"""
        
        # Clean up the complex part
        parts = complex_part.strip().split('_')
        
        # Extract project name (usually at the beginning)
        project_name_parts = []
        for part in parts:
            if any(obj.lower() in part.lower() for obj in self.OBJECTIVES):
                break
            if any(ad_type in part for ad_type in self.AD_TYPES):
                break
            if re.match(r'[A-Z]{2,}', part):  # All caps might be metadata
                break
            if part not in ['pk', 'th', 'none']:
                project_name_parts.append(part)
        
        if project_name_parts:
            result.project_name = '-'.join(project_name_parts)
        
        # Extract objective
        for obj in self.OBJECTIVES:
            if obj.lower() in complex_part.lower():
                result.objective = obj
                break
        
        # Extract period
        for pattern in self.PERIOD_PATTERNS:
            period_match = re.search(pattern, complex_part)
            if period_match:
                result.period = period_match.group(0)
                break
        
        # Extract ad type
        for ad_type in self.AD_TYPES:
            if ad_type in complex_part:
                result.ad_type = ad_type
                break
        
        # Extract creative type from CTA patterns
        if 'CTA_' in complex_part:
            cta_pattern = r'CTA_([A-Z0-9]+)'
            cta_match = re.search(cta_pattern, complex_part)
            if cta_match:
                result.creative_type = cta_match.group(1)
    
    def _calculate_confidence(self, result: APInvoiceData) -> float:
        """Calculate confidence score based on extracted data"""
        score = 0.0
        
        # Base score for having [ST] marker
        score += 0.3
        
        # Project ID and Campaign ID (essential)
        if result.project_id:
            score += 0.2
        if result.campaign_id:
            score += 0.2
        
        # Project name
        if result.project_name:
            score += 0.1
        
        # Objective
        if result.objective:
            score += 0.1
        
        # Period
        if result.period:
            score += 0.05
        
        # Platform
        if result.platform:
            score += 0.05
        
        return min(score, 1.0)

def test_with_real_data():
    """Test the extractor with real Facebook AP invoice data"""
    
    # Real data from the screenshot
    test_cases = [
        {
            'description': 'Instagram - pk|40022|SDH_pk_th-single-detached-house-centro-onnnut-suvarnabhumi_none_Awareness_VDO_FBAWARENESSQ2Y25_[ST]|2089P22',
            'total': 17.89
        },
        {
            'description': 'Instagram - pk|40022|SDH_pk_th-single-detached-house-centro-onnnut-suvarnabhumi_none_Conversion_CTA_FBCONQ2Y25_[ST]|2089P22',
            'total': 4984.62
        },
        {
            'description': 'Instagram - pk|40022|SDH_pk_th-single-detached-house-centro-onnnut-suvarnabhumi_none_LeadAd_CTA_CLOQ2Y25_[ST]|2089P22',
            'total': 6842.52
        },
        {
            'description': 'Instagram - pk|40022|SDH_pk_th-single-detached-house-centro-onnnut-suvarnabhumi_none_Traffic_CollectionCanvas_FBTRAFFICQ2Y25_[ST]|2089P22',
            'total': 0.02
        },
        {
            'description': 'Instagram - pk|40044|SDH_pk_th-single-detached-house-centro-bangna-kingkaew_none_Awareness_VDO_FBAWARENESSQ2Y25_[ST]|2089P01',
            'total': 66.79
        },
        {
            'description': 'Instagram - pk|40077|SDH_pk_th-single-detached-house-modern-bangna-theparak_none_Awareness_VDO_FBAWARENESSQ2Y25_[ST]|2089P47',
            'total': 44.28
        },
        {
            'description': 'Instagram - pk|40077|SDH_pk_th-single-detached-house-modern-bangna-theparak_none_Conversion_CTA_FBCONQ2Y25_[ST]|2089P47',
            'total': 2560.03
        },
        {
            'description': 'Instagram - pk|40089|SDH_pk_th-single-detached-house-centro-rama-9-motorway-2_none_Awareness_VDO_FBAWARENESSQ2Y25_[ST]|2089P08',
            'total': 320.46
        }
    ]
    
    extractor = FacebookAPExtractor()
    
    print("FACEBOOK AP INVOICE EXTRACTION TEST")
    print("=" * 60)
    
    total_amount = 0
    successful_extractions = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Original: {test_case['description']}")
        print(f"Amount: {test_case['total']:,.2f} THB")
        
        # Extract data
        result = extractor.extract_ap_data(test_case['description'], test_case['total'])
        
        if result.confidence > 0.5:
            successful_extractions += 1
        
        total_amount += test_case['total']
        
        # Display extracted data
        print("\nExtracted Data:")
        print(f"  Project ID: {result.project_id}")
        print(f"  Project Name: {result.project_name}")
        print(f"  Campaign ID: {result.campaign_id}")
        print(f"  Platform: {result.platform}")
        print(f"  Objective: {result.objective}")
        print(f"  Period: {result.period}")
        print(f"  Ad Type: {result.ad_type}")
        print(f"  Creative Type: {result.creative_type}")
        print(f"  Confidence: {result.confidence:.1%}")
        
        print("-" * 40)
    
    # Summary
    print(f"\nEXTRACTION SUMMARY")
    print(f"=" * 30)
    print(f"Total Cases: {len(test_cases)}")
    print(f"Successful Extractions: {successful_extractions}")
    print(f"Success Rate: {successful_extractions/len(test_cases):.1%}")
    print(f"Total Amount: {total_amount:,.2f} THB")
    
    # Analytics by category
    print(f"\nANALYTICS BREAKDOWN")
    print(f"=" * 30)
    
    # Group by objective
    objectives = {}
    projects = {}
    
    for test_case in test_cases:
        result = extractor.extract_ap_data(test_case['description'], test_case['total'])
        
        if result.objective:
            if result.objective not in objectives:
                objectives[result.objective] = {'count': 0, 'total': 0}
            objectives[result.objective]['count'] += 1
            objectives[result.objective]['total'] += test_case['total']
        
        if result.project_id:
            if result.project_id not in projects:
                projects[result.project_id] = {'count': 0, 'total': 0}
            projects[result.project_id]['count'] += 1
            projects[result.project_id]['total'] += test_case['total']
    
    print("\nBy Objective:")
    for obj, data in objectives.items():
        print(f"  {obj}: {data['count']} campaigns, {data['total']:,.2f} THB")
    
    print("\nBy Project:")
    for proj, data in projects.items():
        print(f"  Project {proj}: {data['count']} campaigns, {data['total']:,.2f} THB")

if __name__ == "__main__":
    test_with_real_data()