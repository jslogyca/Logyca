# Guía de Personalización - Invoice Analytics Report

## Configuraciones Comunes

### 1. Cambiar el Rango de Fechas

**Ubicación**: `models/invoice_analytics_report.py` - Método `_where()`

**Ejemplo 1**: Mostrar facturas desde hace 6 meses
```python
def _where(self):
    where_str = """
    WHERE m.date >= CURRENT_DATE - INTERVAL '6 months'
        AND m.state = 'posted'
        AND m.move_type IN ('out_invoice', 'out_refund')
        AND l.product_id IS NOT NULL
        AND pt.id IN (9, 1605, 3)
    """
    return where_str
```

**Ejemplo 2**: Mostrar facturas del año actual
```python
def _where(self):
    where_str = """
    WHERE date_part('year', m.date) = date_part('year', CURRENT_DATE)
        AND m.state = 'posted'
        AND m.move_type IN ('out_invoice', 'out_refund')
        AND l.product_id IS NOT NULL
        AND pt.id IN (9, 1605, 3)
    """
    return where_str
```

### 2. Agregar Más Productos

**Ubicación**: `models/invoice_analytics_report.py` - Método `_where()`

**Antes**:
```python
AND pt.id IN (9, 1605, 3)
```

**Después** (agregar productos con IDs 100 y 200):
```python
AND pt.id IN (9, 1605, 3, 100, 200)
```

O para incluir TODOS los productos:
```python
-- Eliminar la línea: AND pt.id IN (9, 1605, 3)
```

### 3. Agregar Nuevos Campos al Reporte

**Paso 1**: Agregar el campo en el modelo

Editar `models/invoice_analytics_report.py`:

```python
class InvoiceAnalyticsReport(models.Model):
    _name = "invoice.analytics.report"
    # ... campos existentes ...
    
    # Nuevo campo
    invoice_reference = fields.Char('Referencia', readonly=True)
    partner_phone = fields.Char('Teléfono', readonly=True)
```

**Paso 2**: Incluir en el SELECT

En el método `_select()`:

```python
def _select(self):
    select_str = """
    SELECT 
        -- ... campos existentes ...
        m.ref as invoice_reference,
        p.phone as partner_phone
    """
    return select_str
```

**Paso 3**: Agregar a las vistas

En `views/invoice_analytics_report_view.xml`:

```xml
<!-- En la vista tree -->
<tree>
    <!-- ... campos existentes ... -->
    <field name="invoice_reference" string="Referencia"/>
    <field name="partner_phone" string="Teléfono"/>
</tree>

<!-- En la búsqueda -->
<search>
    <field name="invoice_reference" string="Referencia"/>
    <field name="partner_phone" string="Teléfono"/>
</search>
```

### 4. Modificar los Tipos de Facturación

**Ubicación**: `models/invoice_analytics_report.py` - Método `_select()`

**Actual**:
```python
(
    SELECT 
        CASE
            WHEN pt2.id = 3 THEN 'Renovación Aportes'
            WHEN pt2.id = 1605 THEN 'Nueva'
            WHEN pt2.id = 9 THEN 'Reactivación'
            ELSE NULL
        END
    FROM account_move_line l2
    -- ...
) AS invoice_type,
```

**Personalizado** (agregar más tipos):
```python
(
    SELECT 
        CASE
            WHEN pt2.id = 3 THEN 'Renovación Aportes'
            WHEN pt2.id = 1605 THEN 'Nueva'
            WHEN pt2.id = 9 THEN 'Reactivación'
            WHEN pt2.id = 50 THEN 'Upgrade'
            WHEN pt2.id = 100 THEN 'Cross-sell'
            ELSE 'Otros'
        END
    FROM account_move_line l2
    -- ...
) AS invoice_type,
```

### 5. Agregar Campos Calculados

**Ejemplo**: Calcular días de atraso de pago

```python
# En el modelo
days_overdue = fields.Integer('Días de Atraso', readonly=True)

# En _select()
CASE 
    WHEN m.payment_state != 'paid' 
         AND m.invoice_date_due < CURRENT_DATE
    THEN CURRENT_DATE - m.invoice_date_due
    ELSE 0
END AS days_overdue,
```

### 6. Filtros Personalizados

**Agregar filtros a la vista search**:

Editar `views/invoice_analytics_report_view.xml`:

