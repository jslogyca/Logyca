# Changelog v1.4.0

## Nuevas Funcionalidades

### 1. Notificación a Talento y Cultura para Incapacidades y Licencias

**Descripción:**
Se agregó la posibilidad de enviar notificaciones de ausencias directamente al departamento de Talento y Cultura en lugar del líder directo, útil para tipos de ausencias especiales como incapacidades y licencias.

**Cambios técnicos:**
- Nuevo campo `notify_talent_culture` (Boolean) en modelo `hr.leave.type`
- Modificación del método `send_approval_notification()` en `website.leave.form`
- Actualización de la vista de formulario de `hr.leave.type`

**Cómo usar:**
1. Ir a **Ausencias > Configuración > Tipos de Ausencia**
2. Abrir el tipo de ausencia deseado (ej: "Incapacidad", "Licencia de Maternidad")
3. En la sección "Configuración Web", marcar el checkbox **"Notificar a Talento y Cultura"**
4. Guardar los cambios

Una vez configurado, todas las solicitudes de ese tipo de ausencia enviarán la notificación a todos los usuarios del grupo "HR Manager" (Talento y Cultura) en lugar del aprobador seleccionado.

**Nota importante:**
- El sistema busca usuarios con el rol "HR Manager" (`hr.group_hr_manager`)
- Asegúrate de que los usuarios de Talento y Cultura tengan este rol asignado
- Si no se encuentra el grupo o no hay usuarios con email, se registrará un warning en el log

---

### 2. Aprobación Automática de Ausencias Pendientes con Fecha de Corte

**Descripción:**
Se implementó un sistema de aprobación automática para ausencias que permanecen en estado "pendiente" por mucho tiempo, con fecha de corte configurable.

**Cambios técnicos:**
- Nuevo método `auto_approve_pending_leaves(cutoff_date=None)` en `website.leave.form`
- Nuevo cron job "Aprobación Automática de Ausencias Pendientes"
- Sistema de logging completo para auditoría

**Cómo usar:**

#### Opción A: Activar Cron Automático (Mensual)
1. Ir a **Ajustes > Técnico > Automatización > Acciones Planificadas**
2. Buscar "Aprobación Automática de Ausencias Pendientes"
3. Marcar como **Activo**
4. El cron se ejecutará el primer día de cada mes a la 1:00 AM

#### Opción B: Ejecución Manual desde Python/Shell
```python
# Aprobar todas las ausencias pendientes hasta hoy
self.env['website.leave.form'].auto_approve_pending_leaves()

# Aprobar ausencias hasta una fecha específica
from datetime import date
cutoff = date(2025, 11, 30)
self.env['website.leave.form'].auto_approve_pending_leaves(cutoff_date=cutoff)
```

#### Opción C: Ejecución Manual desde la UI
1. Ir a **Ausencias > Formularios Web > Formularios Web de Ausencias**
2. Activar modo desarrollador
3. Seleccionar los registros en estado "Enviado"
4. Ir a Acción > Ejecutar Código Python
5. Ingresar: `records.auto_approve_pending_leaves()`

**Retorno del método:**
```python
{
    'total_pending': 10,      # Total de ausencias encontradas
    'approved': 9,            # Ausencias aprobadas exitosamente
    'errors': 1,              # Ausencias con errores
    'error_messages': [...],  # Lista de errores
    'cutoff_date': date(...)  # Fecha de corte utilizada
}
```

**Características:**
- ✅ Aprueba automáticamente ausencias en estado "submitted"
- ✅ Solo procesa ausencias hasta la fecha de corte especificada
- ✅ Envía emails de confirmación a empleados y aprobadores
- ✅ Logging completo de cada operación (éxitos y errores)
- ✅ Retorna estadísticas del proceso
- ✅ Manejo robusto de errores (si una falla, continúa con las demás)

**Recomendaciones:**
- Mantener el cron **desactivado** por defecto y activarlo según necesidad
- Revisar los logs periódicamente en **Ajustes > Técnico > Logging**
- Configurar la frecuencia del cron según las políticas de la empresa
- Realizar pruebas iniciales en ambiente de desarrollo

---

## Archivos Modificados

```
website_leave_form/
├── models/
│   ├── hr_leave_type.py              # Nuevo campo notify_talent_culture
│   └── website_leave_form.py         # Métodos modificados y nuevo método
├── views/
│   └── hr_leave_type_views.xml       # Campo agregado en formulario
└── data/
    └── ir_cron.xml                    # Nuevo cron agregado
```

## Instalación/Actualización

1. Copiar el módulo actualizado al directorio de addons
2. Reiniciar el servicio de Odoo
3. Ir a **Apps** y hacer clic en "Actualizar Lista de Aplicaciones"
4. Buscar el módulo "website_leave_form"
5. Hacer clic en "Actualizar"

## Testing Recomendado

### Para Notificación a Talento y Cultura:
1. Marcar un tipo de ausencia con "Notificar a Talento y Cultura"
2. Crear una solicitud de ese tipo
3. Verificar que el email llegue a los usuarios del grupo HR Manager
4. Revisar logs en caso de errores

### Para Aprobación Automática:
1. Crear solicitudes de prueba en estado "Enviado"
2. Ejecutar el método manualmente con fecha de corte
3. Verificar que las ausencias cambien a estado "Aprobado"
4. Verificar que lleguen emails de confirmación
5. Revisar logs de ejecución

## Soporte

Para reportar issues o solicitar mejoras, contactar al equipo de desarrollo.

---

**Versión:** 1.4.0  
**Fecha:** Noviembre 2025  
**Compatibilidad:** Odoo 17/18
