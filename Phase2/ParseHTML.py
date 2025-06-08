import os
import glob
import re
import json
from bs4 import BeautifulSoup
from typing import Dict, List

class HMOHTMLParser:
    def __init__(self):
        self.hmo_mapping = {
            "maccabi": "מכבי",
            "meuhedet": "מאוחדת", 
            "clalit": "כללית",
            "מכבי": "מכבי",
            "מאוחדת": "מאוחדת",
            "כללית": "כללית"
        }
        
        self.tier_mapping = {
            "gold": "זהב",
            "silver": "כסף", 
            "bronze": "ארד",
            "זהב": "זהב",
            "כסף": "כסף",
            "ארד": "ארד"
        }
    
    def normalize_hmo_name(self, hmo_name: str) -> str:
        """Normalize HMO names"""
        return self.hmo_mapping.get(hmo_name.lower(), hmo_name)
    
    def normalize_tier(self, tier: str) -> str:
        """Normalize tier names"""
        return self.tier_mapping.get(tier.lower(), tier)
    
    def extract_table_data(self, soup: BeautifulSoup) -> Dict:
        """Extract structured benefits data from table"""
        benefits = {}
        
        table = soup.find('table')
        if not table:
            return benefits
        
        rows = table.find_all('tr')
        if len(rows) < 2:
            return benefits
        
        header_row = rows[0]
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        hmo_columns = {}
        for i, header in enumerate(headers[1:], 1):
            normalized_hmo = self.normalize_hmo_name(header)
            if normalized_hmo in ["מכבי", "מאוחדת", "כללית"]:
                hmo_columns[normalized_hmo] = i
        
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            treatment_name = cells[0].get_text(strip=True)
            
            for hmo, col_idx in hmo_columns.items():
                if col_idx < len(cells):
                    cell_content = cells[col_idx].get_text(separator='\n', strip=True)
                    tier_benefits = self.parse_tier_benefits(cell_content)
                    
                    if hmo not in benefits:
                        benefits[hmo] = {}
                    
                    benefits[hmo][treatment_name] = tier_benefits
        
        return benefits
    
    def parse_tier_benefits(self, cell_content: str) -> Dict:
        '''Parse benefits for each tier from a block of text.'''
        tier_benefits = {}
        lines = cell_content.split('\n')
        
        # Process lines in pairs - tier name on one line, benefits on next
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            tier_match = re.search(r'(זהב|כסף|ארד):', line)
            if tier_match:
                tier = tier_match.group(1)
                
                benefits_text = ""
                j = i + 1
                
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    
                    if re.search(r'(זהב|כסף|ארד):', next_line):
                        break
                    
                    benefits_text += next_line + " "
                    j += 1
                
                benefits_text = benefits_text.strip()
                
                if benefits_text:
                    # Extract details from the benefits text
                    discount_match = re.search(r'(\d+)%\s*הנחה', benefits_text)
                    limit_match = re.search(r'עד\s*(\d+)\s*טיפולים', benefits_text)
                    
                    tier_benefits[tier] = {
                        "discount": discount_match.group(1) + "%" if discount_match else "",
                        "annual_limit": limit_match.group(1) if limit_match else "",
                        "full_text": benefits_text
                    }
                
                i = j  
            else:
                i += 1
        
        return tier_benefits
    
     
    def extract_hmo_contact_in_context(self, text_content: str, hmo_patterns: List[str], service_category: str) -> Dict:
        """Extract contact info for specific HMO in service context"""
        
        contact_data = {}
        
        for pattern in hmo_patterns:
            hmo_pattern = rf'{pattern}[^:]*:?\s*([^\n]*(?:\*?\d{{4}}\*?|1-\d{{3}}-\d{{2}}-\d{{2}}-\d{{2}}|1-\d{{3}}-\d{{4}}|0\d-\d{{7}})[^\n]*)'
            
            matches = re.findall(hmo_pattern, text_content, re.IGNORECASE | re.MULTILINE)
            
            if matches:
                contact_line = matches[0].strip()
                
                parsed_contact = self.parse_contact_line(contact_line, service_category)
                if parsed_contact:
                    contact_data.update(parsed_contact)
                    break
        
        return contact_data
    
    def parse_contact_line(self, contact_line: str, service_category: str) -> Dict:
        """Parse individual contact line and add service context"""
        
        contact_data = {
            "service_category": service_category,
            "raw_contact_line": contact_line
        }
        
        phone_patterns = [
            r'\*(\d{4})\*?',
            r'(\d{4})\*',    
            r'(1-\d{3}-\d{2}-\d{2}-\d{2})', 
            r'(1-\d{3}-\d{4})',  
            r'(0\d-\d{7})',   
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, contact_line)
            phones.extend(matches)
        
        if phones:
            contact_data["phones"] = phones
            contact_data["primary_phone"] = phones[0]
        
        ext_patterns = [
            r'שלוחה\s*(\d+)',
            r'שלוחת\s*(\d+)', 
            r'ext\.?\s*(\d+)',
            r'תוסף\s*(\d+)'
        ]
        
        extensions = []
        for pattern in ext_patterns:
            matches = re.findall(pattern, contact_line)
            extensions.extend(matches)
        
        if extensions:
            contact_data["extensions"] = extensions
            contact_data["primary_extension"] = extensions[0]
        
        
        return contact_data
    
 
    
    def extract_contact_info(self, soup: BeautifulSoup) -> Dict:
        """Extract contact information with treatment/service context"""
        contact_info = {}
        
        page_title = ""
        title_tag = soup.find('h2') or soup.find('h1') or soup.find('title')
        if title_tag:
            page_title = title_tag.get_text(strip=True)
        
        service_category = page_title
        
        text_content = soup.get_text()

        hmo_patterns = {
            "מכבי": [r'מכבי', r'maccabi'],
            "מאוחדת": [r'מאוחדת', r'meuhedet'], 
            "כללית": [r'כללית', r'clalit']
        }
        
        for hmo, patterns in hmo_patterns.items():
            hmo_contact = self.extract_hmo_contact_in_context(
                text_content, patterns, service_category
            )
            if hmo_contact:
                contact_info[hmo] = hmo_contact
        
        return contact_info
    
    def extract_treatment_descriptions(self, soup: BeautifulSoup) -> Dict:
        """Extract treatment descriptions from lists"""
        descriptions = {}
        
        ul_elements = soup.find_all('ul')
        for ul in ul_elements:
            items = ul.find_all('li')
            for item in items:
                text = item.get_text(strip=True)
                if ':' in text:
                    name, desc = text.split(':', 1)
                    descriptions[name.strip()] = desc.strip()
        
        return descriptions
    
    def extract_general_description(self, soup: BeautifulSoup) -> str:
        """Extract general description of the service"""
        
        paragraphs = soup.find_all('p')
        if paragraphs:
            return ' '.join([p.get_text(strip=True) for p in paragraphs[:2]])
        return ""
    
    def parse_html_file(self, file_path: str) -> Dict:
        """Parse single HTML file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
        
        title = soup.find('h2')
        title_text = title.get_text(strip=True) if title else os.path.basename(file_path)
        
        description = self.extract_general_description(soup)
        
        return {
            "filename": os.path.basename(file_path),
            "title": title_text,
            "description": description,
            "benefits": self.extract_table_data(soup),
            "contacts": self.extract_contact_info(soup),
            "treatment_descriptions": self.extract_treatment_descriptions(soup)
        }
    
    def parse_all_files(self, html_folder: str) -> Dict:
        """Parse all HTML files in folder with combined structure"""
        
        all_data = {
            "benefits": {},
            "descriptions": {},
            "metadata": []
        }
        
        html_files = glob.glob(f"{html_folder}/*.html")
        
        for file_path in html_files:
            doc_data = self.parse_html_file(file_path)
            
            doc_title = doc_data["title"]
            
            for hmo, treatments in doc_data["benefits"].items():
                if hmo not in all_data["benefits"]:
                    all_data["benefits"][hmo] = {}
                
                service_key = f"{doc_title}"  
                
                if service_key not in all_data["benefits"][hmo]:
                    all_data["benefits"][hmo][service_key] = {
                        "title": doc_title,
                        "treatments": {}
                    }
                
                for treatment, tiers in treatments.items():
                    if treatment not in all_data["benefits"][hmo][service_key]["treatments"]:
                        all_data["benefits"][hmo][service_key]["treatments"][treatment] = {}
                    
                    all_data["benefits"][hmo][service_key]["treatments"][treatment].update(tiers)
                    
                    if "contacts" not in all_data["benefits"][hmo][service_key]["treatments"][treatment]:
                        all_data["benefits"][hmo][service_key]["treatments"][treatment]["contacts"] = {}
                    
                    if hmo in doc_data["contacts"]:
                        all_data["benefits"][hmo][service_key]["treatments"][treatment]["contacts"][hmo] = doc_data["contacts"][hmo]
            
            all_data["descriptions"].update(doc_data["treatment_descriptions"])
            
            all_data["metadata"].append({
                "filename": doc_data["filename"],
                "title": doc_data["title"],
                "description": doc_data["description"]
            })
        
        return all_data
    
    def save_parsed_data(self, data: Dict, output_file: str = "parsed_hmo_data.json"):
        """Save parsed data to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Parsed data saved to {output_file}")
    
if __name__ == "__main__":
    parser = HMOHTMLParser()
    
    data = parser.parse_all_files("phase2_data")
    
    parser.save_parsed_data(data)
    