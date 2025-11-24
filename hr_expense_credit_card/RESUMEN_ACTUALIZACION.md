# ✅ Módulo Actualizado - Valor Excluido del IVA

## Versión 17.0.2.1.0

---

## 🎯 Requerimiento Implementado

### ✨ Valor Excluido del IVA

**Descripción**: Campo adicional en el gasto para registrar valores que NO forman parte de la base del IVA pero SÍ se suman al total del gasto.

---

## 📦 Cambios Realizados

### 1. Nuevos Campos en hr.expense

#### Campo 1: amount_tax_excluded (Monetario)
**Nombre**: "Valor Excluido del IVA"

**Características**:
- ✅ Tipo: Monetary
- ✅ Valor por defecto: 0.00
- ✅ NO afecta la base del IVA
- ✅ SÍ se suma al total del gasto
- ✅ Tracking activado

#### Campo 2: amount_tax_excluded_description (Texto)
**Nombre**: "Descripción Valor Excluido"

**Características**:
- ✅ Tipo: Char
- ✅ Opcional
- ✅ Visible solo cuando amount_tax_excluded > 0
- ✅ Tracking activado

---

## 🔢 Lógica de Cálculo

### Fórmula del Total:

```
Total del Gasto = (Cantidad × Precio Unitario) + Impuestos + Valor Excluido
```

### Importante:
- ❌ El IVA NO se calcula sobre el valor excluido
- ✅ El IVA se calcula SOLO sobre (Cantidad × Precio Unitario)
- ✅ El valor excluido se suma AL FINAL

---

## 💡 Ejemplo Práctico

### Escenario: Almuerzo con Propina

**Datos de Entrada**:
```
Categoría: Almuerzos
Cantidad: 1
Precio Unitario: $100.000
Impuestos: IVA 19%
⭐ Valor Excluido: $10.000
⭐ Descripción: "Propina"
```

**Cálculo**:
```
Base: $100.000
IVA (19% de $100.000): $19.000
Valor Excluido: $10.000
─────────────────────────────
Total: $129.000
```

**Asiento Contable**:
```
┌────────────────────────────────────────────────────┐
│ Cuenta           │ Tercero   │ Débito │ Crédito   │
├────────────────────────────────────────────────────┤
│ 510506 Almuerzos │ Rest. A   │100.000 │      0.00 │ ← Base
│ 240801 IVA       │ Rest. A   │ 19.000 │      0.00 │ ← IVA
│ 510506 Almuerzos │ Rest. A   │ 10.000 │      0.00 │ ← Propina
│ 220505 CXP       │ Banco XYZ │   0.00 │  129.000  │ ← CXP
├────────────────────────────────────────────────────┤
│ TOTAL                        │129.000 │  129.000  │
└────────────────────────────────────────────────────┘
```

**Observaciones**:
- ✅ El IVA es $19.000 (19% de $100.000)
- ✅ La propina NO afecta el cálculo del IVA
- ✅ La propina genera una línea de débito adicional
- ✅ El total de la CXP incluye todo: $129.000

---

## 🖥️ Interfaz de Usuario

### Vista Formulario (hr.expense)

**Ubicación**: Después del campo "Impuestos"

```
┌─────────────────────────────────────────────┐
│ Categoría: [Almuerzos ▼]                    │
│ Proveedor: [Restaurante Central ▼]          │
│ Cantidad: [1]                               │
│ Precio Unitario: [$100.000]                 │
│ Impuestos: [IVA 19% ▼]                      │
│                                             │
│ ⭐ Valor Excluido del IVA: [$10.000]        │
│ ⭐ Descripción: [Propina________________]   │
│                                             │
│ Total: $129.000                             │
└─────────────────────────────────────────────┘
```

**Comportamiento**:
- Si amount_tax_excluded = 0 → La descripción está oculta
- Si amount_tax_excluded > 0 → La descripción se muestra

### Vista Lista (Tree)

**Nueva Columna**: "Valor Excluido del IVA"
- Opcional (oculta por defecto)
- Con suma al pie de columna
- Widget monetario

---

## 📊 Contabilización Detallada

### Por Cada Gasto se Generan:

1. **Línea Base**:
   - Cuenta: Cuenta del gasto
   - Monto: Cantidad × Precio Unitario
   - Proveedor: Proveedor del gasto

2. **Líneas de Impuestos**:
   - Calculados sobre la base (sin valor excluido)
   - Una línea por cada impuesto

3. **Línea de Valor Excluido** (solo si > 0):
   - Cuenta: Cuenta del gasto (misma que la base)
   - Monto: amount_tax_excluded
   - Proveedor: Proveedor del gasto
   - Descripción en el nombre de la línea

4. **Línea CXP**:
   - Cuenta: Cuenta de la tarjeta de crédito
   - Monto: Total (base + impuestos + valor excluido)
   - Tercero: Tercero de la tarjeta

