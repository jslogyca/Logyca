# Módulo de Solicitud de Cuentas Analíticas

## Descripción

Módulo para Odoo 17 que permite solicitar la creación de cuentas analíticas a través de un formulario web público, con un flujo de aprobación completo y notificaciones por correo electrónico.

## Características

### 1. Formulario Web Público
- **URL de acceso:** `/cuentas_analiticas/formulario`
- **Campos del formulario:**
  - Solicitado Por (res.partner) - Solo muestra partners asociados a empleados (work_contact_id)
  - Compañía (res.company)
  - Línea de Negocio (account.analytic.plan)
  - Nombre de Cuenta Analítica deseada
  - Observaciones (texto libre)
  - Correo electrónico - Se completa automáticamente del empleado (work_email)

### 2. Flujo de Estados
El módulo maneja los siguientes estados:

1. **Borrador (draft):** Estado inicial al crear la solicitud
2. **Solicitado (requested):** La solicitud fue enviada y está pendiente de aprobación
3. **Aprobado (approved):** La solicitud fue aprobada y está lista para crear la cuenta
4. **Terminado (done):** La cuenta analítica fue creada exitosamente
5. **Cancelado (cancelled):** La solicitud fue cancelada con una razón

### 3. Notificaciones por Email

El módulo envía correos automáticos en diferentes momentos:

#### Al Solicitante:
- **Confirmación de recepción:** Cuando la solicitud es enviada (estado: requested)
- **Cuenta creada:** Cuando la cuenta analítica es creada (estado: done)
- **Solicitud cancelada:** Cuando la solicitud es cancelada

#### A los Aprobadores:
- **Nueva solicitud pendiente:** Cuando hay una solicitud en estado "Solicitado"
- Los aprobadores son los usuarios asignados al grupo "Aprobador de Cuentas Analíticas"

### 4. Backend - Gestión de Solicitudes

#### Vistas Disponibles:
- **Tree View:** Lista de todas las solicitudes con colores según estado
- **Form View:** Formulario detallado de cada solicitud
- **Kanban View:** Vista de tarjetas agrupadas por estado
- **Search View:** Búsqueda y filtros avanzados

#### Acciones Disponibles (solo para aprobadores):
- **Aprobar:** Cambia la solicitud a estado "Aprobado"
- **Cancelar:** Abre un wizard para ingresar la razón de cancelación
- **Crear Cuenta Analítica:** Visible solo en estado "Aprobado", crea la cuenta y enlaza el registro

### 5. Creación de Cuenta Analítica

Cuando se aprueba una solicitud y se presiona el botón "Crear Cuenta Analítica":
- Se crea un registro en `account.analytic.account` con:
  - Nombre: El nombre solicitado
  - Plan: El plan analítico seleccionado
  - Compañía: La compañía seleccionada
- Se enlaza la cuenta creada a la solicitud
- Se cambia el estado a "Terminado"
- Se envía notificación al solicitante

## Instalación

1. Copiar el módulo a la carpeta de addons de Odoo
2. Actualizar la lista de aplicaciones
3. Instalar el módulo "Solicitud de Cuentas Analíticas"

## Configuración

### Configurar Aprobadores

1. Ir a: **Configuración > Usuarios y Compañías > Grupos**
2. Buscar el grupo: **Aprobador de Cuentas Analíticas**
3. Agregar los usuarios que deben recibir notificaciones y aprobar solicitudes

### Configurar Secuencia (Opcional)

Por defecto, las solicitudes se numeran con el formato: **SCA-00001**

Para cambiar el formato:
1. Ir a: **Configuración > Técnico > Secuencias**
2. Buscar: "Solicitud de Cuenta Analítica"
3. Modificar el prefijo y formato según necesidades

## Uso

### Para Usuarios (Formulario Web):

1. Acceder a: `https://tu-dominio.com/cuentas_analiticas/formulario`
2. Seleccionar el solicitante (partner asociado a empleado)
3. El email se completará automáticamente
4. Seleccionar compañía y línea de negocio
5. Ingresar el nombre deseado para la cuenta analítica
6. Agregar observaciones (opcional)
7. Enviar la solicitud
8. Recibirás un correo de confirmación con el número de solicitud

### Para Aprobadores:

1. Recibirás un correo cuando haya una nueva solicitud
2. Acceder al backend de Odoo
3. Ir a: **Contabilidad > Solicitudes Cuentas Analíticas > Solicitudes**
4. Abrir la solicitud pendiente
5. Revisar los detalles
6. Aprobar o Cancelar (con razón)
7. Si se aprueba, presionar "Crear Cuenta Analítica"
8. El solicitante recibirá una notificación automática

## Estructura del Módulo

```
analytic_account_request/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── analytic_account_request_controller.py
├── models/
│   ├── __init__.py
│   └── analytic_account_request.py
├── views/
│   ├── analytic_account_request_views.xml
│   └── analytic_account_request_templates.xml
├── data/
│   ├── ir_sequence.xml
│   └── mail_template.xml
├── security/
│   ├── analytic_account_request_security.xml
│   └── ir.model.access.csv
└── README.md
```

## Modelos

### analytic.account.request
Modelo principal que almacena las solicitudes de cuentas analíticas.

**Campos principales:**
- `name`: Número de solicitud (auto-generado)
- `partner_id`: Solicitante (partner asociado a empleado)
- `employee_id`: Empleado (computed)
- `email`: Email del empleado (computed)
- `company_id`: Compañía
- `plan_id`: Plan analítico (Línea de Negocio)
- `analytic_account_name`: Nombre deseado para la cuenta
- `observations`: Observaciones
- `state`: Estado de la solicitud
- `cancel_reason`: Razón de cancelación
- `analytic_account_id`: Enlace a la cuenta creada

### analytic.account.request.cancel.wizard
Wizard transiente para cancelar solicitudes ingresando una razón.

## Permisos

### Grupos de Seguridad:
- **Usuario Base:** Puede ver sus propias solicitudes
- **Aprobador de Cuentas Analíticas:** Puede ver todas las solicitudes, aprobar, cancelar y crear cuentas

## Templates de Email

El módulo incluye 4 templates de email profesionales:
1. `email_template_request_approval`: Notificación a aprobadores
2. `email_template_submission_confirmation`: Confirmación al solicitante
3. `email_template_completion`: Notificación de cuenta creada
4. `email_template_cancellation`: Notificación de cancelación

Todos los templates tienen diseño responsive y profesional con colores distintivos.

## Dependencias

- `base`
- `website`
- `hr`
- `mail`
- `analytic`

## Versión

**1.0.0** - Compatible con Odoo 17.0

## Autor

LOGYCA - https://www.logyca.com

## Licencia

LGPL-3

## Soporte

Para soporte o consultas sobre este módulo, contactar al equipo de desarrollo de LOGYCA.
