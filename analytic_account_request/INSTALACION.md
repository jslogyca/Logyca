# Guía de Instalación y Actualización

## Instalación Inicial (Nuevo)

### Requisitos Previos

- Odoo 17.0 instalado y funcionando
- Módulos base: `base`, `website`, `hr`, `mail`, `analytic`
- Acceso a la carpeta de addons de Odoo
- Permisos de administrador en Odoo

### Pasos de Instalación

1. **Copiar el módulo a la carpeta de addons**
   ```bash
   cp -r analytic_account_request /ruta/a/odoo/addons/
   ```

2. **Establecer permisos correctos**
   ```bash
   chown -R odoo:odoo /ruta/a/odoo/addons/analytic_account_request
   chmod -R 755 /ruta/a/odoo/addons/analytic_account_request
   ```

3. **Reiniciar el servicio de Odoo**
   ```bash
   sudo systemctl restart odoo
   # o
   sudo service odoo restart
   ```

4. **Actualizar la lista de aplicaciones**
   - Ir a **Aplicaciones**
   - Click en el menú de opciones (☰)
   - Seleccionar "Actualizar lista de Apps"
   - Eliminar el filtro "Apps" de la búsqueda
   - Buscar "Solicitud de Cuentas Analíticas"

5. **Instalar el módulo**
   - Click en "Instalar"
   - Esperar a que termine la instalación

6. **Configurar grupos de permisos**
   - Ir a **Configuración > Usuarios y Compañías > Grupos**
   - Buscar los grupos:
     - "Aprobador de Cuentas Analíticas"
     - "Aprobador de Tarjetas de Crédito"
     - "Aprobador de Productos"
   - Agregar los usuarios correspondientes a cada grupo

## Actualización del Módulo (Upgrade)

### Si ya tienes instalada una versión anterior

1. **Hacer backup de la base de datos**
   ```bash
   pg_dump nombre_bd > backup_antes_upgrade.sql
   ```

2. **Copiar la nueva versión del módulo**
   ```bash
   cp -r analytic_account_request /ruta/a/odoo/addons/
   ```

3. **Actualizar el módulo**
   
   **Opción A: Desde la interfaz**
   - Ir a **Aplicaciones**
   - Buscar "Solicitud de Cuentas Analíticas"
   - Click en el botón "Actualizar"

   **Opción B: Desde línea de comandos**
   ```bash
   odoo-bin -c /etc/odoo.conf -u analytic_account_request -d nombre_bd
   ```

4. **Verificar que todo funcione correctamente**
   - Acceder a los tres formularios web
   - Verificar que los menús estén correctos
   - Revisar que los permisos funcionen

## Verificación Post-Instalación

### 1. Verificar URLs de los Formularios

Acceder a:
- `https://tu-dominio.com/cuentas_analiticas/formulario`
- `https://tu-dominio.com/tarjeta_credito/formulario`
- `https://tu-dominio.com/producto/formulario`

### 2. Verificar Menús en Backend

Debe aparecer el menú:
```
Solicitudes
├── Cuentas Analíticas
│   └── Solicitudes
├── Solicitudes Tarjetas Crédito
│   └── Solicitudes
└── Solicitudes de Producto
    └── Solicitudes
```

### 3. Verificar Secuencias

Ir a **Configuración > Técnico > Secuencias** y buscar:
- Solicitud de Cuenta Analítica (SCA-)
- Solicitud de Tarjeta de Crédito (STC-)
- Solicitud de Creación de Producto (SCP-)

### 4. Verificar Templates de Email

Ir a **Configuración > Técnico > Correo Electrónico > Templates** y verificar que existan:
- Solicitud de Cuenta Analítica - Notificación a Aprobadores
- Solicitud de Cuenta Analítica - Confirmación
- Solicitud de Cuenta Analítica - Completada
- Solicitud de Cuenta Analítica - Cancelada
- Solicitud de Tarjeta de Crédito - Notificación a Aprobadores
- Tarjeta de Crédito - Confirmación
- Tarjeta de Crédito - Completada
- Tarjeta de Crédito - Cancelada
- Solicitud de Producto - Notificación a Aprobadores
- Solicitud de Producto - Confirmación
- Solicitud de Producto - Completada
- Solicitud de Producto - Cancelada

