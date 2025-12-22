# Módulo de Descuentos Comerciales Condicionados - Notas Crédito Automáticas

## Descripción General

Este módulo para Odoo 17 ofrece **dos modos de operación** para gestionar descuentos comerciales condicionados registrados en la cuenta 530535:

### Modo 1: Reporte Simple
Genera un reporte detallado en Excel de todos los descuentos condicionados **sin crear documentos**. Ideal para:
- Análisis y revisión previa
- Reportes gerenciales
- Auditoría de descuentos
- Planificación contable

### Modo 2: Proceso Automático Completo
Automatiza la creación de notas crédito y comprobantes contables:
- Identifica facturas elegibles
- Genera notas crédito automáticamente
- Crea comprobantes de reversión
- Concilia documentos
- Genera reporte Excel completo

## Funcionalidades Principales

### Modo 1: Reporte Simple (Sin Creación de Documentos)

#### 1. Identificación de Descuentos
El módulo busca automáticamente:
- Apuntes contables en la cuenta 530535 (Descuentos Comerciales Condicionados)
- Registrados en diarios de tipo "banco"
- Con movimientos al débito
- Conciliados con facturas de venta

#### 2. Reporte Excel Informativo
Genera un reporte detallado con:
- Información completa de facturas
- Datos del cliente
- Valores de descuentos
- Comprobantes de pago relacionados
- Información para análisis y toma de decisiones

**Ventajas:**
- ⏱️ Rápido: Solo 1-2 minutos
- 📊 Análisis previo antes de crear documentos
- 🔍 Auditoría y revisión
- 📈 Reportes gerenciales

---

### Modo 2: Proceso Automático Completo (Con Creación de Documentos)

#### 1. Identificación Automática de Facturas

El módulo busca automáticamente:
- Apuntes contables en la cuenta 530535 (Descuentos Comerciales Condicionados)
- Registrados en diarios de tipo "banco"
- Con movimientos al débito
- Conciliados con facturas de venta
- Que no tengan notas crédito previamente generadas por el sistema

### 2. Selección Flexible de Facturas

- Carga todas las facturas elegibles en una interfaz intuitiva
- Permite deseleccionar todas las facturas con un botón
- Permite seleccionar/deseleccionar facturas individuales
- Opción de procesar solo las facturas seleccionadas

### 3. Creación Automática de Notas Crédito

Por cada factura seleccionada, el sistema crea automáticamente:

**Nota Crédito (account.move - out_refund):**
- Tipo: Nota crédito de cliente
- Cliente: Mismo de la factura original
- Monto: Valor del descuento condicionado
- Referencia: Número de la factura original
- Cuenta de ingresos: Misma de la factura original
- Distribución analítica: Heredada de la factura original
- Campo especial: `is_conditional_discount_credit_note = True`

### 4. Creación de Comprobantes de Reversión

Por cada nota crédito generada, se crea un comprobante contable:

**Comprobante de Reversión (account.move - entry):**
- Diario: Parametrizable por el usuario
- Referencia: Número de la factura original

**Líneas del comprobante:**
1. **Débito:**
   - Cuenta: CXC de la factura (cuenta del cliente)
   - Monto: Valor del descuento condicionado
   - Descripción: "Reversion Descuento Condicionado - [Número Factura]"
   - Distribución analítica: Heredada de la factura

2. **Crédito:**
   - Cuenta: 530535 - Descuentos Comerciales Condicionados
   - Monto: Valor del descuento condicionado
   - Descripción: "Reversion Descuento Condicionado - [Número Factura]"
   - Distribución analítica: Heredada de la factura

### 5. Conciliación Automática

El sistema concilia automáticamente:
- La línea CXC de la nota crédito
- Con la línea CXC del comprobante de reversión

Esto garantiza que ambos movimientos queden vinculados y conciliados en el sistema.

### 6. Marcación de Notas Crédito

Todas las notas crédito generadas por este proceso se marcan con el campo booleano:
- `is_conditional_discount_credit_note = True`

Esto permite:
- Identificar fácilmente estas notas crédito en el sistema
- Filtrar y buscar notas crédito generadas automáticamente
- Evitar duplicados en futuras ejecuciones