```xml
<search>
    <!-- ... filtros existentes ... -->
    
    <!-- Filtro por monto -->
    <filter string="Mayor a $1,000,000" name="filter_high_value" 
            domain="[('amount_untaxed', '>=', 1000000)]"/>
    
    <!-- Filtro por vencidas -->
    <filter string="Vencidas" name="filter_overdue" 
            domain="[('payment_state', '!=', 'paid'), 
                     ('invoice_date_due', '<', context_today())]"/>
    
    <!-- Filtro por rango de fechas -->
    <filter string="Último Trimestre" name="filter_last_quarter"
            domain="[('invoice_date', '>=', (context_today() - relativedelta(months=3)).strftime('%Y-%m-%d'))]"/>
</search>
```

### 7. Personalizar Vista Pivot

**Cambiar agrupaciones por defecto**:

Editar `views/invoice_analytics_report_view.xml`:

```xml
<pivot string="Análisis de Facturas">
    <!-- Filas -->
    <field name="team_name" type="row"/>
    <field name="salesperson_name" type="row"/>
    
    <!-- Columnas -->
    <field name="invoice_type" type="col"/>
    
    <!-- Medidas -->
    <field name="amount_untaxed" type="measure"/>
</pivot>
```

### 8. Agregar Nuevos Menús

**Ejemplo**: Crear submenús por tipo de reporte

Editar `views/invoice_analytics_report_view.xml`:

```xml
<!-- Menú para renovaciones -->
<record id="action_invoice_analytics_renewals" model="ir.actions.act_window">
    <field name="name">Renovaciones</field>
    <field name="res_model">invoice.analytics.report</field>
    <field name="view_mode">tree,pivot,graph</field>
    <field name="domain">[('invoice_type', '=', 'Renovación Aportes')]</field>
    <field name="context">{
        'search_default_current_year': 1,
    }</field>
</record>

<menuitem id="menu_invoice_analytics_renewals"
          name="Renovaciones"
          parent="menu_invoice_analytics_root"
          action="action_invoice_analytics_renewals"
          sequence="20"/>

<!-- Menú para nuevas ventas -->
<record id="action_invoice_analytics_new" model="ir.actions.act_window">
    <field name="name">Nuevas Ventas</field>
    <field name="res_model">invoice.analytics.report</field>
    <field name="view_mode">tree,pivot,graph</field>
    <field name="domain">[('invoice_type', '=', 'Nueva')]</field>
    <field name="context">{
        'search_default_current_year': 1,
    }</field>
</record>

<menuitem id="menu_invoice_analytics_new"
          name="Nuevas Ventas"
          parent="menu_invoice_analytics_root"
          action="action_invoice_analytics_new"
          sequence="30"/>
```

### 9. Optimización de Rendimiento

**Agregar índices a la base de datos**:

Crear archivo `data/sql_indexes.sql`:

```sql
-- Índices recomendados para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_account_move_date_state 
    ON account_move(date, state);

CREATE INDEX IF NOT EXISTS idx_account_move_partner_date 
    ON account_move(partner_id, date);

CREATE INDEX IF NOT EXISTS idx_account_move_line_product 
    ON account_move_line(product_id, move_id);
```

### 10. Agregar Totales y Subtotales

**En la vista tree**:

```xml
<tree>
    <!-- Agregar sum para columnas numéricas -->
    <field name="amount_untaxed" sum="Total Facturado"/>
    
    <!-- Agregar count -->
    <field name="invoice_name" count="Total Facturas"/>
</tree>
```

## Validación Después de Cambios

Después de realizar cambios, seguir estos pasos:

1. **Actualizar el módulo**:
   ```bash
   ./odoo-bin -u invoice_analytics_report -d nombre_bd
   ```

2. **Verificar logs**:
   - Revisar que no haya errores de SQL
   - Confirmar que la vista se creó correctamente

3. **Probar en la interfaz**:
   - Verificar que aparezcan los nuevos campos
   - Probar los filtros
   - Confirmar que los datos son correctos

4. **En caso de error**, recrear la vista manualmente:
   ```python
   # En Odoo shell
   env['invoice.analytics.report'].init()
   env.cr.commit()
   ```

## Backup Antes de Modificar

Siempre hacer backup del módulo antes de cambios importantes:

```bash
cp -r invoice_analytics_report invoice_analytics_report_backup_$(date +%Y%m%d)
```

## Contacto y Soporte

Para dudas específicas sobre personalizaciones complejas, contactar al equipo de desarrollo de LOGYCA.