## Configuración Inicial Recomendada

### 1. Configurar Servidor de Correo

Para que funcionen las notificaciones:
- Ir a **Configuración > Técnico > Email > Servidores de Correo Saliente**
- Configurar un servidor SMTP válido
- Probar el envío

### 2. Asignar Aprobadores

Asignar al menos un usuario a cada grupo de aprobadores para recibir las notificaciones.

### 3. Crear Cuentas Analíticas de Prueba

Si aún no existen cuentas analíticas:
- Ir a **Contabilidad > Configuración > Contabilidad Analítica > Cuentas Analíticas**
- Crear algunas cuentas de prueba para cada compañía

### 4. Verificar Empleados

Asegurarse de que:
- Los empleados tengan configurado su `work_contact_id` (Partner relacionado)
- Los empleados tengan `work_email` configurado

## Desinstalación

Si necesitas desinstalar el módulo:

1. **Desinstalar desde Odoo**
   - Ir a **Aplicaciones**
   - Buscar el módulo
   - Click en "Desinstalar"

2. **Eliminar archivos**
   ```bash
   rm -rf /ruta/a/odoo/addons/analytic_account_request
   ```

3. **Reiniciar Odoo**
   ```bash
   sudo systemctl restart odoo
   ```

**Nota**: La desinstalación eliminará todos los datos de solicitudes.

## Troubleshooting

### Error: Módulo no aparece en lista de aplicaciones

1. Verificar que el módulo esté en la carpeta de addons correcta
2. Verificar permisos de archivos
3. Revisar logs de Odoo: `/var/log/odoo/odoo.log`
4. Verificar que el `__manifest__.py` sea válido

### Error: No se pueden enviar emails

1. Verificar configuración del servidor SMTP
2. Verificar que los usuarios tengan emails configurados
3. Revisar logs de Odoo para errores de envío
4. Probar envío manual desde Configuración > Técnico

### Error: Formulario web no carga

1. Verificar que el módulo `website` esté instalado
2. Verificar que no haya conflictos con otros módulos
3. Revisar logs del navegador (F12 > Console)
4. Verificar que la URL sea correcta

### Error: No se cargan las cuentas analíticas en el formulario de producto

1. Verificar que existan cuentas analíticas para la compañía seleccionada
2. Revisar la consola del navegador para errores JavaScript
3. Verificar que el endpoint `/producto/get_analytic_accounts` responda correctamente
4. Revisar logs de Odoo

## Migración de Datos

Si necesitas migrar datos de solicitudes de una instancia a otra:

1. **Exportar datos**
   - Ir a la vista tree de cada tipo de solicitud
   - Seleccionar todas las solicitudes
   - Acción > Exportar

2. **Importar datos**
   - En la nueva instancia, ir a la vista tree
   - Favoritos > Importar registros
   - Seleccionar el archivo exportado

**Nota**: Asegúrate de que los IDs de partners, compañías y empleados coincidan en ambas instancias.

## Soporte

Para soporte adicional:
- Revisar documentación en README.md y FORMULARIO_PRODUCTO.md
- Contactar al equipo de desarrollo de LOGYCA
- Revisar logs de Odoo en `/var/log/odoo/odoo.log`

## Changelog

### Versión 17.0.1.0.0
- Funcionalidad inicial de solicitud de cuentas analíticas
- Funcionalidad de solicitud de tarjetas de crédito
- **NUEVO**: Funcionalidad de solicitud de creación de producto
  - Formulario web completo con aspectos legales
  - Gestión de variantes con carga de archivos
  - Producto diferido con tiempo configurable
  - Integración con cuentas analíticas por compañía
  - Notificaciones por email en todas las etapas
  - Flujo de aprobación completo
