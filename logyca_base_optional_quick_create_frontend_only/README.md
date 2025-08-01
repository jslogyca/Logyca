# Logyca - Base Optional Quick Create Frontend Only

## Description

**Logyca Customization Module**

This module extends the functionality of `base_optional_quick_create` from OCA to only restrict quick creation from the frontend (user interface) while allowing backend operations to continue working normally.

This customization was developed specifically for Logyca's requirements.

## Problem Solved

The original `base_optional_quick_create` module blocks ALL `name_create` calls, which interferes with Logyca's backend operations like:
- Helpdesk automatic contact creation from emails
- Mail system operations
- Portal automatic user creation
- Other programmatic operations

## Solution

This module modifies the restriction logic to only block frontend calls (those containing 'params' in the context) while allowing backend programmatic calls to proceed normally.

## Features

- ✅ Blocks quick creation from frontend forms and many2one fields
- ✅ Allows backend modules to create records programmatically
- ✅ Maintains all original functionality of base_optional_quick_create
- ✅ Compatible with Helpdesk, Mail, Portal and other system modules
- ✅ Specifically designed for Logyca's infrastructure

## Installation

1. Install `base_optional_quick_create` from OCA
2. Install this Logyca customization module
3. Configure models to avoid quick create as usual

## Usage

Works exactly like the original module, but with improved backend compatibility for Logyca's needs.

## Technical Details

The module detects frontend calls by checking for 'params' in the execution context, which is always present in RPC calls from the Odoo web interface but absent in programmatic calls.

## Compatibility

- Odoo 17.0
- Requires: base_optional_quick_create (OCA)
- Developed for: Logyca

## Support

For support or modifications, contact the Logyca development team.