### 7. Reporte Excel Detallado

El sistema genera un reporte en Excel con la siguiente información:

**Columnas del reporte:**
1. Factura de Venta
2. Fecha Factura
3. Cliente
4. NIT Cliente
5. Moneda Factura
6. Subtotal Factura
7. Total Factura
8. Total Factura (Moneda Cía)
9. Comprobante Pago
10. Fecha Pago
11. Valor Descuento
12. **Nota Crédito** (número generado)
13. **Valor NC**
14. **Comprobante Reversión** (número generado)
15. **Valor Reversión**
16. **Estado** (Procesado/Error/Pendiente)
17. **Error** (mensaje de error si aplica)

## Configuración Inicial

### Parámetros Requeridos

Antes de ejecutar el proceso, debe configurar:

1. **Diario para Comprobantes de Reversión:**
   - Debe ser un diario de tipo "General" (Miscellaneous)
   - Se recomienda crear un diario específico para este proceso

2. **Cuenta de Descuentos (530535):**
   - El sistema busca automáticamente la cuenta con código 530535
   - Debe existir en el plan de cuentas

## Proceso de Uso

El módulo ofrece dos formas de trabajar según sus necesidades:

---

### 📊 Opción A: Solo Generar Reporte Excel

**Cuándo usar:**
- Necesita revisar descuentos antes de procesarlos
- Requiere un reporte para análisis o gerencia
- Quiere auditar descuentos sin crear documentos
- Planificación de cierre contable

**Pasos:**

#### Paso 1: Acceso al Módulo
1. Ir a: **Contabilidad → Informes → Reportes → Descuentos Condicionados para NC**

#### Paso 2: Configuración Simple
1. Seleccionar el **Año** a procesar
2. Seleccionar la **Cuenta de Descuentos (530535)**
3. Hacer clic en **"Generar Solo Reporte Excel"**

#### Paso 3: Descarga
1. El sistema genera el reporte inmediatamente
2. Hacer clic en **"Descargar Excel"**

**⏱️ Tiempo total:** 1-2 minutos

---

### 🚀 Opción B: Proceso Completo con NC y Comprobantes

**Cuándo usar:**
- Necesita crear notas crédito automáticamente
- Requiere comprobantes de reversión
- Quiere conciliación automática
- Proceso de cierre mensual

**Pasos:**

### Paso 1: Acceso al Módulo

1. Ir a: **Contabilidad → Informes → Reportes → Descuentos Condicionados para NC**
2. El wizard se abrirá en estado "Borrador"

### Paso 2: Configuración

1. Seleccionar el **Año** a procesar (por defecto: año actual)
2. Seleccionar el **Diario para Comprobantes de Reversión**
3. Seleccionar la **Cuenta de Descuentos (530535)**
4. Hacer clic en **"Cargar Facturas"**

### Paso 3: Revisión y Selección

El sistema mostrará:
- Total de facturas encontradas
- Total de facturas excluidas (ya procesadas o sin conciliación)
- Lista detallada de facturas con:
  - Checkbox de selección (todas vienen seleccionadas por defecto)
  - Número de factura
  - Fecha
  - Cliente
  - Valor del descuento

**Opciones disponibles:**
- **Deseleccionar Todas:** Quita la selección de todas las facturas
- **Seleccionar Todas:** Selecciona todas las facturas nuevamente
- Selección/deselección individual por factura
- **Volver:** Regresa al paso de configuración

### Paso 4: Procesamiento

1. Verificar que las facturas correctas estén seleccionadas
2. Hacer clic en **"Procesar Notas Crédito"**
3. Confirmar la acción en el diálogo de confirmación
4. El sistema procesará cada factura seleccionada y:
   - Creará la nota crédito
   - Creará el comprobante de reversión
   - Conciliará ambos movimientos
   - Actualizará el estado de cada línea

### Paso 5: Descarga del Reporte

