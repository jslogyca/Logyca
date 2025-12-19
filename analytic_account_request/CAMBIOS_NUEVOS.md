# Módulo de Solicitudes - Actualización con Nuevas Funcionalidades

## Cambios Implementados

### 1. Formulario de Tarjeta de Crédito

#### Nuevos Campos:
- **Aprobador (`approver_id`)**: Campo Many2one que permite seleccionar el usuario que aprobará la solicitud. Solo muestra usuarios del grupo "Aprobador de Tarjetas de Crédito".
- **Fecha de Aprobación (`approval_date`)**: Campo Datetime que guarda automáticamente la fecha y hora cuando se aprueba la solicitud.

#### Nuevo Estado:
- **En Trámite (`in_process`)**: Estado intermedio entre "Aprobado" y "Terminado".

#### Flujo de Estados Actualizado:
```
Borrador → Solicitado → Aprobado → En Trámite → Terminado
                              ↓
                         Cancelado
```

#### Nuevos Botones y Funcionalidades:
- **Botón "Pasar a Trámite"**: Visible en estado "Aprobado", cambia el estado a "En Trámite" y envía correo al solicitante.
- **Botón "Marcar como Terminado"**: Ahora solo visible en estado "En Trámite".
- **Validación de Aprobador**: Al aprobar, el sistema verifica que el usuario actual sea el mismo que está configurado en el campo "Aprobador".

#### Nuevo Template de Correo:
- **Notificación "En Trámite"**: Se envía automáticamente al solicitante cuando la solicitud pasa a estado "En Trámite".

---

### 2. Formulario de Producto

#### Nuevos Campos de Aprobación Múltiple:
1. **Autoriza Estructura Financiera (`financial_approver_id`)**: Usuario que aprueba desde el punto de vista financiero.
2. **Autoriza Temas Legales (`legal_approver_id`)**: Usuario que aprueba desde el punto de vista legal.
3. **Autoriza Estructura Contable (`accounting_approver_id`)**: Usuario que aprueba desde el punto de vista contable.

#### Campos de Control de Aprobación:
- `financial_approved`: Boolean que indica si está aprobado financieramente
- `financial_approval_date`: Fecha de aprobación financiera
- `legal_approved`: Boolean que indica si está aprobado legalmente
- `legal_approval_date`: Fecha de aprobación legal
- `accounting_approved`: Boolean que indica si está aprobado contablemente
- `accounting_approval_date`: Fecha de aprobación contable
- `all_approved`: Campo computado que verifica si todas las aprobaciones están completas

#### Nuevos Botones de Aprobación:
- **"Aprobar Financiero"**: Visible en estado "Solicitado" si no está aprobado financieramente
- **"Aprobar Legal"**: Visible en estado "Solicitado" si no está aprobado legalmente
- **"Aprobar Contable"**: Visible en estado "Solicitado" si no está aprobado contablemente

#### Lógica de Aprobación:
- Cada aprobador solo puede aprobar en su área específica
- El sistema verifica que el usuario actual sea el aprobador designado
- Cuando las tres aprobaciones están completas, la solicitud pasa automáticamente a estado "Aprobado"
- Se muestra un indicador visual del estado de cada aprobación

#### Configuración de Aprobadores por Defecto:
Los aprobadores se configuran en **Ajustes → Solicitudes de Cuentas Analíticas**:
- Aprobador Financiero por Defecto
- Aprobador Legal por Defecto
- Aprobador Contable por Defecto

Cuando se crea una nueva solicitud de producto, estos usuarios se asignan automáticamente como aprobadores (pueden modificarse antes de enviar la solicitud).

---

### 3. Formulario de Cuentas Analíticas

#### Mejora en Campo Línea de Negocio:
- **Filtro Dinámico por Compañía**: El campo "Línea de Negocio" (`plan_id`) ahora solo muestra los planes analíticos que tienen cuentas analíticas asociadas a la compañía seleccionada.
- Implementado mediante método computado `_compute_available_plans` que:
  1. Busca todas las cuentas analíticas de la compañía seleccionada
  2. Obtiene los planes analíticos de esas cuentas
  3. Filtra el campo `plan_id` para mostrar solo esos planes
- Dominio aplicado: `[('id', 'in', available_plan_ids)]`

**Nota**: Como el modelo `account.analytic.plan` no tiene campo `company_id`, se implementó una lógica que busca los planes a través de las cuentas analíticas existentes de cada compañía.

