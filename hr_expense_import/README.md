# HR Expense Import

Módulo para importar reportes de gastos (hr.expense.sheet) con sus respectivos gastos (hr.expense) desde archivos Excel.

## Características

- ✅ Importación masiva de gastos agrupados por reporte
- ✅ Validación de datos antes de la importación
- ✅ Soporte para grupos presupuestales y cuentas analíticas
- ✅ Asignación automática de productos según configuración del proveedor
- ✅ Soporte para modo de pago y tarjetas de crédito
- ✅ Mensajes de error detallados

## Dependencias

Este módulo requiere:
- `hr_expense`: Módulo base de gastos de Odoo
- `hr_expense_credit_card`: Módulo personalizado para tarjetas de crédito
- `import_lead_crm_logyca`: Módulo que contiene el modelo `partner.product.purchase`

## Formato del Archivo Excel

El archivo Excel debe tener las siguientes columnas (en orden):

| Columna | Campo | Descripción |
|---------|-------|-------------|
| A | Compañía | Nombre de la compañía (hr.expense - company_id.name) |
| B | Fecha | Fecha del gasto (hr.expense - date) |
| C | Referencia | Referencia del reporte - agrupa los gastos (hr.expense.sheet - name) |
| D | NIT Proveedor | NIT del proveedor (hr.expense - partner_id) |
| E | Notas internas | Descripción del gasto (hr.expense - description) |
| F | Descripción exento de IVA | Descripción del monto exento (hr.expense - amount_tax_excluded_description) |
| G | Proveedor | Nombre del proveedor (hr.expense - partner_id.name) |
| H | Empleado | Nombre del empleado (hr.expense - employee_id) |
| I | Grupo Presupuestal | Nombre del grupo presupuestal (hr.expense - budget_group_id) |
| J | Cuenta Analítica | Nombre de la cuenta analítica (hr.expense - analytic_distribution) |
| K | Total | Monto total del gasto (hr.expense - total_amount) |
| L | Exento de IVA | Monto exento de IVA (hr.expense - total_amount_with_excluded) |
| M | IVA | Monto del IVA (hr.expense - tax_amount) |

### Notas Importantes

1. **Columna C (Referencia)**: Los gastos se agruparán por este campo para crear los reportes de gastos.
2. **Columna D (NIT Proveedor)**: Se busca el proveedor por su NIT con `parent_id = null`.
3. **Asignación de Productos**: Se utiliza la lógica del modelo `partner.product.purchase` similar al wizard `sale.order.import.file.wizard`:
   - Si el grupo presupuestal empieza con "AD": tipo 'ga' (Gasto Administrativo)
   - Si no es por defecto y no empieza con "AD": tipo 'gv' (Gasto de Venta)
   - Si es por defecto: tipo 'co' (Costo)

## Uso

1. Ir a **Gastos > Reportes de Gastos > Importar Reportes de Gastos**
2. Seleccionar el modo de pago:
   - Cuenta Propia del Empleado
   - Cuenta de la Compañía
   - Tarjeta de Crédito (requiere seleccionar la tarjeta)
3. Cargar el archivo Excel
4. Click en **Validar Datos** para verificar que todo esté correcto
5. Revisar el resultado de la validación
6. Si todo está correcto, click en **Importar**

## Validaciones

El módulo valida lo siguiente antes de importar:

1. ✅ Existencia de la compañía
2. ✅ Existencia del proveedor por NIT
3. ✅ Configuración de productos para el proveedor
4. ✅ Existencia del empleado
5. ✅ Existencia del grupo presupuestal
6. ✅ Existencia de la cuenta analítica
7. ✅ No duplicación de referencias de reportes
8. ✅ Tarjeta de crédito seleccionada (si aplica)

## Ejemplo de Flujo

```python
# Ejemplo de estructura del Excel:
# Columna C (Referencia) agrupa los gastos en reportes

Referencia: "RPT-2024-001"
  - Gasto 1: Proveedor A, $100
  - Gasto 2: Proveedor B, $200
  - Gasto 3: Proveedor C, $150

Referencia: "RPT-2024-002"
  - Gasto 1: Proveedor D, $300
  - Gasto 2: Proveedor E, $250

# Resultado: 2 reportes de gastos creados
# RPT-2024-001 con 3 gastos
# RPT-2024-002 con 2 gastos
```

## Campos del Wizard

- **Archivo Excel**: Archivo a importar (requerido)
- **Pagador por**: Modo de pago para todos los gastos (requerido)
  - Cuenta Propia del Empleado
  - Cuenta de la Compañía
  - Tarjeta de Crédito
- **Tarjeta de Crédito**: Tarjeta asociada (requerido si modo = Tarjeta de Crédito)

## Campos del Reporte de Gastos (hr.expense.sheet)

Los siguientes campos se asignan del wizard al reporte:
- `name`: Referencia del reporte (Columna C)
- `employee_id`: Empleado del reporte (Columna H)
- `company_id`: Compañía del reporte (Columna A)
- `payment_mode`: Modo de pago (desde el wizard)
- `credit_card_id`: Tarjeta de crédito (desde el wizard)

## Campos del Gasto (hr.expense)

Cada fila del Excel crea un gasto con los siguientes campos:
- `date`: Fecha del gasto (Columna B)
- `employee_id`: Empleado (Columna H)
- `product_id`: Producto (asignado automáticamente según proveedor)
- `partner_id`: Proveedor (Columna D por NIT)
- `name`: Descripción (Columna E)
- `total_amount`: Total (Columna K)
- `total_amount_with_excluded`: Exento de IVA (Columna L)
- `tax_amount`: IVA (Columna M)
- `amount_tax_excluded_description`: Descripción exento (Columna F)
- `company_id`: Compañía (Columna A)
- `payment_mode`: Modo de pago (desde el wizard)
- `budget_group_id`: Grupo presupuestal (Columna I)
- `analytic_distribution`: Distribución analítica (Columna J)

## Mensajes de Error

El módulo proporciona mensajes detallados indicando la fila y el tipo de error:

```
❌ Fila 3: Proveedor con NIT '900123456' no existe en el sistema
❌ Fila 5: Empleado 'Juan Pérez' no existe en el sistema
⚠️ Fila 7: No existe configuración de productos para el proveedor 'ABC S.A.'
```

## Autor

LOGYCA - 2024

## Licencia

LGPL-3