---

## 📝 Casos de Uso Comunes

### 1. Propinas
```
Base: $50.000
Propina: $5.000
Total: $55.000
```

### 2. Servicio a la Habitación
```
Base: $100.000
IVA (19%): $19.000
Servicio: $15.000
Total: $134.000
```

### 3. Cargos Adicionales No Gravados
```
Base: $200.000
IVA (19%): $38.000
Cargo adicional: $20.000
Total: $258.000
```

### 4. Descuentos en Efectivo
```
Base: $100.000
IVA (19%): $19.000
Descuento: -$10.000
Total: $109.000
```

---

## ✅ Verificación Post-Instalación

### Checklist:

1. **Campos Visibles**:
   - [ ] Campo "Valor Excluido del IVA" visible en formulario
   - [ ] Campo "Descripción" visible cuando valor > 0
   - [ ] Columna opcional en vista lista

2. **Cálculo Correcto**:
   - [ ] Total = Base + IVA + Valor Excluido
   - [ ] IVA se calcula SOLO sobre la base
   - [ ] Valor excluido NO afecta el IVA

3. **Contabilización**:
   - [ ] Línea adicional por valor excluido
   - [ ] CXP incluye el valor excluido
   - [ ] Asiento cuadra correctamente

---

## 🔄 Flujo de Trabajo

### Paso 1: Crear Gasto con Valor Excluido

```
Gastos > Mis Gastos > Crear

1. Categoría: Almuerzos
2. Proveedor: Restaurante
3. Cantidad: 1
4. Precio Unitario: $100.000
5. Impuestos: IVA 19%
6. ⭐ Valor Excluido: $10.000
7. ⭐ Descripción: "Propina"
8. Guardar

→ Total calculado: $129.000
```

### Paso 2: Crear Reporte y Contabilizar

```
Gastos > Mis Reportes > Crear

1. Agregar gasto
2. Seleccionar tarjeta de crédito
3. Aprobar
4. Contabilizar

→ Sistema genera asiento con línea adicional
→ CXP incluye el valor excluido
```

---

## 🆙 Actualización desde Versión Anterior

### Gastos Existentes:
- ✅ Automáticamente tienen amount_tax_excluded = 0
- ✅ No requieren modificación
- ✅ Continúan funcionando igual

### Nuevos Gastos:
- ✅ Pueden usar el nuevo campo
- ✅ Valor por defecto: 0
- ✅ Opcional su uso

---

## 📂 Archivos Modificados

### Modelos:
- ✅ `models/hr_expense.py` - Agregados campos y métodos compute

### Vistas:
- ✅ `views/hr_expense_views.xml` - Campos en formulario y lista

### Lógica de Negocio:
- ✅ `models/hr_expense_sheet.py` - Contabilización actualizada

---

## 📊 Comparación: Antes vs Ahora

### ANTES (v17.0.2.0.0):
```
Gasto:
- Base: $100.000
- IVA: $19.000
- Total: $119.000

Asiento:
Débito:  $100.000 (Base)
Débito:  $ 19.000 (IVA)
Crédito: $119.000 (CXP)
```

### AHORA (v17.0.2.1.0):
```
Gasto:
- Base: $100.000
- IVA: $19.000
- Valor Excluido: $10.000
- Total: $129.000

Asiento:
Débito:  $100.000 (Base)
Débito:  $ 19.000 (IVA)
Débito:  $ 10.000 (Valor Excluido) ⭐
Crédito: $129.000 (CXP)
```

---

## 🎯 Ventajas de la Implementación

1. ✅ **Flexible**: Valor por defecto 0 (no afecta gastos normales)
2. ✅ **Preciso**: IVA calculado correctamente sobre la base
3. ✅ **Trazable**: Línea separada en el asiento contable
4. ✅ **Descriptivo**: Campo para explicar el concepto
5. ✅ **Compatible**: Funciona con gastos existentes

---

## 📞 Información

**Empresa**: LOGYCA  
**Versión**: 17.0.2.1.0  
**Fecha**: 2024-11-24  
**Compatible**: Odoo 17.0  

---

## ✨ Resumen de Cambios

**v17.0.2.1.0**:
- ✅ Campo `amount_tax_excluded` agregado
- ✅ Campo `amount_tax_excluded_description` agregado
- ✅ Método `_compute_total_amount()` actualizado
- ✅ Método `_compute_total_amount_currency()` actualizado
- ✅ Contabilización con línea adicional
- ✅ Vistas actualizadas (formulario y lista)
- ✅ Documentación completa incluida

---

**🎉 Funcionalidad Lista para Usar**

El módulo está actualizado y listo para instalarse/actualizarse.

📦 [Descargar Módulo](computer:///mnt/user-data/outputs/hr_expense_credit_card.zip)
