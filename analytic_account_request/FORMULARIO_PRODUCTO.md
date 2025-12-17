# Formulario de Solicitud de Creación de Producto

## Descripción General

El formulario de solicitud de creación de producto es un formulario web público que permite a los colaboradores de LOGYCA solicitar la creación de nuevos productos en el sistema Odoo, incluyendo toda la información necesaria y los aspectos legales requeridos.

## URL de Acceso

```
https://tu-dominio.com/producto/formulario
```

## Campos del Formulario

### 1. Información del Solicitante

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| Nombre del Colaborador | Selection | Sí | Seleccionar de lista de empleados activos |
| Organización | Selection | Sí | Organización para la cual se va crear el producto |

### 2. Información del Producto

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| Producto en Odoo | Selection | Sí | Opciones: Existente, Nuevo, Variantes |
| Nombre del Producto | Char | Sí | Nombre descriptivo del producto |
| Justificación del Producto | Text | Sí | Razón para la creación del producto |
| Medio de Divulgación | Selection | Sí | Tienda Virtual o Negociación Directa |
| Variantes | Selection | Sí | Sí o No |
| Archivo de Variantes | Binary | No | Se habilita si "Variantes" = Sí |
| Cuenta Analítica | Many2one | Sí | Se filtra por la organización seleccionada |
| Producto es Diferido | Boolean | No | Checkbox |
| Tiempo de Diferimiento | Integer | Condicional | Solo si "Producto es Diferido" = True |
| Forma de Pago | Selection | Sí | Anticipado o A crédito |
| Responsable de Políticas | Char | Sí | Nombre del responsable |

### 3. Aspectos Legales

Todos los campos de aspectos legales son tipo Text y opcionales:

| Campo | Descripción |
|-------|-------------|
| Objeto | El propósito del contrato descrito de forma precisa |
| Objetivos Específicos | Relación detallada de los diversos propósitos |
| Alcance | Descripción del alcance del contrato |
| Duración | Tiempo de ejecución e indicación de prórroga |
| Lugar | Lugar(es) donde se ejecutará el contrato |
| Precio | Determinación del monto del contrato |
| Obligaciones LOGYCA | Obligaciones de LOGYCA (dar, hacer o no hacer) |
| Obligaciones del Aceptante | Compromisos del aceptante |
| Causales Especiales de Terminación | Condiciones para terminación anticipada |
| Forma de Liquidación | Proceso en caso de terminación anticipada |
| Cesión del Contrato | Posibilidad de cesión y autorización |
| Cláusula Penal | Condiciones si se requiere cláusula penal |
| Observaciones | Observaciones adicionales |

## Flujo de Estados

```
Borrador (draft)
    ↓
Solicitado (requested) ← Estado inicial al enviar el formulario
    ↓
Aprobado (approved)
    ↓
Terminado (done)

Cancelado (cancelled) ← Puede ocurrir desde "Solicitado" o "Aprobado"
```

## Funcionalidades Especiales

### 1. Carga Dinámica de Cuentas Analíticas

Cuando el usuario selecciona una organización, el sistema automáticamente carga las cuentas analíticas correspondientes a esa compañía mediante una llamada AJAX al endpoint `/producto/get_analytic_accounts`.

### 2. Campos Condicionales

- **Archivo de Variantes**: Solo se muestra si el campo "Variantes" = "Sí"
- **Tiempo de Diferimiento**: Solo se muestra si "Producto es Diferido" está marcado

### 3. Validaciones

El formulario valida que todos los campos requeridos estén completos antes de permitir el envío.

## Notificaciones por Email

### 1. Confirmación al Solicitante

Se envía inmediatamente después de enviar el formulario:
- **Asunto**: "Solicitud de Producto Recibida: SCP-XXXXX"
- **Contenido**: 
  - Confirmación de recepción
  - Número de solicitud
  - Resumen de la solicitud
  - Estado actual

### 2. Notificación a Aprobadores

Se envía a todos los usuarios del grupo "Aprobador de Productos":
- **Asunto**: "Nueva Solicitud de Creación de Producto: SCP-XXXXX"
- **Contenido**:
  - Detalles de la solicitud
  - Información del producto
  - Link directo a la solicitud en Odoo

### 3. Notificación de Completación

