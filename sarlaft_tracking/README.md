# SARLAFT Tracking Module

## Overview

This module provides a comprehensive SARLAFT (Sistema de Administración del Riesgo de Lavado de Activos y de la Financiación del Terrorismo) query tracking system for Odoo 18. It enables organizations to maintain proper compliance records for Anti-Money Laundering and Counter-Terrorism Financing regulations.

## Features

### Core Functionality
- **SARLAFT Query Registration**: Record and track SARLAFT queries for customers, suppliers, and employees with detailed information including:
  - Registration numbers
  - Query and next query dates
  - Risk level assessment (High, Medium, Low)
  - Result options and additional information
  - Result links and comments
- **Partner Integration**: Seamless integration with contacts (res.partner) and employees (hr.employee)
- **Automated Notifications**: System-generated activities and reminders for upcoming query deadlines
- **Identification Management**: Integration with Latin American identification types

### Data Management
- **Computed Fields**: Automatic calculation of overdue status and days to next query
- **Display Names**: Smart naming convention using registration numbers and partner names
- **Tracking**: Full audit trail with mail.thread integration for change tracking
- **Validation**: Data integrity checks to ensure next query dates are after current query dates

### Security & Access Control
- **Role-based Access**: Two security groups with different permission levels
  - SARLAFT / Read: Read-only access to SARLAFT records
  - SARLAFT / Administration: Full access including creation, editing, and management
- **Record Rules**: Proper access control rules for each group
- **Data Visibility**: Only users in SARLAFT groups can access data, buttons, and menus

### Views & Reports
- **Comprehensive Views**: List, form, and kanban views with intelligent sorting and filtering
- **Visual Indicators**: Color-coded records based on risk levels and overdue status
- **Smart Buttons**: Quick access to SARLAFT records from partner and employee forms
- **Analytics**: Pivot and graph reports for compliance analysis
- **Custom Reports**: Dedicated reporting views for SARLAFT tracking analysis

### Automation & Configuration
- **Configurable Notifications**: System parameter to define notification days in advance (default: 30 days)
- **Scheduled Tasks**: Daily cron job to create reminder activities for administrators
- **Activity Management**: Automatic creation of activities for users in SARLAFT Administration group
- **SARLAFT Options**: Configurable result options for query outcomes

## Installation

1. Copy the module to your Odoo addons directory
2. Update the module list in Odoo
3. Install the "SARLAFT Tracking" module
4. The module will automatically create:
   - Security groups and access rules
   - System parameters for notifications
   - Cron job for automated reminders

## Configuration

### Groups and Permissions
After installation, assign users to the appropriate SARLAFT groups:
- Go to Settings > Users & Companies > Groups
- Find "SARLAFT / Read" and "SARLAFT / Administration" groups
- Add users as needed

### Notification Settings
Configure the notification days parameter:
- Go to Settings > Technical > Parameters > System Parameters
- Find key: `sarlaft_tracking.notification_days`
- Set the value (default: 30 days before next query date)

### SARLAFT Options Configuration
Set up result options for SARLAFT queries:
- Go to SARLAFT > Configuration > SARLAFT Options
- Create or modify options that will be available when recording query results
- Each option can have a name and description

## Usage

### Creating SARLAFT Records
1. Go to SARLAFT > Tracking > SARLAFT Records
2. Click "Create" to add a new record
3. Fill in the required information:
   - Partner Type (Customer, Supplier, or Employee)
   - Related Partner (automatically links to employee if available)
   - Query Date and Next Query Date
   - Requested By (person who requested the query)
   - Registration Number (sequential number)
   - Result Option (from configured options)
   - Risk Level (High, Medium, Low)
   - Additional Information and Result Link
   - Optional Comments

### Data Import
The module supports standard Odoo import functionality:
1. Go to SARLAFT > Tracking > SARLAFT Records
2. Click "Import" in the list view
3. Upload your Excel or CSV file with the required columns
4. Map columns to fields following Odoo's import wizard
5. Preview and validate data before final import

