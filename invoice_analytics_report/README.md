# Módulo: Invoice Analytics Report

## Descripción

Módulo para Odoo 17 que crea un reporte analítico de facturas mediante una vista PostgreSQL optimizada. Proporciona análisis detallado de facturación con información de clientes, productos, equipos de ventas y clasificaciones empresariales.

## Características

- **Vista PostgreSQL optimizada**: Utiliza vistas SQL nativas para mejor rendimiento
- **Análisis multidimensional**: Vistas tree, pivot y graph
- **Filtros avanzados**: Por equipo, vendedor, sector, tamaño de empresa, tipo de facturación
- **Información consolidada**: Combina datos de clientes, productos, equipos y clasificaciones
- **Específico para Colombia**: Incluye campos personalizados como NIT, DIAN, sectores LOGYCA

## Dependencias

- `base`
- `account`
- `product`
- `crm`
- `sale`

**Nota**: Este módulo asume que existen los siguientes modelos personalizados en tu base de datos:
- `logyca_vinculation_types`
- `logyca_sectors`
- `logyca_member_red`

## Instalación

1. Copiar el módulo a la carpeta de addons de Odoo:
   ```bash
   cp -r invoice_analytics_report /path/to/odoo/addons/
   ```

2. Actualizar la lista de aplicaciones en Odoo:
   - Modo desarrollador > Apps > Update Apps List

3. Buscar e instalar el módulo "Invoice Analytics Report"

## Uso

### Acceso al reporte

Ir a: **Reportes Facturación > Análisis de Facturas**

### Vistas disponibles

1. **Vista Lista (Tree)**:
   - Muestra todas las facturas con detalles completos
   - Permite ordenar por cualquier columna
   - Suma automática del subtotal

2. **Vista Pivot**:
   - Análisis dimensional de datos
   - Configuración predeterminada: Año/Mes vs Equipo
   - Personalizable con drag & drop de dimensiones

3. **Vista Gráfico**:
   - Visualización gráfica de los datos
   - Tipo de gráfico configurable (barras, líneas, circular)

### Filtros predefinidos

- **Año Actual**: Facturas del año en curso (activado por defecto)
- **Mes Actual**: Facturas del mes actual
- **Por Tipo**: Nueva, Renovación, Reactivación
- **Por Estado de Pago**: Pagado, Pendiente

### Agrupaciones disponibles

- Equipo de ventas
- Vendedor
- Sector económico
- Tamaño de empresa
- Tipo de facturación
- Año y mes
- Estado de pago

## Estructura del Módulo

```
invoice_analytics_report/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── invoice_analytics_report.py
├── views/
│   └── invoice_analytics_report_view.xml
├── security/
│   └── ir.model.access.csv
└── README.md
```

## Campos del Reporte

### Información del Cliente
- **NIT**: Número de identificación tributaria
- **Cliente**: Nombre del cliente (considera jerarquía padre-hijo)

### Información de Factura
- **Factura**: Número de factura
- **Fecha Factura**: Fecha de emisión
- **Fecha Vencimiento**: Fecha de vencimiento del pago
- **Mes/Año**: Para agrupaciones temporales
- **Subtotal**: Monto sin impuestos

### Información de Producto
- **Producto Facturado**: Nombre del producto
- **Tipo de Facturación**: Nueva, Renovación o Reactivación

### Información Comercial
- **Equipo**: Equipo de ventas asignado
- **Vendedor**: Usuario responsable de la factura
- **Plazo de Pago**: Términos de pago
- **Estado de Pago**: Estado actual del pago

### Clasificación del Cliente
- **Tipo de Vinculación**: Tipos de vinculación del cliente
- **Fecha de Vinculación**: Cuándo se vinculó el cliente
- **Sector**: Sector económico
- **Tamaño de Empresa**: MYPE, MEDIANA, GRANDE
- **Red de Valor**: Red a la que pertenece
- **Tipo de Miembro**: Clasificación de membresía

## Personalización

### Modificar el rango de fechas

Editar en `models/invoice_analytics_report.py`, método `_where()`:

```python
def _where(self):
    where_str = """
    WHERE m.date > '2024-01-01'  # Cambiar fecha aquí
        AND m.state = 'posted'
        ...
    """
    return where_str
```

### Agregar productos

Modificar la condición en el método `_where()`:

```python
AND pt.id IN (9, 1605, 3, NUEVO_ID)  # Agregar nuevos IDs
```

### Agregar campos personalizados

1. Agregar el campo en el modelo (`models/invoice_analytics_report.py`):
   ```python
   nuevo_campo = fields.Char('Nuevo Campo', readonly=True)
   ```

2. Incluir en el SELECT del método `_select()`:
   ```python
   campo_tabla.nombre as nuevo_campo,
   ```

3. Agregar en la vista (`views/invoice_analytics_report_view.xml`):
   ```xml
   <field name="nuevo_campo" string="Nuevo Campo"/>
   ```

## Rendimiento

La vista PostgreSQL se crea una sola vez al instalar/actualizar el módulo. Los datos se consultan directamente desde la vista SQL, lo que proporciona:

- **Alta velocidad de consulta**: No procesa datos en Python
- **Optimización de base de datos**: Aprovecha índices y optimizador de PostgreSQL
- **Menor consumo de memoria**: Datos filtrados en BD

## Solución de Problemas

### Error: "relation does not exist"

La vista no se creó correctamente. Solución:
```bash
# En Odoo shell
./odoo-bin shell -d nombre_bd
>>> env['invoice.analytics.report'].init()
>>> env.cr.commit()
```

### No aparecen datos

Verificar:
1. Que existan facturas después de 2025-01-01
2. Que las facturas estén en estado 'posted'
3. Que tengan productos con IDs: 9, 1605 o 3

### Falta información de vinculación/sector

Verificar que los módulos de LOGYCA estén instalados:
- Módulo de tipos de vinculación
- Módulo de sectores
- Módulo de redes de valor

## Mantenimiento

Para actualizar la vista después de cambios en el código:

1. Actualizar el módulo desde la interfaz de Odoo
2. O ejecutar desde línea de comandos:
   ```bash
   ./odoo-bin -u invoice_analytics_report -d nombre_bd
   ```

## Licencia

LGPL-3

## Autor

LOGYCA - https://logyca.com

## Soporte

Para soporte o consultas, contactar al equipo de desarrollo de LOGYCA.
