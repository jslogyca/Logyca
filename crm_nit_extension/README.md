# CRM NIT Extension

## Descripción
Módulo de extensión para Odoo 17 CRM que agrega el campo NIT (Número de Identificación Tributaria) para registros de empresas en leads.

## Características
- **Campo NIT**: Campo de tipo `char` para almacenar el NIT de la empresa
- **Visibilidad condicional**: El campo solo es visible cuando:
  - `type == 'lead'` (es un lead)
  - `type == False` (registro nuevo sin tipo definido)
- **Ubicación**: El campo aparece después del campo `partner_name` en el formulario de lead
- **Tracking**: El campo tiene habilitado el seguimiento de cambios

## Instalación

1. Copiar el módulo a la carpeta de addons de Odoo:
   ```bash
   cp -r crm_nit_extension /ruta/a/odoo/addons/
   ```

2. Actualizar la lista de módulos en Odoo:
   - Ir a Apps
   - Click en "Actualizar lista de aplicaciones"

3. Buscar e instalar "CRM NIT Extension"

## Uso

1. Ir a CRM > Leads
2. Crear o editar un Lead (no una Oportunidad)
3. El campo NIT aparecerá después del campo "Nombre de la empresa"
4. Ingresar el NIT de la empresa (ej: 900123456-7)

## Notas técnicas

### Herencia
- **Modelo heredado**: `crm.lead`
- **Vista heredada**: `crm.crm_lead_view_form`

### Estructura del campo
```python
nit = fields.Char(
    string='NIT',
    help='Número de Identificación Tributaria de la empresa',
    tracking=True,
)
```

### Dominio de visibilidad
```xml
invisible="not (type == 'lead' or type == False)"
```

Esto es equivalente al dominio original solicitado:
```python
['|', ('type', '=', 'lead'), ('type', '=', False)]
```

## Dependencias
- `crm`: Módulo CRM nativo de Odoo 17

## Versión
- **Versión del módulo**: 17.0.1.0.0
- **Versión de Odoo**: 17.0

## Autor
LOGYCA - https://www.logyca.com

## Licencia
LGPL-3
