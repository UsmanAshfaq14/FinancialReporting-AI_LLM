import json
import csv
from datetime import datetime
from typing import Dict, List, Union, Optional
import io

class FinancialReportingSystem:
    def __init__(self):
        self.required_fields = ['month', 'revenue', 'currency', 'tax_rate']
        self.months_order = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }

    def validate_data_structure(self, data: List[Dict]) -> Dict:
        """Validate the data structure and required fields."""
        validation_report = {
            'data_format': 'JSON/CSV',
            'num_records': len(data),
            'field_checks': {},
            'data_type_checks': {},
            'is_valid': True,
            'error_message': None
        }

        # Check required fields
        for field in self.required_fields:
            missing_rows = [i for i, record in enumerate(data, 1) 
                          if field not in record]
            validation_report['field_checks'][field] = 'present' if not missing_rows else f'missing in rows {missing_rows}'
            if missing_rows:
                validation_report['is_valid'] = False
                validation_report['error_message'] = f"ERROR: Missing required field(s): {field} at row(s) {missing_rows}"
                return validation_report

        # Validate data types and values
        for i, record in enumerate(data, 1):
            # Validate revenue
            try:
                revenue = float(record['revenue'])
                if revenue < 0:
                    validation_report['data_type_checks']['revenue'] = 'invalid (negative)'
                    validation_report['is_valid'] = False
                    validation_report['error_message'] = f"ERROR: Invalid value for revenue at row {i}: must be non-negative"
                    return validation_report
            except ValueError:
                validation_report['data_type_checks']['revenue'] = 'invalid (non-numeric)'
                validation_report['is_valid'] = False
                validation_report['error_message'] = f"ERROR: Invalid data type for revenue at row {i}"
                return validation_report

            # Validate tax_rate
            try:
                tax_rate = float(record['tax_rate'])
                if not 0 <= tax_rate <= 100:
                    validation_report['data_type_checks']['tax_rate'] = 'invalid (out of range)'
                    validation_report['is_valid'] = False
                    validation_report['error_message'] = f"ERROR: Invalid value for tax_rate at row {i}: must be between 0 and 100"
                    return validation_report
            except ValueError:
                validation_report['data_type_checks']['tax_rate'] = 'invalid (non-numeric)'
                validation_report['is_valid'] = False
                validation_report['error_message'] = f"ERROR: Invalid data type for tax_rate at row {i}"
                return validation_report

            # Validate conversion_rate if currency is not USD
            if record['currency'].upper() != 'USD':
                if 'conversion_rate' not in record:
                    validation_report['field_checks']['conversion_rate'] = f'missing for non-USD currency at row {i}'
                    validation_report['is_valid'] = False
                    validation_report['error_message'] = f"ERROR: Missing conversion_rate for non-USD currency at row {i}"
                    return validation_report
                try:
                    conv_rate = float(record['conversion_rate'])
                    if conv_rate <= 0:
                        validation_report['data_type_checks']['conversion_rate'] = 'invalid (not positive)'
                        validation_report['is_valid'] = False
                        validation_report['error_message'] = f"ERROR: Invalid value for conversion_rate at row {i}: must be positive"
                        return validation_report
                except ValueError:
                    validation_report['data_type_checks']['conversion_rate'] = 'invalid (non-numeric)'
                    validation_report['is_valid'] = False
                    validation_report['error_message'] = f"ERROR: Invalid data type for conversion_rate at row {i}"
                    return validation_report

        validation_report['data_type_checks'] = {
            'revenue': 'valid',
            'tax_rate': 'valid',
            'conversion_rate': 'valid'
        }
        return validation_report

    def process_data(self, data: List[Dict]) -> Dict:
        """Process the financial data and generate analysis."""
        # Sort data by month
        sorted_data = sorted(data, key=lambda x: self.months_order[x['month'].lower()])
        processed_results = []
        
        prev_adjusted_revenue = None
        for record in sorted_data:
            # Step 1: Currency Conversion
            revenue = float(record['revenue'])
            if record['currency'].upper() != 'USD':
                conversion_rate = float(record['conversion_rate'])
                converted_revenue = revenue * conversion_rate
            else:
                converted_revenue = revenue
                conversion_rate = 1.0

            # Step 2: Tax Adjustment
            tax_rate = float(record['tax_rate'])
            adjusted_revenue = converted_revenue * (1 - tax_rate/100)

            # Step 3: Percentage Growth
            if prev_adjusted_revenue is not None:
                growth = ((adjusted_revenue - prev_adjusted_revenue) / prev_adjusted_revenue) * 100
            else:
                growth = None

            processed_results.append({
                'month': record['month'],
                'input_data': {
                    'revenue': revenue,
                    'currency': record['currency'],
                    'tax_rate': tax_rate,
                    'conversion_rate': conversion_rate
                },
                'calculations': {
                    'converted_revenue': round(converted_revenue, 2),
                    'adjusted_revenue': round(adjusted_revenue, 2),
                    'percentage_growth': round(growth, 2) if growth is not None else 'N/A'
                }
            })
            
            prev_adjusted_revenue = adjusted_revenue

        return {
            'total_records': len(processed_results),
            'results': processed_results
        }

    def generate_report(self, data: List[Dict]) -> str:
        """Generate the final report in markdown format with LaTeX formulas."""
        validation_results = self.validate_data_structure(data)
        if not validation_results['is_valid']:
            return validation_results['error_message']

        processed_data = self.process_data(data)
        
        report = [
            "# Data Validation Report",
            "## 1. Data Structure Check:",
            f"- Data format: {validation_results['data_format']}",
            f"- Number of records: {validation_results['num_records']}",
            "",
            "## 2. Required Fields Check:",
        ]

        for field, status in validation_results['field_checks'].items():
            report.append(f"- {field}: {status}")

        report.extend([
            "",
            "## 3. Data Type & Value Validation:",
            f"- revenue (non-negative): {validation_results['data_type_checks']['revenue']}",
            f"- tax_rate (0 to 100): {validation_results['data_type_checks']['tax_rate']}",
            f"- conversion_rate (if required, positive): {validation_results['data_type_checks']['conversion_rate']}",
            "",
            "## Validation Summary:",
            "Data validation is successful! Proceeding with analysis...",
            "",
            "# Formulas Used:",
            "1. **Currency Conversion:**  ",
            "   $\\text{Converted Revenue} = \\text{revenue} \\times \\text{conversion_rate}$",
            "2. **Tax Adjustment:**  ",
            "   $\\text{Adjusted Revenue} = \\text{Converted Revenue} \\times \\left(1 - \\frac{\\text{tax_rate}}{100}\\right)$",
            "3. **Percentage Growth:**  ",
            "   $\\text{Percentage Growth} = \\left(\\frac{\\text{Adjusted Revenue}_{\\text{current}} - \\text{Adjusted Revenue}_{\\text{previous}}}{\\text{Adjusted Revenue}_{\\text{previous}}}\\right) \\times 100$",
            "",
            "# Revenue Dataset Transformation Report",
            f"Total Records Evaluated: {processed_data['total_records']}"
        ])

        for result in processed_data['results']:
            report.extend([
                "",
                f"## Record for Month: {result['month']}",
                "### Input Data:",
                f"- Revenue: {result['input_data']['revenue']}",
                f"- Currency: {result['input_data']['currency']}",
                f"- Tax Rate: {result['input_data']['tax_rate']}%",
                f"- Conversion Rate: {result['input_data']['conversion_rate']}",
                "",
                "### Step-by-Step Calculations:",
                "1. **Currency Conversion:**",
                f"   ${result['calculations']['converted_revenue']} = {result['input_data']['revenue']} \\times {result['input_data']['conversion_rate']}$",
                "",
                "2. **Tax Adjustment:**",
                f"   ${result['calculations']['adjusted_revenue']} = {result['calculations']['converted_revenue']} \\times (1 - {result['input_data']['tax_rate']}/100)$",
                "",
                "3. **Percentage Growth:**",
                f"   {result['calculations']['percentage_growth']}%",
                "",
                f"### Final Transformed Data for {result['month']}:",
                f"- Converted Revenue: ${result['calculations']['converted_revenue']}$",
                f"- Adjusted Revenue: ${result['calculations']['adjusted_revenue']}$",
                f"- Percentage Growth: {result['calculations']['percentage_growth']}"
            ])

        return "\n".join(report)

    def parse_input(self, input_data: str, format_type: str) -> List[Dict]:
        """Parse input data from either CSV or JSON format."""
        if format_type.lower() == 'csv':
            csv_file = io.StringIO(input_data)
            reader = csv.DictReader(csv_file)
            return list(reader)
        elif format_type.lower() == 'json':
            data = json.loads(input_data)
            return data.get('records', []) if isinstance(data, dict) else data
        else:
            raise ValueError("Invalid format type. Must be either 'csv' or 'json'.")

