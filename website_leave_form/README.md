# Formulario Web de Ausencias para Odoo 17

Módulo que permite crear solicitudes de ausencia a través de un formulario web público, consultar ausencias aprobadas y enviar recordatorios automáticos.

## Instalación

1. Copia la carpeta `website_leave_form` en tu directorio de addons de Odoo
2. Actualiza la lista de aplicaciones
3. Instala el módulo "Formulario Web de Ausencias"

## Uso

### Solicitar Ausencias
Accede al formulario en: `https://tu-dominio.com/ausencias/formulario`

### Consultar Ausencias Aprobadas
Accede al formulario en: `https://tu-dominio.com/ausencias/consultar`

## Características

### Solicitud de Ausencias
- Formulario web público (sin login)
- Validación de empleado por email corporativo
- Selección de aprobador (usuarios internos)
- Campo de fecha de solicitud (automático con fecha actual)
- Adjuntos condicionales según tipo de ausencia
- Creación automática de registros hr.leave
- Notificación automática por email al aprobador
- Creación de actividad para el aprobador en Odoo
- Interfaz responsive con Bootstrap 5
- Registro de auditoría

### Consulta de Ausencias
- Consulta de ausencias aprobadas por número de identificación
- Filtrado por rango de fechas
- Envío automático de resumen por email
- Email con detalle completo de todas las ausencias aprobadas

### Recordatorios Automáticos ⏰ NUEVO
- **Cron automático** que se ejecuta diariamente a las 8:00 AM
- Envía recordatorios **8 días antes** del inicio de cada ausencia aprobada
- Email personalizado al empleado con:
  - Detalles de la ausencia (fechas, duración, tipo)
  - Contador de días restantes
  - Instrucciones para modificar fechas
  - Información de contacto de Nómina
- Marca automáticamente las ausencias con recordatorio enviado
- Manejo de errores robusto

## Configuración

### Tipos de Ausencia con Adjuntos Obligatorios

Para configurar tipos de ausencia que requieran adjuntos (como incapacidades):

1. Ve a **Recursos Humanos > Configuración > Tipos de Ausencia**
2. Selecciona o crea un tipo de ausencia
3. Marca la casilla **"Requiere Adjuntos"**
4. Guarda los cambios

Cuando un usuario seleccione este tipo en el formulario web, se mostrará automáticamente el campo para adjuntar documentos.

### Configuración del Recordatorio Automático

El cron job está configurado para ejecutarse diariamente. Puedes modificar la configuración:

1. Ve a **Configuración > Técnico > Automatización > Acciones Planificadas**
2. Busca "Enviar Recordatorios de Ausencias (8 días antes)"
3. Puedes modificar:
   - **Frecuencia**: Actualmente cada 1 día
   - **Hora de ejecución**: Por defecto 8:00 AM
   - **Activo**: Activar/desactivar el recordatorio
4. Para cambiar los días de anticipación, edita el código en `models/hr_leave.py` línea:
   ```python
   reminder_date = today + timedelta(days=8)  # Cambiar 8 por los días deseados
   ```

### Personalizar Email de Recordatorio

Para personalizar el contenido del email de recordatorio:

1. Ve a **Configuración > Técnico > Emails > Templates**
2. Busca "Recordatorio de Inicio de Ausencia"
3. Modifica el contenido según tus necesidades
4. Puedes cambiar:
   - Información de contacto de Nómina
   - Diseño y colores
   - Mensajes y textos

## Características del Email de Notificación (Aprobador)

- Email enviado automáticamente al aprobador cuando se crea una solicitud
- Incluye todos los detalles de la ausencia
- Botón directo para ver y aprobar en Odoo
- Diseño responsive y profesional

## Características del Email de Resumen

- Información completa del empleado
- Lista detallada de todas las ausencias aprobadas
- Contador total de ausencias
- Fecha, duración y motivo de cada ausencia
- Diseño profesional y fácil de leer

## Estructura del Módulo

```
website_leave_form/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── website_leave_form.py
│   ├── hr_leave_type.py
│   └── hr_leave.py (recordatorios)
├── controllers/
│   ├── __init__.py
│   └── website_leave_controller.py
├── views/
│   ├── website_leave_form_templates.xml
│   └── hr_leave_type_views.xml
├── data/
│   ├── mail_template.xml (notificación aprobador)
│   ├── leave_summary_mail_template.xml (resumen empleado)
│   ├── leave_reminder_mail_template.xml (recordatorio)
│   └── ir_cron.xml (tarea programada)
└── security/
    └── ir.model.access.csv
```

## Notas Técnicas

- Los adjuntos se vinculan directamente al registro `hr.leave`
- Se crean copias de los adjuntos en `website.leave.form` para auditoría
- El campo `reminder_sent` previene envíos duplicados de recordatorios
- El cron maneja errores sin detener el proceso para otros empleados
- Los logs de errores se registran en `ir.logging` para debugging

## Soporte

Para soporte técnico o consultas, contacta al departamento de IT.

## Autor

Tu Empresa