1. Una vez completado el proceso, se mostrará un resumen
2. Hacer clic en **"Descargar Excel"** para obtener el reporte completo
3. El archivo incluirá:
   - Todas las facturas procesadas
   - Números de notas crédito y comprobantes generados
   - Estado de cada proceso (Procesado/Error)
   - Mensajes de error para casos fallidos

## Manejo de Errores

### Errores Durante el Procesamiento

Si alguna factura falla durante el procesamiento:
- El estado de esa línea se marca como "Error"
- Se registra el mensaje de error específico
- El proceso continúa con las demás facturas
- El reporte Excel incluirá la información del error

### Errores Comunes

1. **"No se encontró línea de CXC en la factura"**
   - La factura no tiene línea de cuenta por cobrar
   - Verificar la configuración de la factura

2. **"No se encontró cuenta de ingresos en la factura"**
   - La factura no tiene líneas de ingreso válidas
   - Verificar las líneas de la factura

3. **Error de conciliación**
   - Problemas al conciliar las cuentas
   - Verificar que las cuentas sean conciliables

## Validaciones del Sistema

### Prevención de Duplicados

El sistema verifica antes de procesar:
- Que la factura no tenga una nota crédito generada previamente por este proceso
- Solo se incluyen facturas que cumplan con todos los criterios

### Validaciones de Configuración

- Diario de reversión debe ser de tipo "General"
- Cuenta 530535 debe existir y estar activa
- Las facturas deben estar en estado "Publicado"
- Las facturas deben tener conciliación válida

## Estructura de Datos

### Modelo: account.move (Heredado)

```python
is_conditional_discount_credit_note = fields.Boolean(
    string='NC por Descuento Condicionado',
    default=False,
    copy=False,
    readonly=True
)
```

### Modelo: conditional.discount.invoice.line (Transient)

Almacena temporalmente la información de cada factura a procesar:
- Referencia a la factura original
- Valor del descuento
- Comprobante de pago relacionado
- Línea de descuento 530535
- Estado del procesamiento
- Referencias a documentos generados

### Modelo: conditional.discount.report.wizard (Transient)

Wizard principal que gestiona todo el proceso:
- Parámetros de búsqueda
- Configuración de cuentas y diarios
- Líneas de facturas a procesar
- Generación de documentos
- Generación de reporte

## Consideraciones Técnicas

### Herencia de Información Contable

El sistema hereda automáticamente de la factura original:
- Distribución analítica
- Cuenta de CXC (clientes)
- Cuenta de ingresos
- Información del cliente

### Conciliación Automática

- Utiliza el método estándar de Odoo `reconcile()`
- Concilia líneas con la misma cuenta y montos opuestos
- Actualiza automáticamente los saldos pendientes

### Generación de Excel

- Utiliza la librería `xlsxwriter`
- Formato profesional con:
  - Encabezados con formato
  - Columnas con ancho ajustado
  - Formatos numéricos para montos
  - Formatos de fecha localizados

## Notas de Implementación

### Base de Datos

El módulo no crea tablas permanentes adicionales, solo usa:
- Herencia de `account.move` (campo adicional)
- Modelos transient para el wizard

### Performance

- Optimizado para procesar múltiples facturas
- Búsqueda eficiente por índices de conciliación
- Procesamiento secuencial con manejo de errores

### Seguridad

- Permisos basados en grupos de contabilidad
- Solo usuarios con permisos de contabilidad pueden ejecutar el proceso
- Todos los movimientos quedan registrados en el log de Odoo

## Soporte y Mantenimiento

### Logs

Todos los errores se registran en:
- Campo `error_message` de cada línea procesada
- Logs del servidor Odoo
- Reporte Excel

### Auditoría

Es posible auditar el proceso mediante:
- Campo `is_conditional_discount_credit_note` en notas crédito
- Referencias cruzadas en comprobantes
- Reporte Excel con información completa

## Autor

**LOGYCA**
- Website: https://www.logyca.com
- Versión: 17.0.1.0.0
- Licencia: LGPL-3

## Dependencias

- `account`: Módulo de contabilidad de Odoo
- `base`: Módulo base de Odoo

## Versión de Odoo

Este módulo está diseñado y probado para **Odoo 17**.
