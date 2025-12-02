# Guía de Instalación y Uso - Módulo HR Expense Import

## 📦 Instalación

### Requisitos Previos

El módulo **hr_expense_import** requiere que los siguientes módulos estén instalados:

1. ✅ `hr_expense` (módulo estándar de Odoo)
2. ✅ `hr_expense_credit_card` (módulo personalizado de LOGYCA)
3. ✅ `import_lead_crm_logyca` (módulo personalizado de LOGYCA - contiene el modelo `partner.product.purchase`)

### Pasos de Instalación

1. **Descomprimir el módulo**
   ```bash
   unzip hr_expense_import.zip
   ```

2. **Copiar a la carpeta de addons de Odoo**
   ```bash
   cp -r hr_expense_import /ruta/a/odoo/addons/
   ```

3. **Actualizar lista de aplicaciones**
   - Ir a Aplicaciones
   - Click en "Actualizar Lista de Aplicaciones"
   - Buscar "HR Expense Import"

4. **Instalar el módulo**
   - Click en "Instalar"

## 🚀 Uso del Módulo

### Acceso al Importador

1. Ir al menú: **Gastos > Reportes de Gastos > Importar Reportes de Gastos**
2. Se abrirá el wizard de importación

### Configuración Previa Requerida

Antes de importar, asegúrate de tener configurado:

#### 1. Proveedores (res.partner)
- Todos los proveedores deben estar creados en el sistema
- Deben tener el campo `vat` (NIT) configurado correctamente
- `parent_id` debe estar vacío (no pueden ser contactos)

#### 2. Empleados (hr.employee)
- Los empleados deben existir en el sistema
- El nombre debe coincidir exactamente con el del Excel

#### 3. Configuración de Productos por Proveedor (partner.product.purchase)
Cada proveedor debe tener configurados los productos que se usarán para los gastos:

```python
# Ejemplo de configuración:
partner.product.purchase
├── partner_id: Proveedor A
├── company_id: FUNDACION LOGYCA
├── product_id: Producto de Gasto Administrativo
├── product_type: 'ga' (Gasto Administrativo)
└── amount_type: 'total'
```

Tipos de productos:
- **ga**: Gasto Administrativo (cuando el grupo presupuestal empieza con "AD")
- **gv**: Gasto de Venta (cuando el grupo no es por defecto y no empieza con "AD")
- **co**: Costo (cuando el grupo presupuestal es por defecto)

#### 4. Grupos Presupuestales (logyca.budget_group)
- Deben estar creados por compañía
- El nombre debe coincidir con el Excel

#### 5. Cuentas Analíticas (account.analytic.account)
- Deben existir en el sistema
- Pueden estar asociadas a una compañía o ser globales

#### 6. Tarjetas de Crédito (credit.card)
- Solo necesario si se usa el modo de pago "Tarjeta de Crédito"

### Proceso de Importación

#### Paso 1: Preparar el Archivo Excel

Descarga la plantilla `template_import_expenses.xlsx` que se incluye con el módulo.

**Estructura del archivo:**

| Columna | Campo | Tipo | Ejemplo |
|---------|-------|------|---------|
| A | Compañía | Texto | FUNDACION LOGYCA |
| B | Fecha | Fecha | 24/11/2024 |
| C | Referencia | Texto | RPT-2024-001 |
| D | NIT Proveedor | Texto | 900123456 |
| E | Descripción | Texto | Compra de papelería |
| F | Desc. Exento IVA | Texto | N/A |
| G | Nombre Proveedor | Texto | Proveedor A S.A.S |
| H | Empleado | Texto | Juan Pérez |
| I | Grupo Presupuestal / Cuenta Analítica | Texto | ADMINISTRACION |
| J | Total | Número | 100000 |
| K | Exento de IVA | Número | 0 |
| L | IVA | Número | 19000 |

**⚠️ CAMBIO IMPORTANTE en v2.0.0:**
- **Columna I** ahora acepta tanto Grupos Presupuestales como Cuentas Analíticas
- El sistema detecta automáticamente qué tipo de registro es
- Busca primero como `logyca.budget_group`, luego como `account.analytic.account`
- **Ya NO existe la Columna J** (Cuenta Analítica separada)

**Importante:**
- La columna C (Referencia) agrupa los gastos en un mismo reporte
- Todos los gastos con la misma referencia se asociarán al mismo `hr.expense.sheet`

**Ejemplo:**
```
Referencia: RPT-2024-001
  ├── Gasto 1: Papelería - $100,000
  ├── Gasto 2: Internet - $150,000
  └── Gasto 3: Taxi - $50,000
  
Resultado: 1 reporte con 3 gastos = Total $300,000
```

#### Paso 2: Configurar el Wizard

1. **Seleccionar Modo de Pago**
   - Cuenta Propia del Empleado
   - Cuenta de la Compañía
   - Tarjeta de Crédito

2. **Seleccionar Tarjeta** (solo si modo = Tarjeta de Crédito)
   - Elegir la tarjeta de crédito de la lista

