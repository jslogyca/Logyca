# 📘 GUÍA RÁPIDA DE USUARIO
## Descuentos Comerciales Condicionados - Generación de Notas Crédito

---

## 🎯 ¿Qué hace este módulo?

Este módulo ofrece **dos formas de trabajar** con descuentos comerciales condicionados:

### **Opción 1: Solo Reporte Excel** 📊
Genera un reporte detallado en Excel de todos los descuentos condicionados (cuenta 530535) **sin crear documentos**. Útil para:
- Revisar descuentos antes de procesarlos
- Análisis y auditoría
- Reportes gerenciales
- Planificación contable

### **Opción 2: Proceso Automático Completo** 🚀
Por cada descuento registrado en la cuenta 530535, el sistema:

1. ✅ Crea automáticamente la nota crédito
2. ✅ Genera el comprobante contable de reversión
3. ✅ Concilia ambos documentos
4. ✅ Genera un reporte Excel detallado

**Todo en solo unos clics, sin necesidad de crear documentos manualmente.**

---

## 🚀 INICIO RÁPIDO

### ⚡ Opción A: Solo Reporte Excel (Más Rápido - 2 Pasos)

#### PASO 1: Abrir el Módulo
```
📍 Ubicación: Contabilidad → Informes → Reportes → Descuentos Condicionados para NC
```

#### PASO 2: Configurar y Generar
1. Seleccionar el **Año** a procesar (ejemplo: 2025)
2. Seleccionar la **Cuenta de Descuentos (530535)**
3. Hacer clic en **"Generar Solo Reporte Excel"**
4. ✅ Descargar el reporte

**⏱️ Tiempo:** 1-2 minutos

---

### 🚀 Opción B: Proceso Completo con NC y Comprobantes (4 Pasos)

#### PASO 1: Configuración Inicial (Solo primera vez)

##### Crear Diario de Reversión
```
📍 Ubicación: Contabilidad → Configuración → Diarios
```

1. Clic en **"Nuevo"**
2. Configurar:
   - **Nombre**: Reversión Descuentos Condicionados
   - **Tipo**: Miscellaneous (General)
   - **Código Corto**: REVDC
3. Guardar

##### Verificar Cuenta 530535
```
📍 Ubicación: Contabilidad → Configuración → Plan de Cuentas
```

1. Buscar cuenta: **530535**
2. Verificar que exista y esté activa
3. Si no existe, crearla como cuenta de gastos

---

#### PASO 2: Ejecutar el Proceso

##### 2.1 Abrir el Módulo
```
📍 Ubicación: Contabilidad → Informes → Reportes → Descuentos Condicionados para NC
```

##### 2.2 Configurar Parámetros

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Año** | Año a procesar | 2025 |
| **Diario para Comprobantes** | Diario creado en Paso 1 | Reversión Descuentos Condicionados |
| **Cuenta de Descuentos** | Cuenta 530535 | 530535 - Descuentos Comerciales Condicionados |

##### 2.3 Cargar Facturas

1. Clic en **"Cargar Facturas para Procesar NC"**
2. El sistema mostrará:
   - ✅ Total de facturas encontradas
   - ⚠️ Total excluidas (ya procesadas)
   - 📋 Lista detallada de facturas elegibles

---

#### PASO 3: Seleccionar y Procesar

#### 3.1 Revisar Facturas

El sistema muestra una tabla con:

| Columna | Descripción |
|---------|-------------|
| **☑️ Seleccionar** | Checkbox para seleccionar/deseleccionar |
| **Factura** | Número de factura |
| **Fecha** | Fecha de la factura |
| **Cliente** | Nombre del cliente |
| **Valor Descuento** | Monto del descuento condicionado |
| **Comprobante Pago** | Número del pago relacionado |

#### 3.2 Opciones de Selección

**Opción A: Procesar todas las facturas**
- Dejar todas seleccionadas (vienen marcadas por defecto)
- Ir directamente a "Procesar"

**Opción B: Procesar solo una factura**
1. Clic en **"Deseleccionar Todas"**
2. Marcar manualmente la factura deseada
3. Ir a "Procesar"

**Opción C: Procesar algunas facturas**
- Desmarcar individualmente las que NO se van a procesar
- Dejar marcadas solo las deseadas
- Ir a "Procesar"

#### 3.3 Procesar

1. Verificar que las facturas correctas estén seleccionadas
2. Clic en **"Procesar Notas Crédito"**
3. Confirmar en el mensaje de alerta
4. ⏳ Esperar a que el sistema procese...

---

## ✅ RESULTADO

### Documentos Creados

Por cada factura procesada, se crean automáticamente:

#### 1️⃣ Nota Crédito
```
📍 Ubicación: Contabilidad → Clientes → Notas Crédito
```
- **Tipo**: Nota Crédito de Cliente
- **Monto**: Valor del descuento
- **Estado**: Publicada
- **Marcada como**: NC por Descuento Condicionado ✓

#### 2️⃣ Comprobante de Reversión
```
📍 Ubicación: Contabilidad → Contabilidad → Asientos Contables
```
- **Diario**: [Diario configurado]
- **Línea 1**: Débito a CXC Cliente
- **Línea 2**: Crédito a Cuenta 530535
- **Estado**: Publicada
- **Conciliado**: Con la Nota Crédito ✓

### Reporte Excel

Descargue el reporte haciendo clic en **"Descargar Excel"**

**Contenido del reporte:**

