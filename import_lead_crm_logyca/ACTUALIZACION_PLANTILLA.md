# Actualización de Plantilla Excel - Órdenes de Compra

## 📊 Nueva Estructura de Columnas

La plantilla Excel debe actualizarse con la siguiente estructura:

### Columnas Requeridas (Orden de índices):

| Índice | Columna | Descripción | Ejemplo |
|--------|---------|-------------|---------|
| 0 | Compañía | Nombre exacto de la compañía en Odoo | LOGYCA |
| 1 | Fecha | Fecha del documento | 2025-01-11 |
| 2 | Referencia | Referencia de la orden de compra | REF-2025-001 |
| 3 | NIT Proveedor | NIT del proveedor sin puntos ni guiones | 900123456 |
| **4** | **Descripción** | **NUEVA - Descripción personalizada de la línea** | **Servicio de consultoría especializada** |
| 5 | Grupo Presupuestal | Nombre del grupo presupuestal | GP-ADMIN-001 |
| 6 | Cuenta Analítica | Nombre de la cuenta analítica | PROYECTO-X |
| 7 | Consumo | Valor de consumo (numérico) | 1000000 |
| 8 | Descuento | Valor de descuento (numérico) | -50000 |
| 9 | Total | Valor total (numérico) | 950000 |
| 10 | IVA | Valor de IVA (numérico) | 180500 |

## 🆕 Cambio Principal - Columna "Descripción"

### ¿Qué es?
La nueva columna "Descripción" (índice 4) permite personalizar el texto que aparecerá en el campo `name` de cada línea de la orden de compra.

### ¿Por qué es útil?
Antes, el campo `name` de la línea se llenaba automáticamente con el nombre del producto. Ahora puedes especificar una descripción más detallada o personalizada.

### Comportamiento:
- **Si la columna tiene contenido**: Se usa ese texto como descripción de la línea
- **Si la columna está vacía**: Se usa el nombre del producto por defecto

### Ejemplos de Uso:

#### Ejemplo 1: Descripción Personalizada
```excel
| ... | Descripción | ... |
|-----|-------------|-----|
| ... | Licencia de software Office 365 - Plan E3 - Renovación anual | ... |
```
→ La línea mostrará: "Licencia de software Office 365 - Plan E3 - Renovación anual"

#### Ejemplo 2: Vacío (usa nombre de producto)
```excel
| ... | Descripción | ... |
|-----|-------------|-----|
| ... |             | ... |
```
→ La línea mostrará: "Software Office" (nombre del producto configurado)

## 📝 Plantilla Excel Actualizada

### Estructura de Encabezados:

```
A        | B      | C          | D              | E           | F                  | G                | H       | I         | J     | K
Compañía | Fecha  | Referencia | NIT Proveedor  | Descripción | Grupo Presupuestal | Cuenta Analítica | Consumo | Descuento | Total | IVA
```

### Ejemplo de Datos:

```excel
LOGYCA | 2025-01-11 | REF-2025-001 | 900123456 | Servicio de consultoría estratégica para proyecto X | GP-ADMIN-001 | PROYECTO-X | 5000000 | 0 | 5000000 | 950000
LOGYCA | 2025-01-11 | REF-2025-001 | 900123456 | Licencias Microsoft 365 E3 - 50 usuarios - Año 2025 | GP-TECNOLOGIA | PROYECTO-X | 0 | 0 | 15000000 | 2850000
LOGYCA | 2025-01-11 | REF-2025-001 | 900123456 | Descuento por pronto pago | GP-TECNOLOGIA | PROYECTO-X | 0 | -500000 | 0 | 0
```

## 🔄 Migración de Plantillas Existentes

Si tienes plantillas viejas, sigue estos pasos:

1. **Abrir plantilla existente**
2. **Insertar nueva columna** después de "NIT Proveedor" (índice 4)
3. **Nombrar la columna**: "Descripción"
4. **Completar datos** (opcional, puede quedar vacía)
5. **Verificar orden** de todas las columnas según tabla anterior
6. **Guardar** con nuevo nombre: "Plantilla_Cargue_Compras_v1.2.xlsx"

## ⚠️ Importante

- **No cambiar el orden de las columnas** - El código lee por índice
- **La columna Descripción es opcional** - Puede quedar vacía
- **Usar formato numérico** para columnas de valores (Consumo, Descuento, Total, IVA)
- **NIT sin formato** - Solo números, sin puntos ni guiones

## ✅ Lista de Verificación

Antes de usar la nueva plantilla, verifica:

- [ ] La columna "Descripción" está en la posición correcta (índice 4)
- [ ] Los encabezados coinciden exactamente con los mostrados arriba
- [ ] Los valores numéricos no tienen formato de texto
- [ ] Los nombres de compañías, grupos y cuentas son exactos
- [ ] Has probado con el botón "Validar Datos" antes de importar

## 📁 Ubicación de la Plantilla

La plantilla actualizada debe estar en:
```
import_lead_crm_logyca/static/xls/Plantilla_Cargue_Compras.xlsx
```

## 🔗 Descarga en Odoo

La plantilla se descarga desde:
**Compras > Operaciones > Purchase Lead Import File Wizard > Descargar Plantilla**

---

**Nota**: Actualizar la plantilla Excel física en la carpeta `/static/xls/` del módulo con la nueva estructura.
