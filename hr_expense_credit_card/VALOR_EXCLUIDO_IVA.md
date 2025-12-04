# Nueva Funcionalidad: Valor Excluido del IVA

## Versión 17.0.2.1.0

---

## 📋 Descripción

Se ha agregado la capacidad de registrar valores que no forman parte de la base gravable del IVA pero que se suman al total del gasto.

### Casos de Uso Comunes:
- **Propinas**: Valor adicional que no es gravado con IVA
- **Servicios adicionales**: Cargos no gravados
- **Descuentos en efectivo**: Valores que no afectan la base del IVA
- **Comisiones especiales**: Cargos adicionales no gravables

---

## 🆕 Campos Agregados

### En el modelo hr.expense:

#### 1. amount_tax_excluded (Monetary)
**Nombre**: "Valor Excluido del IVA"

**Características**:
- Tipo: Monetario
- Valor por defecto: 0.00
- Se suma al total del gasto
- NO afecta la base del IVA
- Tracking: Sí

**Descripción**: Valor que no hace parte de la base del IVA pero se suma al total del gasto.

#### 2. amount_tax_excluded_description (Char)
**Nombre**: "Descripción Valor Excluido"

**Características**:
- Tipo: Texto corto
- Opcional
- Tracking: Sí
- Se muestra solo si amount_tax_excluded > 0

**Descripción**: Descripción del concepto del valor excluido del IVA.

---

## 💡 Cómo Funciona

### Ejemplo Práctico:

**Escenario**: Almuerzo de negocios con propina

**Datos**:
- Precio del almuerzo: $100.000
- IVA (19%): $19.000
- Propina (no gravada): $10.000

**Registro en el Gasto**:
```
Categoría: Almuerzos
Cantidad: 1
Precio Unitario: $100.000
Impuestos: IVA 19%
Valor Excluido del IVA: $10.000
Descripción Valor Excluido: "Propina"
```

**Cálculo del Total**:
```
Base: $100.000
IVA (19% de $100.000): $19.000
Valor Excluido: $10.000
------------------------
Total del Gasto: $129.000
```

**Asiento Contable Generado**:
```
┌────────────────────────────────────────────────────────┐
│ Cuenta           │ Tercero    │ Débito │ Crédito │ Desc│
├────────────────────────────────────────────────────────┤
│ 510506 Almuerzos │ Rest. A    │100.000 │    0.00 │Base │
│ 240801 IVA       │ Rest. A    │ 19.000 │    0.00 │IVA  │
│ 510506 Almuerzos │ Rest. A    │ 10.000 │    0.00 │Prop │
│ 220505 CXP       │ Banco XYZ  │   0.00 │129.000  │CXP  │
├────────────────────────────────────────────────────────┤
│ TOTAL                         │129.000 │129.000  │     │
└────────────────────────────────────────────────────────┘
```

**Observaciones**:
- El IVA se calcula solo sobre $100.000 (base)
- La propina de $10.000 NO afecta el cálculo del IVA
- El valor excluido genera una línea de débito adicional
- El total de la CXP es $129.000 (incluye todo)

---

## 📱 Interfaz de Usuario

### Vista Formulario:

**Ubicación**: Después del campo "Impuestos" (tax_ids)

**Campos visibles**:
1. **Valor Excluido del IVA**: 
   - Widget monetario
   - Placeholder: "0.00"
   - Siempre visible

2. **Descripción Valor Excluido**:
   - Input de texto
   - Placeholder: "Ej: Propina, servicio adicional, etc."
   - Visible solo cuando amount_tax_excluded > 0

### Vista Lista (Tree):

**Columna**: "Valor Excluido del IVA"
- Opcional (hide por defecto)
- Widget monetario
- Suma total al pie de columna

---

## 🔢 Cálculos Implementados

### Método: _compute_total_amount()

**Lógica**:
```python
Total del Gasto = (Cantidad × Precio Unitario) + Impuestos + Valor Excluido
```

**Ejemplo**:
```
Cantidad: 1
Precio Unitario: $100.000
IVA (19%): $19.000
Valor Excluido: $10.000

Total = (1 × $100.000) + $19.000 + $10.000 = $129.000
```

### Método: _compute_total_amount_currency()

**Lógica**: Igual que _compute_total_amount pero en la moneda del gasto.

---

## 📊 Contabilización

### Generación de Líneas en el Asiento:

1. **Línea Base del Gasto**:
   - Cuenta: Cuenta del gasto
   - Proveedor: Proveedor del gasto
   - Monto: Cantidad × Precio Unitario (sin valor excluido)

2. **Líneas de Impuestos**:
   - Calculados sobre la base (sin valor excluido)
   - Una línea por cada impuesto

3. **Línea de Valor Excluido** (si existe):
   - Cuenta: Cuenta del gasto (misma que la base)
   - Proveedor: Proveedor del gasto
   - Monto: amount_tax_excluded
   - Descripción: "Nombre del gasto - Descripción valor excluido"

4. **Línea CXP**:
   - Cuenta: Cuenta de la tarjeta de crédito
   - Tercero: Tercero de la tarjeta
   - Monto: Total (base + impuestos + valor excluido)

---

## ✅ Validaciones

### Campos Obligatorios:
- `amount_tax_excluded`: NO (por defecto es 0)
- `amount_tax_excluded_description`: NO (opcional)

### Reglas de Negocio:
1. Si `amount_tax_excluded` = 0 → La descripción se oculta
2. Si `amount_tax_excluded` > 0 → Se recomienda llenar la descripción
3. El valor excluido NO afecta el cálculo de impuestos
4. El valor excluido SÍ se suma al total del gasto
5. El valor excluido genera una línea adicional en el asiento