| Información de Factura | Información de Proceso |
|----------------------|----------------------|
| Factura de Venta | ✅ Nota Crédito (número) |
| Fecha Factura | ✅ Valor NC |
| Cliente | ✅ Comprobante Reversión (número) |
| NIT | ✅ Valor Reversión |
| Valores Factura | ✅ Estado (Procesado/Error) |
| Comprobante Pago | ⚠️ Error (si aplica) |

---

## 🎨 INTERFAZ VISUAL

### Estados del Proceso

El wizard muestra 3 pantallas diferentes según el estado:

#### 🟦 Estado 1: CONFIGURACIÓN
- Campos para ingresar año y seleccionar cuentas
- Botón: **"Cargar Facturas"**

#### 🟨 Estado 2: SELECCIÓN
- Tabla con facturas encontradas
- Checkboxes de selección
- Botones:
  - **"Procesar Notas Crédito"**
  - **"Seleccionar Todas"**
  - **"Deseleccionar Todas"**
  - **"Volver"**

#### 🟩 Estado 3: COMPLETADO
- Mensaje de éxito
- Tabla con resultados
- Indicadores de estado por factura
- Botones:
  - **"Descargar Excel"**
  - **"Generar Otro Proceso"**

---

## ⚡ CONSEJOS PRÁCTICOS

### ✅ Mejores Prácticas

1. **Revisar antes de procesar**
   - Verificar que las facturas sean correctas
   - Confirmar los montos de descuento
   - Revisar que los clientes sean los esperados

2. **Procesamiento gradual**
   - Para grandes volúmenes, procesar en lotes
   - Deseleccionar todas y procesar por grupos

3. **Descarga del reporte**
   - Siempre descargar el reporte Excel
   - Guardar como respaldo del proceso
   - Usar para conciliación contable

4. **Verificación posterior**
   - Revisar las notas crédito creadas
   - Verificar la conciliación
   - Validar los comprobantes de reversión

### ⚠️ Evitar Errores Comunes

❌ **NO procesar la misma factura dos veces**
   - El sistema previene duplicados automáticamente

❌ **NO modificar documentos manualmente después**
   - Los documentos están conciliados entre sí

❌ **NO eliminar notas crédito sin eliminar el comprobante**
   - Mantener la integridad de la conciliación

✅ **SÍ verificar la configuración antes de procesar**
✅ **SÍ descargar el reporte Excel como respaldo**
✅ **SÍ revisar los documentos creados**

---

## 🔍 VERIFICACIÓN RÁPIDA

### Checklist Post-Proceso

Después de procesar, verificar:

- [ ] ✅ Se creó 1 nota crédito por factura
- [ ] ✅ Se creó 1 comprobante de reversión por factura
- [ ] ✅ Notas crédito están en estado "Publicada"
- [ ] ✅ Comprobantes están en estado "Publicada"
- [ ] ✅ Notas crédito están conciliadas
- [ ] ✅ Reporte Excel descargado
- [ ] ✅ Sin errores en columna de estado
- [ ] ✅ Cuenta 530535 con saldo 0

---

## 🆘 AYUDA RÁPIDA

### Problemas Comunes

#### "No se encontraron descuentos condicionados"
**Solución:** Verificar que existan pagos con descuentos en el año seleccionado

#### "Registros Excluidos" alto
**Causa:** Facturas ya procesadas anteriormente
**Acción:** Normal, el sistema previene duplicados

#### Factura con estado "Error"
**Solución:** 
1. Ver mensaje de error en reporte Excel
2. Revisar la factura original
3. Corregir el problema
4. Volver a ejecutar el proceso

---

## 📞 SOPORTE

### Documentación Completa
- `README.md`: Documentación técnica detallada
- `INSTALACION.md`: Guía de instalación y pruebas

### Contacto
- **Website**: https://www.logyca.com
- **Email**: soporte@logyca.com

---

## 🎓 EJEMPLOS PRÁCTICOS

### 📊 Ejemplo 1: Solo generar reporte para revisión

**Situación:**
Quiero revisar todos los descuentos del año 2025 antes de crear notas crédito

**Pasos:**

1. ✅ Abrir módulo
2. ✅ Seleccionar año: 2025
3. ✅ Seleccionar cuenta: 530535
4. ✅ Clic en **"Generar Solo Reporte Excel"**
5. ✅ Descargar Excel
6. ✅ Revisar información en el archivo

**Resultado:**
- Reporte Excel con todas las facturas y descuentos
- NO se crean notas crédito ni comprobantes
- Puedo analizar la información y decidir qué procesar

---

### 🚀 Ejemplo 2: Procesar una sola factura

**Situación:**
Tengo 10 facturas con descuentos, pero solo quiero procesar la factura FV-2025-0123

**Pasos:**

1. ✅ Abrir módulo
2. ✅ Configurar año: 2025
3. ✅ Seleccionar diario y cuenta
4. ✅ Clic en **"Cargar Facturas para Procesar NC"**
5. ✅ Ver las 10 facturas listadas
6. ✅ Clic en **"Deseleccionar Todas"**
7. ✅ Marcar solo la checkbox de FV-2025-0123
8. ✅ Clic en "Procesar Notas Crédito"
9. ✅ Confirmar
10. ✅ Esperar resultado
11. ✅ Descargar reporte Excel
12. ✅ Verificar nota crédito y comprobante creados

**Resultado:**
- 1 nota crédito creada para FV-2025-0123
- 1 comprobante de reversión creado
- Ambos conciliados
- Las otras 9 facturas quedan disponibles para procesar después

---

**¡Listo para usar!** 🎉

Este módulo simplifica completamente el proceso de notas crédito por descuentos condicionados.

**Versión:** 1.0.0
**Fecha:** Diciembre 2024