3. **[NUEVO v2.0.0] Agrupar por Factura** (solo visible si modo = Tarjeta de Crédito)
   - ✅ **Activado**: Al contabilizar, se generará una sola CXP al tercero de la tarjeta de crédito
   - ❌ **Desactivado** (default): Se generará una CXP por cada gasto (comportamiento estándar)
   
   **Ejemplo de Agrupación:**
   ```
   Con Agrupar por Factura = True:
   ├── Gasto 1: Proveedor A - $100 ┐
   ├── Gasto 2: Proveedor B - $200 ├→ CXP única a Banco XYZ: $450
   └── Gasto 3: Proveedor C - $150 ┘
   
   Con Agrupar por Factura = False:
   ├── Gasto 1: Proveedor A - $100 → CXP a Proveedor A: $100
   ├── Gasto 2: Proveedor B - $200 → CXP a Proveedor B: $200
   └── Gasto 3: Proveedor C - $150 → CXP a Proveedor C: $150
   ```

4. **Cargar el Archivo Excel**
   - Click en el campo "Archivo Excel"
   - Seleccionar el archivo preparado

#### Paso 3: Validar Datos

1. Click en el botón **"Validar Datos"**
2. El sistema verificará:
   - ✅ Existencia de compañías
   - ✅ Existencia de proveedores
   - ✅ Configuración de productos
   - ✅ Existencia de empleados
   - ✅ Existencia de grupos presupuestales o cuentas analíticas (Columna I)
   - ✅ No duplicación de referencias
   - ✅ Configuración de tarjeta (si aplica)

3. **Revisar el resultado:**
   - ✅ **Verde**: Todo correcto, listo para importar
   - ⚠️ **Amarillo**: Advertencias, se puede importar pero revisar
   - ❌ **Rojo**: Errores críticos, corregir antes de importar

**Ejemplo de resultado:**
```
================================================================================
✅ VALIDACIÓN EXITOSA
================================================================================
Total de referencias encontradas: 2
Total de gastos a importar: 5

El archivo está listo para ser importado.
```

#### Paso 4: Importar

1. Si la validación es exitosa, click en **"Importar"**
2. Confirmar la acción
3. El sistema creará:
   - Los reportes de gastos (`hr.expense.sheet`)
   - Los gastos individuales (`hr.expense`)
   - Las asociaciones entre ellos

4. Al finalizar, se mostrará la vista de los reportes creados

## 🔍 Validaciones y Errores Comunes

### Error: "Proveedor con NIT 'XXX' no existe"
**Solución:** Crear el proveedor con ese NIT en Contactos

### Error: "No existe configuración de productos para el proveedor"
**Solución:** Crear registro en `partner.product.purchase`:
```python
# Ir a: Configuración > Técnico > Modelos de Base de Datos
# Buscar: partner.product.purchase
# Crear registro con:
- Partner: [Proveedor]
- Company: [Compañía]
- Product: [Producto de gasto]
- Tipo: ga/gv/co según corresponda
- Tipo Total: total
```

### Error: "Empleado 'XXX' no existe"
**Solución:** 
1. Verificar que el nombre coincida exactamente
2. Crear el empleado si no existe

### Error: "Grupo Presupuestal 'XXX' no existe"
**Solución:** Crear el grupo presupuestal en la compañía correspondiente

### Error: "Ya existe un Reporte de Gastos con la referencia 'XXX'"
**Solución:** 
1. Cambiar la referencia en el Excel, o
2. Eliminar el reporte existente si es un duplicado

## 📊 Lógica de Asignación de Productos

El módulo determina automáticamente qué producto usar según el grupo presupuestal:

```python
if budget_group.by_default_group:
    # Usar producto tipo 'co' (Costo)
    product_type = 'co'
elif budget_group.name.upper().startswith('AD'):
    # Usar producto tipo 'ga' (Gasto Administrativo)
    product_type = 'ga'
else:
    # Usar producto tipo 'gv' (Gasto de Venta)
    product_type = 'gv'
```

## 🔐 Permisos Requeridos

Los usuarios necesitan uno de estos grupos:
- `hr_expense.group_hr_expense_user` (Usuario de Gastos)
- `hr_expense.group_hr_expense_team_approver` (Aprobador de Gastos)

## 📝 Notas Técnicas

### Campos Automáticos

Los siguientes campos se calculan o asignan automáticamente:

1. **product_id**: Según configuración de `partner.product.purchase`
2. **analytic_distribution**: Desde la cuenta analítica o grupo presupuestal
3. **payment_mode**: Desde el wizard (aplica a todos los gastos)
4. **credit_card_id**: Desde el wizard (solo si payment_mode = 'credit_card')

### Agrupación de Gastos

Los gastos se agrupan por la columna C (Referencia) del Excel:
- Misma referencia = Mismo reporte de gastos
- Diferente referencia = Reporte diferente

### Commits

El módulo hace commit después de crear cada reporte para evitar pérdida de datos en caso de error.

## 🆘 Soporte

Para soporte técnico, contactar a:
- **Email**: soporte@logyca.com
- **Desarrollador**: LOGYCA

## 📄 Licencia

LGPL-3

---

**Versión:** 17.0.2.0.0  
**Última actualización:** Diciembre 2024

## 🆕 Novedades v2.0.0

### Cambios Principales

1. **Columna I Inteligente**: Ahora detecta automáticamente si el valor es un grupo presupuestal o cuenta analítica
2. **Columna J Eliminada**: Ya no existe columna separada para cuentas analíticas
3. **Agrupar por Factura**: Nueva opción para generar CXP única al contabilizar con tarjeta de crédito
4. **Formato Simplificado**: 12 columnas en lugar de 13

### Migración desde v1.0.0

Si tiene archivos Excel del formato anterior:
1. Eliminar la Columna J (Cuenta Analítica)
2. Los valores de Columna J ahora van en Columna I junto con grupos presupuestales
3. Actualizar referencias: K→J, L→K, M→L
