# Corrección de Error - ValueError en @depends

## Error Encontrado

```
ValueError: Wrong @depends on '_compute_total_amount_currency' 
(compute method of field hr.expense.total_amount_currency). 
Dependency field 'unit_amount' not found in model hr.expense.
```

## Causa del Error

El error ocurría porque intenté hacer override de los métodos `_compute_total_amount()` y `_compute_total_amount_currency()` del modelo base `hr.expense`, pero estos métodos ya tienen sus propios decoradores `@api.depends` definidos en el modelo base.

Cuando se hereda un modelo y se intenta redefinir un método compute con diferentes dependencias, Odoo lanza este error porque los campos que se mencionan en el `@depends` no coinciden con los del modelo heredado.

## Solución Implementada

En lugar de hacer override de los métodos compute existentes, creé un **nuevo campo computado** llamado `total_amount_with_excluded` que:

1. **Depende de** `total_amount` y `amount_tax_excluded`
2. **Calcula** el total sumando ambos valores
3. **No interfiere** con los cálculos estándar de Odoo

### Código Correcto

```python
# Campo computado nuevo (NO override)
total_amount_with_excluded = fields.Monetary(
    string='Total con Valor Excluido',
    compute='_compute_total_amount_with_excluded',
    currency_field='currency_id',
    store=True,
    help='Total del gasto incluyendo el valor excluido del IVA'
)

@api.depends('total_amount', 'amount_tax_excluded')
def _compute_total_amount_with_excluded(self):
    """
    Calcula el total incluyendo el valor excluido del IVA
    """
    for expense in self:
        expense.total_amount_with_excluded = expense.total_amount + expense.amount_tax_excluded
```

## Cambios Realizados

### 1. Modelo hr.expense

**Antes** (INCORRECTO):
```python
@api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id', 'amount_tax_excluded')
def _compute_total_amount(self):
    # Override del método base - CAUSA ERROR
    super(HrExpense, expense)._compute_total_amount()
    expense.total_amount += expense.amount_tax_excluded
```

**Ahora** (CORRECTO):
```python
# Nuevo campo computado
total_amount_with_excluded = fields.Monetary(...)

@api.depends('total_amount', 'amount_tax_excluded')
def _compute_total_amount_with_excluded(self):
    # No interfiere con el modelo base
    expense.total_amount_with_excluded = expense.total_amount + expense.amount_tax_excluded
```

### 2. Vistas

Se agregó el campo `total_amount_with_excluded` en las vistas para mostrar el total que incluye el valor excluido.

**Vista Formulario**:
- Se muestra `total_amount` (estándar de Odoo)
- Se muestra `total_amount_with_excluded` (cuando hay valor excluido)

**Vista Lista**:
- Columna `total_amount` (estándar)
- Columna `total_amount_with_excluded` (opcional, oculta por defecto)

### 3. Contabilización

El método `_prepare_expense_credit_card_move_vals()` ya calculaba correctamente el total sumando:
- Base
- Impuestos
- Valor excluido

Por lo tanto, NO requirió cambios en la lógica de contabilización.

## Funcionamiento Correcto

### Flujo de Cálculo:

1. **Usuario ingresa**:
   - Precio unitario: $100.000
   - Cantidad: 1
   - IVA: 19%
   - Valor excluido: $10.000

2. **Odoo calcula** (estándar):
   - `total_amount` = (1 × $100.000) + IVA($19.000) = $119.000

3. **Nuestro módulo calcula** (adicional):
   - `total_amount_with_excluded` = $119.000 + $10.000 = $129.000

4. **Contabilización**:
   - Línea base: $100.000
   - Línea IVA: $19.000
   - Línea valor excluido: $10.000
   - Línea CXP: $129.000

## Verificación

### Test 1: Sin Valor Excluido
```
Precio: $100.000
IVA: $19.000
Valor Excluido: $0

total_amount = $119.000
total_amount_with_excluded = $119.000 ✓
```

### Test 2: Con Valor Excluido
```
Precio: $100.000
IVA: $19.000
Valor Excluido: $10.000

total_amount = $119.000
total_amount_with_excluded = $129.000 ✓
```

## Ventajas de Esta Solución

1. ✅ **No interfiere** con los cálculos estándar de Odoo
2. ✅ **Compatible** con el módulo base hr_expense
3. ✅ **Claro** - Campo separado indica su propósito
4. ✅ **Flexible** - Se puede usar o no según necesidad
5. ✅ **Mantenible** - No depende de internos del módulo base

## Resumen

El error se solucionó cambiando el enfoque de "override de método compute" a "nuevo campo computado independiente". Esto mantiene la compatibilidad con Odoo y hace el código más mantenible.

---

**Estado**: ✅ Corregido y listo para usar
