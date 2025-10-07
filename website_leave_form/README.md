# Formulario Web de Ausencias para Odoo 17

Módulo que permite crear solicitudes de ausencia a través de un formulario web público y consultar ausencias aprobadas.

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
- Selección de aprobador
- Campo de fecha de solicitud (automático con fecha actual)
- Adjuntos condicionales según tipo de ausencia
- Creación automática de registros hr.leave
- Notificación automática por email al aprobador
- Interfaz responsive con Bootstrap 5
- Registro de auditoría

### Consulta de Ausencias
- Consulta de ausencias aprobadas por número de identificación
- Filtrado por rango de fechas
- Envío automático de resumen por email
- Email con detalle completo de todas las ausencias aprobadas

## Configuración de Tipos de Ausencia

Para configurar tipos de ausencia que requieran adjuntos (como incapacidades):

1. Ve a **Recursos Humanos > Configuración > Tipos de Ausencia**
2. Selecciona o crea un tipo de ausencia
3. Marca la casilla **"Requiere Adjuntos"**
4. Guarda los cambios

Cuando un usuario seleccione este tipo en el formulario web, se mostrará automáticamente el campo para adjuntar documentos.

## Características del Email de Notificación

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

## Autor

Tu Empresa