---

## 🔄 Flujo de Trabajo Actualizado

### 1. Crear Gasto con Valor Excluido

**Ruta**: Gastos > Mis Gastos > Crear

```
1. Categoría: Almuerzos
2. Proveedor: Restaurante Central
3. Cantidad: 1
4. Precio Unitario: $100.000
5. Impuestos: IVA 19%
6. ⭐ Valor Excluido del IVA: $10.000
7. ⭐ Descripción: "Propina"
8. Total calculado: $129.000
9. Guardar
```

### 2. Crear Reporte y Contabilizar

El proceso es el mismo, el sistema automáticamente:
- Incluye el valor excluido en el total
- Genera la línea adicional en el asiento
- Calcula correctamente los impuestos sobre la base

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Almuerzo con Propina

**Datos**:
- Base: $50.000
- Propina: $5.000
- Sin IVA

**Asiento**:
```
Débito:  510506 - Rest. A  - $50.000 (Almuerzo)
Débito:  510506 - Rest. A  - $ 5.000 (Almuerzo - Propina)
Crédito: 220505 - Banco XYZ - $55.000 (CXP)
```

### Ejemplo 2: Taxi con Propina y IVA

**Datos**:
- Base: $30.000
- IVA (19%): $5.700
- Propina: $3.000

**Asiento**:
```
Débito:  510515 - Taxi B    - $30.000 (Taxi)
Débito:  240801 - Taxi B    - $ 5.700 (IVA)
Débito:  510515 - Taxi B    - $ 3.000 (Taxi - Propina)
Crédito: 220505 - Banco XYZ - $38.700 (CXP)
```

### Ejemplo 3: Hotel con Servicios Adicionales

**Datos**:
- Base (habitación): $200.000
- IVA (19%): $38.000
- Servicio a la habitación (no gravado): $15.000

**Asiento**:
```
Débito:  510520 - Hotel A   - $200.000 (Hotel)
Débito:  240801 - Hotel A   - $ 38.000 (IVA)
Débito:  510520 - Hotel A   - $ 15.000 (Hotel - Servicio habitación)
Crédito: 220505 - Banco XYZ - $253.000 (CXP)
```

---

## 🔍 Casos Especiales

### Caso 1: Valor Excluido Negativo (Descuento)

Si necesitas registrar un descuento que no afecta el IVA:

**Datos**:
- Base: $100.000
- IVA (19%): $19.000
- Descuento en efectivo: -$5.000

**Registro**:
```
Precio Unitario: $100.000
IVA: 19%
Valor Excluido: -$5.000
Descripción: "Descuento efectivo"
Total: $114.000
```

### Caso 2: Sin Valor Excluido

Si no hay valor excluido, simplemente:
- Dejar en 0 el campo "Valor Excluido del IVA"
- No llenar la descripción
- El comportamiento es el mismo que antes

---

## 🆙 Migración desde Versión Anterior

### Gastos Existentes:

Todos los gastos creados con versiones anteriores:
- Tendrán `amount_tax_excluded` = 0 por defecto
- No tendrán descripción
- Su total permanece igual
- No requieren modificación

### Reportes Pendientes:

Los reportes pendientes de contabilizar:
- Funcionan normalmente
- Si tienen gastos con valor excluido > 0, se contabilizarán correctamente

---

## 📊 Reportes y Análisis

### En la Vista Lista:

Puedes ver el total de valores excluidos:
```
Gastos > Mis Gastos > Vista Lista
→ Activar columna "Valor Excluido del IVA"
→ Ver suma total al pie de la columna
```

### En el Reporte de Gastos:

El total del reporte incluye automáticamente los valores excluidos de todos los gastos.

---

## ⚠️ Consideraciones Importantes

1. **Base del IVA**: El valor excluido NO forma parte de la base gravable
2. **Total del Gasto**: El valor excluido SÍ se suma al total
3. **Contabilización**: Genera línea adicional con la misma cuenta del gasto
4. **Descripción**: Recomendada pero no obligatoria
5. **Valor por Defecto**: 0 (no afecta gastos sin valor excluido)

---

## 🐛 Troubleshooting

### Problema: El IVA se está calculando sobre el valor excluido

**Causa**: El sistema está funcionando correctamente. El IVA solo se calcula sobre el precio unitario × cantidad.

**Verificación**:
```
Base: $100.000
IVA esperado: $19.000 (19% de $100.000)
Valor excluido: $10.000
Total: $129.000

✓ IVA = $19.000 (correcto)
✗ IVA = $24.510 (incorrecto - incluiría valor excluido)
```

### Problema: El total no incluye el valor excluido

**Causa**: El módulo no está actualizado correctamente.

**Solución**:
```bash
./odoo-bin -d tu_database -u hr_expense_credit_card --stop-after-init
```

### Problema: No veo los campos nuevos

**Causa**: Cache del navegador o actualización incompleta.

**Solución**:
1. Ctrl + F5 (refrescar navegador)
2. Verificar que el módulo está en versión 17.0.2.1.0
3. Actualizar módulo si es necesario

---

## 📞 Soporte

**Empresa**: LOGYCA  
**Website**: https://www.logyca.com  
**Versión**: 17.0.2.1.0

---

## ✨ Changelog

### v17.0.2.1.0 (2024-11-24)
- ✅ Agregado campo `amount_tax_excluded`
- ✅ Agregado campo `amount_tax_excluded_description`
- ✅ Actualizado cálculo de total para incluir valor excluido
- ✅ Actualizada contabilización para generar línea adicional
- ✅ Agregados campos en vistas formulario y lista

---

**Funcionalidad lista para usar** ✅
