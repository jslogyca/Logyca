# Changelog

Todos los cambios notables en este módulo serán documentados en este archivo.

## [17.0.2.0.0] - 2024-12-01

### Cambios Importantes

#### Eliminado
- **Columna J (Cuenta Analítica)**: Se eliminó la columna separada para cuentas analíticas del archivo Excel
- El formato ahora tiene 12 columnas en lugar de 13

#### Modificado
- **Columna I (Grupo Presupuestal / Cuenta Analítica)**: 
  - Ahora detecta automáticamente si el valor corresponde a `logyca.budget_group` o `account.analytic.account`
  - Búsqueda inteligente: primero intenta como grupo presupuestal, luego como cuenta analítica
  - Mejora la flexibilidad sin necesidad de columnas separadas

#### Agregado
- **Campo `agrupar_por_factura`** en `hr.expense.import.wizard`:
  - Tipo: Boolean
  - Default: False
  - Solo visible cuando `payment_mode = 'credit_card'`
  - Controla el comportamiento de contabilización de CXP
  
- **Campo `agrupar_por_factura`** en `hr.expense.sheet`:
  - Se sincroniza desde el wizard al crear el reporte
  - Permite control granular por reporte de gastos
  
- **Override del método `action_sheet_move_create`** en `hr.expense.sheet`:
  - Implementa lógica de agrupación de CXP
  - Cuando `agrupar_por_factura = True`:
    - Agrupa todas las líneas de CXP en una sola
    - Asigna el partner de la tarjeta de crédito
    - Suma todos los montos en crédito
    - Mantiene una única línea de CXP al tercero de la tarjeta
  - Cuando `agrupar_por_factura = False`:
    - Comportamiento estándar (una CXP por gasto)

### Mejoras Técnicas

#### Validaciones Actualizadas
- Validación 5 y 6 combinadas en una sola validación inteligente para Columna I
- Mensajes de error mejorados para indicar claramente cuando no se encuentra ni grupo presupuestal ni cuenta analítica
- Total de validaciones reducido de 7 a 6

#### Vistas Actualizadas
- `hr_expense_import_wizard_views.xml`:
  - Instrucciones actualizadas reflejando el nuevo formato de 12 columnas
  - Campo `agrupar_por_factura` agregado con visibilidad condicional
  - Documentación en línea sobre el comportamiento del nuevo campo

- `hr_expense_sheet_views.xml`:
  - Nueva herencia de vista form para mostrar campo `agrupar_por_factura`
  - Campo solo visible cuando hay tarjeta de crédito configurada

### Detalles de Implementación

#### Lógica de Búsqueda Columna I
```python
# Primero buscar como grupo presupuestal
budget_group = env['logyca.budget_group'].search([
    ('name', '=', value),
    ('company_id', '=', company_id)
])

# Si no es grupo, buscar como cuenta analítica
if not budget_group:
    analytic = env['account.analytic.account'].search([
        ('name', '=', value),
        '|', ('company_id', '=', company_id), ('company_id', '=', False)
    ])
```

#### Lógica de Agrupación de CXP
```python
if agrupar_por_factura and credit_card_id:
    # Agrupa líneas payable
    payable_lines = move.line_ids.filtered(
        lambda l: l.account_id.account_type == 'liability_payable' 
        and l.credit > 0
    )
    
    # Mantiene primera línea con suma total
    first_line.write({
        'credit': sum(payable_lines.mapped('credit')),
        'partner_id': credit_card_id.partner_id.id
    })
    
    # Elimina líneas restantes
    payable_lines[1:].unlink()
```

### Compatibilidad

#### Archivos Excel Existentes
- ⚠️ **IMPORTANTE**: Los archivos Excel con formato antiguo (13 columnas) NO son compatibles
- Es necesario actualizar plantillas Excel eliminando la Columna J
- Las columnas se recorrieron: K→J, L→K, M→L

#### Migración
Si tiene archivos Excel del formato anterior:
1. Eliminar la Columna J (Cuenta Analítica)
2. Mover los datos de K, L, M a J, K, L respectivamente
3. Los valores que estaban en Columna J ahora van en Columna I junto con grupos presupuestales

### Notas de Actualización

- El campo `agrupar_por_factura` es opcional y no afecta reportes existentes
- Los reportes creados con el wizard tienen el valor según lo seleccionado al importar
- Se puede modificar manualmente en cada reporte si es necesario
- La agrupación solo funciona si hay una tarjeta de crédito configurada con partner

### Testing Recomendado

1. Importar con `agrupar_por_factura = False` (comportamiento estándar)
2. Importar con `agrupar_por_factura = True` y verificar CXP única
3. Verificar que Columna I detecta correctamente grupos presupuestales
4. Verificar que Columna I detecta correctamente cuentas analíticas
5. Probar validación cuando valor en Columna I no existe

---

## [17.0.1.0.0] - 2024-XX-XX

### Agregado
- Versión inicial del módulo
- Importación masiva de reportes de gastos desde Excel
- Validación de datos antes de importación
- Soporte para grupos presupuestales y cuentas analíticas (columnas separadas)
- Asignación automática de productos según proveedor
- Soporte para tarjetas de crédito