Se envía al solicitante cuando la solicitud es marcada como "Terminado":
- **Asunto**: "Solicitud de Producto Procesada: SCP-XXXXX"
- **Contenido**:
  - Confirmación de procesamiento
  - Detalles del producto creado

### 4. Notificación de Cancelación

Se envía al solicitante si la solicitud es cancelada:
- **Asunto**: "Solicitud de Producto Cancelada: SCP-XXXXX"
- **Contenido**:
  - Información de cancelación
  - Razón de la cancelación

## Backend - Gestión de Solicitudes

### Menú de Acceso

```
Solicitudes > Solicitudes de Producto > Solicitudes
```

### Vista Tree

Muestra todas las solicitudes con:
- Número de solicitud
- Fecha
- Solicitante
- Nombre del producto
- Tipo de producto
- Organización
- Estado (con colores)

### Vista Form

Organizada en dos pestañas:

**1. Información del Producto**
- Datos del solicitante
- Datos generales del producto
- Configuración financiera
- Justificación
- Archivo de variantes (si aplica)

**2. Aspectos Legales**
- Todos los campos legales organizados por secciones

### Botones de Acción

Según el estado actual:
- **En "Solicitado"**: Aprobar, Cancelar
- **En "Aprobado"**: Marcar como Terminado, Cancelar
- **En "Cancelado"**: Solo visualización

### Filtros y Búsquedas

- Por estado
- Por solicitante
- Por nombre de producto
- Por tipo de producto
- Por compañía
- Por cuenta analítica
- Filtro especial "Mis Solicitudes"

## Configuración de Aprobadores

Para agregar usuarios como aprobadores:

1. Ir a **Configuración > Usuarios y Compañías > Grupos**
2. Buscar el grupo "Aprobador de Productos"
3. En la pestaña "Usuarios", agregar los usuarios que deben recibir notificaciones y poder aprobar solicitudes

## Código del Modelo

**Modelo**: `product.request`  
**Archivo**: `models/product_request.py`

**Wizard de Cancelación**: `product.request.cancel.wizard`

## API Endpoints

### GET - Mostrar Formulario
```
/producto/formulario
```

### POST - Enviar Solicitud
```
/producto/submit
```
**Método**: POST  
**Content-Type**: multipart/form-data (para soporte de archivos)

### JSON-RPC - Obtener Cuentas Analíticas
```
/producto/get_analytic_accounts
```
**Método**: POST  
**Tipo**: JSON-RPC  
**Parámetros**: `company_id`

## Secuencia

- **Prefijo**: SCP-
- **Formato**: SCP-XXXXX (5 dígitos)
- **Código**: product.request

## Consideraciones de Implementación

1. **Archivos**: El formulario acepta archivos para el campo de variantes. Los archivos se almacenan como campos Binary en Odoo.

2. **Permisos**: Los usuarios regulares pueden ver sus propias solicitudes. Solo los aprobadores pueden modificar los estados.

3. **Logs**: El sistema registra logs detallados de todas las operaciones para facilitar el debugging.

4. **Emails**: Los templates de email están diseñados con HTML responsive para una buena visualización en todos los dispositivos.

## Personalización

Para personalizar el formulario:

1. **Campos**: Editar `models/product_request.py`
2. **Vista Web**: Editar `views/product_request_templates.xml`
3. **Vista Backend**: Editar `views/product_request_views.xml`
4. **Emails**: Editar `data/product_mail_template.xml`

## Troubleshooting

### El formulario no carga las cuentas analíticas

Verificar:
1. Que la compañía seleccionada tenga cuentas analíticas asociadas
2. Que el endpoint `/producto/get_analytic_accounts` esté respondiendo
3. Revisar los logs del navegador (Console)

### Los emails no se envían

Verificar:
1. Configuración del servidor de correo en Odoo
2. Que los usuarios estén en el grupo "Aprobador de Productos"
3. Que los usuarios tengan email configurado
4. Revisar los logs de Odoo

### El archivo de variantes no se sube

Verificar:
1. Que el formulario tenga `enctype="multipart/form-data"`
2. Límite de tamaño de archivo en el servidor web
3. Permisos de escritura en el sistema de archivos

## Soporte

Para soporte o consultas, contactar al equipo de desarrollo de LOGYCA.
