#!/usr/bin/env python3
"""
Electricity Carbon Footprint Calculator
Flask backend application for calculating CO2 emissions from electricity usage
"""

from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os
import tempfile

# Initialize Flask application
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'carbon-footprint-calculator-2025'

# Constants for calculations
EMISSION_FACTOR = 0.82  # kg CO2 per kWh for India
MONTHS_PER_YEAR = 12

def calculate_carbon_footprint(monthly_usage_kwh):
    """
    Calculate annual carbon footprint from monthly electricity usage
    
    Args:
        monthly_usage_kwh (float): Monthly electricity usage in kWh
    
    Returns:
        dict: Dictionary containing calculation results
    """
    # Calculate annual usage
    annual_usage = monthly_usage_kwh * MONTHS_PER_YEAR
    
    # Calculate annual CO2 emissions using India's emission factor
    annual_emissions = annual_usage * EMISSION_FACTOR
    
    # Calculate additional context (approximate values for impact visualization)
    # 1 tree absorbs ~22 kg CO2 per year on average
    trees_needed = round(annual_emissions / 22, 1)
    
    # 1 kg CO2 = approximately 2.3 miles driven in average car
    car_miles = round(annual_emissions * 2.3)
    
    return {
        'annual_usage': round(annual_usage, 2),
        'annual_emissions': round(annual_emissions, 2),
        'trees_needed': trees_needed,
        'car_miles': car_miles
    }

@app.route('/')
def index():
    """
    Homepage route - displays the calculator form
    """
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    """
    Calculate route - processes form data and displays results
    """
    try:
        # Get form data
        user_type = request.form.get('user_type')
        monthly_usage = float(request.form.get('monthly_usage', 0))
        
        # Validate inputs
        if not user_type or monthly_usage < 0:
            return render_template('index.html', error="Please provide valid inputs")
        
        # Calculate carbon footprint
        results = calculate_carbon_footprint(monthly_usage)
        
        # Prepare data for template
        template_data = {
            'user_type': user_type,
            'monthly_usage': monthly_usage,
            'annual_usage': results['annual_usage'],
            'annual_emissions': results['annual_emissions'],
            'trees_needed': results['trees_needed'],
            'car_miles': results['car_miles']
        }
        
        return render_template('result.html', **template_data)
    
    except ValueError:
        return render_template('index.html', error="Please enter a valid number for monthly usage")
    except Exception as e:
        return render_template('index.html', error="An error occurred during calculation")

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """
    Generate and download PDF report
    """
    try:
        # Get form data
        user_type = request.form.get('user_type')
        monthly_usage = float(request.form.get('monthly_usage'))
        annual_usage = float(request.form.get('annual_usage'))
        annual_emissions = float(request.form.get('annual_emissions'))
        
        # Create temporary file for PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_filename = temp_file.name
        temp_file.close()
        
        # Generate PDF
        generate_pdf_report(temp_filename, {
            'user_type': user_type,
            'monthly_usage': monthly_usage,
            'annual_usage': annual_usage,
            'annual_emissions': annual_emissions
        })
        
        # Send file and clean up
        return send_file(
            temp_filename,
            as_attachment=True,
            download_name=f'Carbon_Footprint_Report_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500

def generate_pdf_report(filename, data):
    """
    Generate PDF report using ReportLab
    
    Args:
        filename (str): Output PDF filename
        data (dict): Report data
    """
    # Create PDF document
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkgreen
    )
    
    # Title
    story.append(Paragraph("🌱 Electricity Carbon Footprint Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report date
    report_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"<b>Report Generated:</b> {report_date}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Input Details Section
    story.append(Paragraph("Input Details", heading_style))
    
    input_data = [
        ['Parameter', 'Value'],
        ['User Type', data['user_type']],
        ['Monthly Electricity Usage', f"{data['monthly_usage']} kWh"],
        ['Annual Electricity Usage', f"{data['annual_usage']} kWh"]
    ]
    
    input_table = Table(input_data, colWidths=[3*inch, 2*inch])
    input_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(input_table)
    story.append(Spacer(1, 30))
    
    # Results Section
    story.append(Paragraph("Carbon Footprint Results", heading_style))
    
    # Main result highlight
    result_text = f"""
    <para align=center>
    <b><font size=18 color=red>Annual CO₂ Emissions: {data['annual_emissions']} kg</font></b>
    </para>
    """
    story.append(Paragraph(result_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Calculation method
    story.append(Paragraph("Calculation Method", heading_style))
    calculation_text = f"""
    <b>Formula:</b> Annual CO₂ Emission = Monthly Usage × 12 × Emission Factor<br/>
    <b>Emission Factor (India):</b> {EMISSION_FACTOR} kg CO₂ per kWh<br/>
    <b>Calculation:</b> {data['monthly_usage']} kWh × 12 × {EMISSION_FACTOR} = {data['annual_emissions']} kg CO₂
    """
    story.append(Paragraph(calculation_text, styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Environmental Impact Context
    story.append(Paragraph("Environmental Impact Context", heading_style))
    
    # Calculate additional context
    trees_needed = round(data['annual_emissions'] / 22, 1)
    car_miles = round(data['annual_emissions'] * 2.3)
    
    impact_data = [
        ['Impact Metric', 'Equivalent'],
        ['Trees needed to offset emissions', f"{trees_needed} trees per year"],
        ['Equivalent car miles driven', f"{car_miles:,} miles"],
        ['Monthly average', f"{round(data['annual_emissions']/12, 1)} kg CO₂"]
    ]
    
    impact_table = Table(impact_data, colWidths=[3*inch, 2*inch])
    impact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(impact_table)
    story.append(Spacer(1, 30))
    
    # Recommendations
    story.append(Paragraph("Recommendations to Reduce Carbon Footprint", heading_style))
    recommendations = """
    • Switch to LED light bulbs to reduce electricity consumption<br/>
    • Use energy-efficient appliances (5-star rated)<br/>
    • Install solar panels if feasible<br/>
    • Unplug devices when not in use<br/>
    • Use natural light during daytime<br/>
    • Set AC temperature to 24°C or higher<br/>
    • Regular maintenance of electrical appliances
    """
    story.append(Paragraph(recommendations, styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Footer
    footer_text = """
    <para align=center>
    <font size=10>
    This report was generated by the Electricity Carbon Footprint Calculator<br/>
    Data based on India's electricity emission factor of 0.82 kg CO₂/kWh<br/>
    For more information on reducing your carbon footprint, consult environmental agencies.
    </font>
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('index.html', error="Internal server error occurred"), 500

if __name__ == '__main__':
    # Run the Flask application
    print("🌱 Starting Electricity Carbon Footprint Calculator...")
    print("📊 Open your browser and go to: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    
    # Run in debug mode for development
    app.run(debug=True, host='0.0.0.0', port=5000)
