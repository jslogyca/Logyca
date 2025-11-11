# Módulo Import Lead CRM LOGYCA - Versión 1.2

## 📋 Descripción

Módulo mejorado para la importación masiva de Leads CRM y Órdenes de Compra en Odoo 17/18.

## 🆕 Nuevas Funcionalidades v1.2

### 1. ✅ Nueva Columna "Descripción"
- **Ubicación**: Columna índice 4 en el archivo Excel
- **Función**: El contenido de esta celda se inserta en el campo `name` de cada línea de la orden de compra
- **Beneficio**: Permite personalizar la descripción de cada línea sin depender del nombre del producto

**Ejemplo en Excel:**
```
| Compañía | Fecha | Referencia | NIT | Descripción | Grupo Presupuestal | ... |
|----------|-------|------------|-----|-------------|-------------------|-----|
| LOGYCA   | ...   | REF-001    | ... | Servicio de consultoría especial | GP-001 | ... |
```

### 2. ✅ Botón de Validación
Un nuevo botón **"Validar Datos"** que realiza las siguientes validaciones ANTES de importar:

#### Validaciones Implementadas:

**a) Validación de Grupo Presupuestal**
- Verifica que cada grupo presupuestal mencionado existe en el sistema
- Valida la correspondencia con la compañía especificada

**b) Validación de Cuenta Analítica**
- Confirma la existencia de todas las cuentas analíticas
- Verifica compatibilidad con la compañía o si son globales

**c) Validación de Proveedor**
- Verifica que el NIT del proveedor existe en el sistema
- Confirma que el contacto es de tipo proveedor

**d) Validación de Referencias Duplicadas**
- Busca órdenes de compra existentes con la misma referencia
- Previene duplicación de pedidos para el mismo proveedor y compañía

#### Resultado de la Validación

El botón muestra un informe detallado con:
- ✓ Número de registros a procesar
- ✓ Errores encontrados (si existen)
- ✓ Advertencias (si existen)
- ✓ Confirmación de que los datos son correctos

**Si hay errores**, el sistema muestra:
```
=== RESULTADO DE LA VALIDACIÓN ===

✗ SE ENCONTRARON ERRORES

Total de errores: 3

ERRORES:
  • Fila 2: Proveedor con NIT '900123456' no existe en el sistema
  • Fila 3: Grupo Presupuestal 'GP-XXX' no existe para la compañía LOGYCA
  • Fila 5: Cuenta Analítica 'AN-999' no existe

Por favor corrija estos problemas antes de importar.
```

**Si todo está correcto**, muestra:
```
=== RESULTADO DE LA VALIDACIÓN ===

✓ VALIDACIÓN EXITOSA

Todos los datos son correctos. Puede proceder con la importación.

- Registros a procesar: 15
- Proveedor: 900123456
- Referencia: REF-2025-001
```

## 📥 Instalación

1. Copiar la carpeta `import_lead_crm_logyca` en el directorio de addons de Odoo
2. Actualizar la lista de aplicaciones
3. Buscar "Import Leads CRM - LOGYCA"
4. Instalar o actualizar el módulo

## 🔧 Uso

### Importar Órdenes de Compra

1. Ir a **Compras > Operaciones > Purchase Lead Import File Wizard**
2. Descargar la plantilla Excel
3. Completar la plantilla con los datos:
   - Columna 0: Compañía
   - Columna 1: Fecha
   - Columna 2: Referencia
   - Columna 3: NIT Proveedor
   - **Columna 4: Descripción (NUEVA)**
   - Columna 5: Grupo Presupuestal
   - Columna 6: Cuenta Analítica
   - Columna 7: Consumo
   - Columna 8: Descuento
   - Columna 9: Total
   - Columna 10: IVA

4. **Paso 1: VALIDAR**
   - Cargar el archivo Excel
   - Hacer clic en **"Validar Datos"**
   - Revisar el informe de validación
   - Corregir errores si existen

5. **Paso 2: IMPORTAR**
   - Una vez validado correctamente
   - Hacer clic en **"Import"**
   - El sistema creará la orden de compra con todas sus líneas

## 🔍 Flujo de Trabajo Recomendado

```
1. Preparar archivo Excel con datos
      ↓
2. Cargar archivo en el wizard
      ↓
3. Clic en "Validar Datos"
      ↓
4. ¿Hay errores? → SÍ → Corregir archivo y volver al paso 2
      ↓ NO
5. Clic en "Import"
      ↓
6. ✓ Orden de compra creada exitosamente
```

## ⚠️ Notas Importantes

1. **La columna "Descripción" es opcional**: Si se deja vacía, se usará el nombre del producto por defecto
2. **Siempre validar antes de importar**: Esto previene errores y pérdida de tiempo
3. **Referencias únicas**: El sistema alerta si ya existe una orden con la misma referencia
4. **Grupos presupuestales especiales**: El sistema diferencia grupos que comienzan con "AD" para clasificación automática

## 🐛 Solución de Problemas

### Error: "Grupo Presupuestal no existe"
- **Solución**: Verificar que el nombre del grupo sea exacto (respeta mayúsculas/minúsculas)
- Crear el grupo presupuestal en el sistema si no existe

### Error: "Proveedor no existe"
- **Solución**: Verificar el NIT en el sistema
- Crear el contacto como proveedor si es necesario

### Error: "Ya existe una orden con esta referencia"
- **Solución**: Cambiar la referencia en el Excel o verificar si es un duplicado real
- Revisar la orden existente antes de crear una nueva

## 📝 Changelog

### Versión 1.2 (2025-01-11)
- ✅ Agregada columna "Descripción" para líneas de OC
- ✅ Botón de validación de datos pre-importación
- ✅ Validación de grupos presupuestales
- ✅ Validación de cuentas analíticas
- ✅ Validación de proveedores
- ✅ Validación de referencias duplicadas
- ✅ Mejora en mensajes de error
- ✅ Documentación actualizada

### Versión 1.1 (Anterior)
- Importación masiva de Leads
- Importación masiva de Órdenes de Compra
- Mapeo de productos por proveedor

## 👥 Soporte

Para soporte técnico contactar al equipo de desarrollo de LOGYCA.

---

**Desarrollado por:** LOGYCA  
**Licencia:** LGPL-3  
**Versión Odoo:** 17.0+ / 18.0+
