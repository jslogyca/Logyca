# CHANGELOG - Módulo Descuentos Comerciales Condicionados

## [1.0.0] - 2024-12-22

### ✨ Nuevas Funcionalidades

#### Creación Automática de Notas Crédito
- Generación automática de notas crédito para descuentos condicionados
- Identificación de facturas elegibles basada en apuntes contables 530535
- Prevención de duplicados mediante campo de marcación
- Selección flexible de facturas a procesar

#### Comprobantes de Reversión Contable
- Creación automática de comprobantes de reversión
- Diario parametrizable para comprobantes
- Débito a cuenta CXC y crédito a cuenta 530535
- Herencia de distribución analítica desde factura original
- Descripción automática con referencia a factura

#### Conciliación Automática
- Conciliación de CXC de nota crédito con CXC de comprobante
- Actualización automática de saldos pendientes
- Trazabilidad completa de movimientos

#### Interfaz de Usuario Mejorada
- Wizard de 3 pasos: Configuración → Selección → Resultado
- Vista de árbol para selección de facturas
- Botones de "Seleccionar Todas" / "Deseleccionar Todas"
- Selección individual por factura
- Mensajes informativos en cada paso
- Indicadores visuales de estado (Procesado/Error/Pendiente)

#### Reporte Excel Ampliado
- Nuevas columnas:
  - Número de Nota Crédito
  - Valor de Nota Crédito
  - Número de Comprobante Reversión
  - Valor de Comprobante Reversión
  - Estado del proceso
  - Mensaje de error (si aplica)
- Formato profesional con colores y bordes
- Ancho de columnas optimizado
- Formatos numéricos y de fecha localizados

#### Manejo Robusto de Errores
- Procesamiento individual por factura
- Registro de errores sin detener el proceso completo
- Mensajes descriptivos de error por factura
- Inclusión de errores en reporte Excel
- Estados diferenciados: Procesado / Error / Pendiente

#### Trazabilidad y Auditoría
- Campo booleano `is_conditional_discount_credit_note` en notas crédito
- Referencias cruzadas entre documentos
- Reporte completo con toda la información del proceso
- Links directos a documentos generados en interfaz

### 🔧 Mejoras Técnicas

#### Modelos de Datos
- Nuevo modelo: `conditional.discount.invoice.line` (transient)
  - Gestión de facturas a procesar
  - Almacenamiento temporal de resultados
  - Referencias a documentos generados
- Herencia de `account.move` con campo de marcación

#### Validaciones y Seguridad
- Validación de configuración antes de procesar
- Verificación de existencia de cuentas requeridas
- Control de permisos por grupos de contabilidad
- Validación de estados de documentos

#### Performance
- Búsqueda optimizada por índices de conciliación
- Prevención de búsquedas duplicadas
- Procesamiento eficiente de múltiples facturas
- Manejo de memoria optimizado para reportes grandes

### 📚 Documentación

#### Archivos de Documentación
- `README.md`: Documentación completa del módulo
  - Descripción detallada de funcionalidades
  - Explicación del proceso contable
  - Estructura de datos
  - Consideraciones técnicas
  
- `INSTALACION.md`: Guía de instalación y pruebas
  - Requisitos previos
  - Pasos de instalación detallados
  - Escenarios de prueba completos
  - Solución de problemas comunes
  - Checklist de instalación

- `CHANGELOG.md`: Historial de cambios (este archivo)

### 🔄 Cambios en Archivos Existentes

#### `__manifest__.py`
- Actualización de descripción
- Adición de nuevas vistas
- Adición de modelos

#### `conditional_discount_report_wizard.py`
- Refactorización completa del wizard
- Nuevos métodos:
  - `action_load_invoices()`: Carga de facturas elegibles
  - `action_select_all()`: Selección masiva
  - `action_unselect_all()`: Deselección masiva
  - `action_process_credit_notes()`: Procesamiento de NC
  - `_create_credit_note()`: Creación de nota crédito
  - `_create_reversal_entry()`: Creación de comprobante
  - `_reconcile_entries()`: Conciliación automática
  - `_prepare_report_data()`: Preparación de datos para Excel
- Actualización de `_generate_excel()` con nuevas columnas
- Estados ampliados: draft → loaded → done

#### `conditional_discount_report_wizard_views.xml`
- Diseño de interfaz de 3 pasos
- Vista de árbol para líneas de facturas
- Nuevos botones de acción
- Mensajes informativos contextuales
- Colores y formato mejorados

#### `security/ir.model.access.csv`
- Permisos para nuevo modelo `conditional.discount.invoice.line`
- Permisos para usuarios y managers de contabilidad

### 🆕 Nuevos Archivos

- `models/__init__.py`: Inicialización de modelos
- `models/account_move.py`: Herencia de account.move
- `views/account_move_views.xml`: Vista del campo de marcación
- `README.md`: Documentación completa
- `INSTALACION.md`: Guía de instalación
- `CHANGELOG.md`: Este archivo

### 🐛 Correcciones

- Mejora en lógica de identificación de facturas relacionadas
- Manejo correcto de casos sin conciliación
- Validación de existencia de líneas CXC
- Control de errores en generación de documentos

### ⚠️ Breaking Changes

- El wizard ahora requiere configuración adicional (diario y cuenta)
- El flujo cambió de 1 paso a 3 pasos
- El método `action_generate_report()` fue reemplazado por `action_load_invoices()`

### 📦 Dependencias

- `account`: ^17.0
- `base`: ^17.0

### 🔐 Seguridad

- Todos los movimientos requieren permisos de contabilidad
- Validación de configuración antes de procesar
- Registro completo de auditoría en logs

### 🎯 Compatibilidad

- Odoo 17.0
- Python 3.10+
- PostgreSQL 12+

---

## Notas de Migración

### Desde versión anterior (reporte simple)

Si ya tenía instalada una versión anterior de este módulo:

1. **Backup de base de datos**: Hacer backup completo antes de actualizar
2. **Actualizar módulo**: Usar el modo de actualización de Odoo
3. **Configurar nuevos campos**: Configurar diario de reversión y cuenta
4. **Verificar permisos**: Asegurar que usuarios tengan permisos adecuados
5. **Probar en ambiente de desarrollo**: Antes de producción

### Datos existentes

- Las notas crédito creadas manualmente NO se verán afectadas
- Solo las creadas por el nuevo sistema tendrán el campo de marcación
- Comprobantes anteriores permanecen intactos

---

## Roadmap Futuro

### Versión 1.1.0 (Planeada)
- [ ] Filtro por compañía (multi-company)
- [ ] Selección de rango de fechas personalizado
- [ ] Exportación a PDF además de Excel
- [ ] Dashboard con estadísticas de descuentos
- [ ] Programación de proceso automático

### Versión 1.2.0 (Planeada)
- [ ] Integración con módulo de aprobaciones
- [ ] Notificaciones por email de documentos creados
- [ ] Historial de procesos ejecutados
- [ ] Comparativa entre periodos

---

## Contribuciones

Este módulo es desarrollado y mantenido por **LOGYCA**.

Para reportar bugs o solicitar features:
- Website: https://www.logyca.com
- Email: soporte@logyca.com

---

**Versión actual:** 1.0.0
**Fecha de release:** Diciembre 22, 2024
**Autor:** LOGYCA
**Licencia:** LGPL-3