### Integration with Partners and Employees
- **Partner Records**: When viewing a contact, you'll see:
  - SARLAFT smart button showing count of records
  - SARLAFT tab with summary information (last query, next query, risk level)
  - Direct access to create new SARLAFT records
- **Employee Records**: Similar integration with employee forms
- **Automatic Linking**: When selecting a partner with associated employees, the employee field is automatically populated

### Monitoring and Alerts
- **Overdue Tracking**: Records automatically show overdue status when next query date has passed
- **Days Counter**: Real-time calculation of days remaining until next query
- **Activity Reminders**: Automated creation of activities for administrators based on upcoming deadlines
- **Mail Integration**: Full tracking of changes and communications related to SARLAFT records

### Reports and Analytics
1. Go to SARLAFT > Reports > SARLAFT Analysis
2. Use different view modes:
   - **List View**: Detailed record listing with filters and grouping
   - **Pivot View**: Cross-tabulation analysis by various dimensions
   - **Graph View**: Visual charts and statistics
3. Apply filters by:
   - Date ranges (query date, next query date)
   - Partner type (customer, supplier, employee)
   - Risk level and overdue status
   - Company and user assignments

## Technical Details

### Models and Architecture
- **sarlaft.tracking**: Main tracking model with comprehensive field set
  - Inherits from `mail.thread` and `mail.activity.mixin` for communication tracking
  - Includes computed fields for display names, overdue status, and date calculations
  - Implements validation constraints and onchange methods
- **sarlaft.option**: Configuration model for query result options
- **Extended Models**:
  - `res.partner`: Extended with SARLAFT fields and computed data
  - `hr.employee`: Extended with SARLAFT integration and tracking capabilities

### Key Fields and Functionality
- **Core Fields**: Partner/Employee references, dates, registration numbers, risk levels
- **Identification**: Integration with `l10n_latam.identification.type` for proper ID management
- **Computed Fields**: Automatic calculation of overdue status and time-based indicators
- **Tracking**: Full audit trail with field-level change tracking
- **Activities**: Automated reminder system with configurable timing

### Data Files and Configuration
- **Security**: Complete access control with groups and record rules
- **Cron Jobs**: Daily automated reminder creation for upcoming queries
- **System Parameters**: Configurable notification timing
- **Views**: Comprehensive UI with list, form, kanban, pivot, and graph views

### Integration Points
- **Latin American Localization**: Uses `l10n_latam_base` for identification types
- **HR Module**: Deep integration with employee management
- **Contacts**: Enhanced partner records with SARLAFT tracking
- **Mail System**: Full communication and activity tracking
- **Reporting**: Built-in analytics and reporting capabilities

### Dependencies
- `base`: Core Odoo framework
- `contacts`: Partner management
- `hr`: Employee management
- `l10n_latam_base`: Latin American localization for identification types
- `mail`: Communication and activity tracking
- `web`: Web interface components

### Customization and Extension
The module is designed for easy customization:
- **Result Options**: Fully configurable through the UI
- **Notification Timing**: Adjustable via system parameters
- **Security**: Granular access control with groups
- **Fields**: Extensible model structure for additional requirements
- **Views**: Customizable interface components

## Compliance and Best Practices

### SARLAFT Compliance
This module helps organizations maintain compliance with Colombian SARLAFT regulations by:
- Providing structured record-keeping for all queries
- Ensuring proper documentation of risk assessments
- Maintaining audit trails for regulatory review
- Automating reminder systems to prevent missed deadlines
- Integrating with existing business processes

### Data Security
- Role-based access ensures only authorized personnel can view/modify records
- Complete audit trail maintains data integrity
- Integration with Odoo's security framework
- Proper data validation and constraints

## Support and Maintenance

### Version Information
- **Module Version**: 18.0.1.0.0
- **Odoo Version**: 18.0
- **Category**: Compliance
- **Author**: Logyca
- **Website**: https://www.logyca.org

### Troubleshooting
- Check user group assignments if menus/buttons don't appear
- Verify system parameters for notification timing issues
- Review cron job logs for automated reminder problems
- Ensure proper identification type configuration for partner integration

## License

This module is licensed under LGPL-3, allowing for both commercial and non-commercial use with proper attribution.