# Example usage
if __name__ == "__main__":
    # Sample data
    sample_data = '''
                {
    "records": [
        { "month": "January", "revenue": 26000, "currency": "USD", "tax_rate": 9, "conversion_rate": 1 },
        { "month": "February", "revenue": 27500, "currency": "EUR", "tax_rate": 11, "conversion_rate": 1.2 },
        { "month": "March", "revenue": 30000, "currency": "GBP", "tax_rate": 10, "conversion_rate": 1.4 },
        { "month": "April", "revenue": 32000, "currency": "USD", "tax_rate": 8, "conversion_rate": 1 },
        { "month": "May", "revenue": 34000, "currency": "EUR", "tax_rate": 12, "conversion_rate": 1.2 },
        { "month": "June", "revenue": 36000, "currency": "GBP", "tax_rate": 15, "conversion_rate": 1.4 },
        { "month": "July", "revenue": 38000, "currency": "USD", "tax_rate": 7, "conversion_rate": 1 },
        { "month": "August", "revenue": 40000, "currency": "EUR", "tax_rate": 10, "conversion_rate": 1.2 },
        { "month": "September", "revenue": 42000, "currency": "GBP", "tax_rate": 13, "conversion_rate": 1.4 },
        { "month": "October", "revenue": 44000, "currency": "USD", "tax_rate": 6, "conversion_rate": 1 },
        { "month": "November", "revenue": 46000, "currency": "EUR", "tax_rate": 14, "conversion_rate": 1.2 },
        { "month": "December", "revenue": 48000, "currency": "GBP", "tax_rate": 16, "conversion_rate": 1.4 }
    ]
    }

        '''
    
    reporter = FinancialReportingSystem()
    try:
        data = reporter.parse_input(sample_data, 'json')
        report = reporter.generate_report(data)
        print(report)
    except Exception as e:
        print(f"Error processing data: {str(e)}")