---

## Instrucciones de Instalación/Actualización

### 1. Actualizar el Módulo

```bash
# Actualizar el módulo en Odoo
./odoo-bin -u analytic_account_request -d nombre_base_datos
```

### 2. Configurar Aprobadores por Defecto (Solo para Productos)

1. Ir a **Ajustes → Técnico → Parámetros del Sistema** o navegar a **Ajustes** (si se muestra la configuración)
2. Buscar la sección "Solicitudes de Cuentas Analíticas"
3. Configurar los tres aprobadores por defecto:
   - Aprobador Financiero por Defecto
   - Aprobador Legal por Defecto
   - Aprobador Contable por Defecto

**Nota**: Estos usuarios deben existir en el sistema antes de configurarlos.

### 3. Configurar Aprobador para Tarjetas de Crédito

El campo "Aprobador" en las tarjetas de crédito debe configurarse manualmente en cada solicitud. El sistema solo permite seleccionar usuarios que pertenezcan al grupo "Aprobador de Tarjetas de Crédito".

---

## Archivos Modificados

### Modelos:
- `models/credit_card_request.py`: Agregados campos de aprobador, fecha de aprobación, estado "in_process" y métodos de validación
- `models/product_request.py`: Agregados campos de aprobación múltiple, métodos de aprobación individual y lógica de configuración por defecto
- `models/analytic_account_request.py`: Agregado dominio dinámico al campo plan_id
- `models/res_config_settings.py`: **NUEVO** - Modelo para configuración de aprobadores por defecto

### Vistas:
- `views/credit_card_request_views.xml`: Actualizada vista de formulario con nuevos campos y botones
- `views/product_request_views.xml`: Actualizada vista con campos de aprobación y indicadores visuales
- `views/res_config_settings_views.xml`: **NUEVO** - Vista de configuración para aprobadores

### Datos:
- `data/credit_card_mail_template.xml`: Agregado template de correo para estado "En Trámite"

### Otros:
- `__manifest__.py`: Agregado archivo de vista de configuración
- `models/__init__.py`: Importado nuevo modelo res_config_settings

---

## Uso del Sistema

### Para Tarjetas de Crédito:

1. **Crear Solicitud**: El solicitante crea una solicitud desde el formulario web
2. **Asignar Aprobador**: Seleccionar el usuario que aprobará (del grupo de aprobadores)
3. **Solicitar**: Cambiar estado a "Solicitado"
4. **Aprobar**: El aprobador designado aprueba la solicitud
5. **Pasar a Trámite**: Usar el botón "Pasar a Trámite" (envía correo al solicitante)
6. **Terminar**: Cuando esté lista, marcar como "Terminado"

### Para Productos:

1. **Crear Solicitud**: Los aprobadores por defecto se asignan automáticamente
2. **Solicitar**: Cambiar estado a "Solicitado"
3. **Aprobaciones Individuales**: 
   - Cada aprobador debe dar su aprobación usando su botón específico
   - Los botones solo son visibles para el aprobador designado
4. **Aprobación Automática**: Cuando las 3 aprobaciones están completas, pasa automáticamente a "Aprobado"
5. **Terminar**: Crear el producto y marcar como terminado

---

## Validaciones Implementadas

### Tarjetas de Crédito:
- Solo el aprobador designado puede aprobar la solicitud
- Solo se puede pasar a "En Trámite" desde estado "Aprobado"
- Solo se puede "Terminar" desde estado "En Trámite"

### Productos:
- Cada aprobador solo puede aprobar en su área específica
- No se puede aprobar la solicitud completa sin las 3 aprobaciones
- El sistema muestra mensajes claros indicando qué aprobaciones faltan

### Cuentas Analíticas:
- Solo se muestran planes analíticos de la compañía seleccionada

---

## Notas Técnicas

- Los parámetros de configuración se almacenan en `ir.config_parameter`
- Las fechas de aprobación se guardan automáticamente con `fields.Datetime.now()`
- Los dominios dinámicos permiten filtrado en tiempo real
- Los campos computados (`all_approved`) se actualizan automáticamente
- Se mantiene la compatibilidad con versión Odoo 17

---

## Soporte

Para cualquier problema o pregunta sobre estas funcionalidades, contactar al equipo de desarrollo de LOGYCA.
