# Solicitudes de Cuentas Analíticas, Tarjetas de Crédito y Productos

Módulo de Odoo 17 que permite a los usuarios realizar solicitudes a través de formularios web públicos para:
1. Creación de cuentas analíticas
2. Tarjetas de crédito corporativas
3. Creación de productos

## Características

### Formulario de Solicitud de Cuentas Analíticas
- Formulario web público accesible sin autenticación
- Campos:
  - Solicitante (res.partner asociado a empleados)
  - Compañía
  - Plan analítico
  - Nombre de la cuenta analítica
- Flujo de aprobación con estados (Borrador, Solicitado, Aprobado, Terminado, Cancelado)
- Creación automática de cuenta analítica al aprobar
- Notificaciones por email en cada etapa

### Formulario de Solicitud de Tarjeta de Crédito
- Formulario web público accesible sin autenticación
- Campos principales:
  - Solicitante (res.partner asociado a empleados)
  - Tarjetahabiente (res.partner asociado a empleados)
  - Número de cédula
  - Organización
  - Equipo/Departamento
  - Cargo (se completa automáticamente)
- Estados: Borrador, Solicitado, Aprobado, Terminado, Cancelado
- Notificaciones automáticas por email

### Formulario de Solicitud de Creación de Producto (NUEVO)
- Formulario web público accesible sin autenticación
- **Información del Producto:**
  - Solicitante (colaborador)
  - Organización
  - Tipo de producto (Existente, Nuevo, Variantes)
  - Nombre del producto
  - Justificación
  - Medio de divulgación (Tienda Virtual, Negociación Directa)
  - Variantes (Sí/No) con opción de adjuntar archivo
  - Cuenta analítica del producto
  - Producto diferido (con tiempo en meses)
  - Forma de pago (Anticipado, A crédito)
  - Responsable de políticas

- **Aspectos Legales:**
  - Objeto del contrato
  - Objetivos específicos
  - Alcance
  - Duración
  - Lugar
  - Precio
  - Obligaciones LOGYCA
  - Obligaciones del aceptante
  - Causales especiales de terminación
  - Forma de liquidación
  - Cesión del contrato
  - Cláusula penal
  - Observaciones

- Estados: Borrador, Solicitado, Aprobado, Terminado, Cancelado
- Notificaciones automáticas por email en cada etapa

## Instalación

1. Copiar el módulo en la carpeta de addons de Odoo
2. Actualizar lista de aplicaciones
3. Instalar el módulo "Solicitud de Cuentas Analíticas, Tarjetas de Crédito y Productos"

## Configuración

### Grupos de Permisos

El módulo crea tres grupos de permisos:

1. **Aprobador de Cuentas Analíticas**: 
   - Usuarios que recibirán notificaciones de nuevas solicitudes de cuentas analíticas
   - Pueden aprobar, cancelar y gestionar solicitudes

2. **Aprobador de Tarjetas de Crédito**:
   - Usuarios que recibirán notificaciones de nuevas solicitudes de tarjetas de crédito
   - Pueden aprobar, cancelar y gestionar solicitudes

3. **Aprobador de Productos** (NUEVO):
   - Usuarios que recibirán notificaciones de nuevas solicitudes de productos
   - Pueden aprobar, cancelar y gestionar solicitudes

Para configurar, ir a: **Configuración > Usuarios y Compañías > Grupos**

### URLs de Acceso

- **Cuentas Analíticas**: `https://tu-dominio.com/cuentas_analiticas/formulario`
- **Tarjetas de Crédito**: `https://tu-dominio.com/tarjeta_credito/formulario`
- **Productos**: `https://tu-dominio.com/producto/formulario` **(NUEVO)**

## Flujo de Trabajo

### Para Solicitudes de Producto

1. **Usuario completa el formulario web**
   - Ingresa todos los datos requeridos
   - Puede adjuntar archivo de variantes si aplica
   - Completa aspectos legales según sea necesario

2. **Sistema procesa la solicitud**
   - Se genera número de solicitud (SCP-XXXXX)
   - Se crea registro en estado "Solicitado"
   - Se envía email de confirmación al solicitante
   - Se notifica a usuarios del grupo "Aprobador de Productos"

3. **Aprobador revisa la solicitud**
   - Accede desde backend de Odoo
   - Puede aprobar o cancelar (con razón)

4. **Si se aprueba**
   - Pasa a estado "Aprobado"
   - Aprobador puede marcar como "Terminado"
   - Se notifica al solicitante

5. **Si se cancela**
   - Pasa a estado "Cancelado"
   - Se registra razón de cancelación
   - Se notifica al solicitante

## Notificaciones por Email

### Solicitudes de Producto
- **Al solicitar**: Confirmación al solicitante con número de solicitud
- **Al aprobar**: Notificación a aprobadores
- **Al terminar**: Notificación al solicitante de que fue procesada
- **Al cancelar**: Notificación al solicitante con razón de cancelación

## Vistas Backend

### Solicitudes de Producto
- **Menú**: Solicitudes > Solicitudes de Producto > Solicitudes
- **Vista Tree**: Lista de todas las solicitudes con colores por estado
- **Vista Form**: Detalle completo de la solicitud organizado en pestañas
  - Información del Producto
  - Aspectos Legales
- **Búsquedas y Filtros**: Por estado, solicitante, tipo de producto, etc.

## Secuencias

- Cuentas Analíticas: `SCA-XXXXX`
- Tarjetas de Crédito: `STC-XXXXX`
- Productos: `SCP-XXXXX` **(NUEVO)**

## Dependencias

- base
- website
- hr
- mail
- analytic

## Versión

- **Versión del módulo**: 17.0.1.0.0
- **Versión de Odoo**: 17.0

## Autor

**LOGYCA**
- Website: https://www.logyca.com

## Licencia

LGPL-3
