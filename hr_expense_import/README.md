# HR Expense Import

Módulo para importar reportes de gastos (hr.expense.sheet) con sus respectivos gastos (hr.expense) desde archivos Excel.

## Características

- ✅ Importación masiva de gastos agrupados por reporte
- ✅ Validación de datos antes de la importación
- ✅ Soporte para grupos presupuestales y cuentas analíticas (detección automática)
- ✅ Asignación automática de productos según configuración del proveedor
- ✅ Soporte para modo de pago y tarjetas de crédito
- ✅ Agrupación opcional de CXP por factura
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
| I | Grupo Presupuestal / Cuenta Analítica | Detecta automáticamente si es logyca.budget_group o account.analytic.account |
| J | Total | Monto total del gasto (hr.expense - total_amount) |
| K | Exento de IVA | Monto exento de IVA (hr.expense - amount_tax_excluded) |
| L | IVA | Monto del IVA (hr.expense - tax_amount) |

### Notas Importantes

1. **Columna C (Referencia)**: Los gastos se agruparán por este campo para crear los reportes de gastos.
2. **Columna D (NIT Proveedor)**: Se busca el proveedor por su NIT con `parent_id = null`.
3. **Columna I (Grupo Presupuestal / Cuenta Analítica)**: 
   - El sistema primero intenta buscar como `logyca.budget_group`
   - Si no encuentra, busca como `account.analytic.account`
   - Si no encuentra ninguno, genera un error de validación
4. **Asignación de Productos**: Se utiliza la lógica del modelo `partner.product.purchase` similar al wizard `sale.order.import.file.wizard`:
   - Si el grupo presupuestal empieza con "AD": tipo 'ga' (Gasto Administrativo)
   - Si no es por defecto y no empieza con "AD": tipo 'gv' (Gasto de Venta)
   - Si es por defecto: tipo 'co' (Costo)

## Uso

1. Ir a **Gastos > Reportes de Gastos > Importar Reportes de Gastos**
2. Seleccionar el modo de pago:
   - Cuenta Propia del Empleado
   - Cuenta de la Compañía
   - Tarjeta de Crédito (requiere seleccionar la tarjeta)
3. **[NUEVO]** Si selecciona Tarjeta de Crédito, puede activar **Agrupar por Factura**:
   - ✅ **Activado**: Al contabilizar, se generará una sola CXP al tercero de la tarjeta de crédito
   - ❌ **Desactivado**: Se generará una CXP por cada gasto (comportamiento estándar)
4. Cargar el archivo Excel
5. Click en **Validar Datos** para verificar que todo esté correcto
6. Revisar el resultado de la validación
7. Si todo está correcto, click en **Importar**

## Validaciones

El módulo valida lo siguiente antes de importar:

1. ✅ Existencia de la compañía
2. ✅ Existencia del proveedor por NIT
3. ✅ Configuración de productos para el proveedor
4. ✅ Existencia del empleado
5. ✅ Existencia del grupo presupuestal o cuenta analítica (Columna I)
6. ✅ No duplicación de referencias de reportes
7. ✅ Tarjeta de crédito seleccionada (si aplica)

## Funcionalidad de Agrupación por Factura

### Comportamiento Normal (Agrupar por Factura = False)
```
Reporte de Gastos: RPT-2024-001
  - Gasto 1: Proveedor A, $100 → CXP a Proveedor A: $100
  - Gasto 2: Proveedor B, $200 → CXP a Proveedor B: $200
  - Gasto 3: Proveedor C, $150 → CXP a Proveedor C: $150
  
Total: 3 CXP creadas (una por cada proveedor)
```

### Con Agrupación por Factura (Agrupar por Factura = True + Tarjeta de Crédito)
```
Reporte de Gastos: RPT-2024-001
  - Gasto 1: Proveedor A, $100 ┐
  - Gasto 2: Proveedor B, $200 ├→ CXP a Banco XYZ (tarjeta): $450
  - Gasto 3: Proveedor C, $150 ┘
  
Total: 1 CXP creada (agrupada al tercero de la tarjeta de crédito)
```

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
- **[NUEVO] Agrupar por Factura**: Checkbox visible solo cuando modo = Tarjeta de Crédito
  - Default: False
  - Controla el comportamiento de la contabilización de CXP

## Campos del Reporte de Gastos (hr.expense.sheet)

Los siguientes campos se asignan del wizard al reporte:
- `name`: Referencia del reporte (Columna C)
- `employee_id`: Empleado del reporte (Columna H)
- `company_id`: Compañía del reporte (Columna A)
- `payment_mode`: Modo de pago (desde el wizard)
- `credit_card_id`: Tarjeta de crédito (desde el wizard)
- **[NUEVO]** `agrupar_por_factura`: Indica si se agrupan las CXP (desde el wizard)

## Campos del Gasto (hr.expense)

Cada fila del Excel crea un gasto con los siguientes campos:
- `date`: Fecha del gasto (Columna B)
- `employee_id`: Empleado (Columna H)
- `product_id`: Producto (asignado automáticamente según proveedor)
- `partner_id`: Proveedor (Columna D por NIT)
- `name`: Descripción (Columna E)
- `total_amount`: Total (Columna J)
- `amount_tax_excluded`: Exento de IVA (Columna K)
- `tax_amount`: IVA (Columna L)
- `amount_tax_excluded_description`: Descripción exento (Columna F)
- `company_id`: Compañía (Columna A)
- `payment_mode`: Modo de pago (desde el wizard)
- `budget_group_id`: Grupo presupuestal (Columna I, si aplica)
- `analytic_distribution`: Distribución analítica (Columna I, si aplica)

## Mensajes de Error

El módulo proporciona mensajes detallados indicando la fila y el tipo de error:

```
❌ Fila 3: Proveedor con NIT '900123456' no existe en el sistema
❌ Fila 5: Empleado 'Juan Pérez' no existe en el sistema
⚠️ Fila 7: No existe configuración de productos para el proveedor 'ABC S.A.'
❌ Fila 9: El valor 'INVALID' no corresponde ni a un Grupo Presupuestal ni a una Cuenta Analítica válida
```

## Cambios en la Versión Actual

### Cambios Principales
1. **Eliminada Columna J**: Se eliminó la columna de Cuenta Analítica separada
2. **Columna I Mejorada**: Ahora detecta automáticamente si es Grupo Presupuestal o Cuenta Analítica
3. **Campo Agrupar por Factura**: Nueva funcionalidad para agrupar CXP en contabilización
4. **Lógica de Contabilización**: Override del método `action_sheet_move_create` para soportar agrupación

### Detalles Técnicos
- El campo `agrupar_por_factura` solo es visible cuando `payment_mode == 'credit_card'`
- La agrupación de CXP solo funciona si hay una tarjeta de crédito configurada con un partner asociado
- Las líneas de CXP se agrupan buscando líneas con `account_type == 'liability_payable'` y `credit > 0`

## Autor

LOGYCA - 2024

## Licencia

LGPL-3
