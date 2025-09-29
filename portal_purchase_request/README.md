# Portal de Solicitudes de Compra

Este módulo introduce un sistema para la gestión de solicitudes de compra iniciadas por colaboradores. Su objetivo es centralizar y formalizar el proceso de recepción de requerimientos, reemplazando métodos menos estructurados como correos electrónicos o llamadas.

### Gestión desde el Portal del Partner

El módulo habilita una sección dedicada en el portal de cliente, desde la cual los colaboradores pueden generar solicitudes de compra. A través de un formulario, especifican los productos y las cantidades que necesitan y envían la solicitud directamente al sistema Odoo.

Adicionalmente, el portal ofrece a los colaboradores visibilidad completa sobre el ciclo de vida de sus solicitudes. Pueden consultar en tiempo real el estado de cada una (ej. Recibida, En Revisión, Aprobada, Rechazada), lo que garantiza la transparencia del proceso.

### Proceso de Aprobación y Conversión Interna

Cada solicitud enviada desde el portal se registra en el backend del módulo de Compras para ser procesada por el equipo interno. Las solicitudes siguen un flujo de aprobación definido, pasando por estados como "Borrador", "Para Aprobar", "Aprobado" y "Rechazado".

Los usuarios con los permisos adecuados tienen la facultad de revisar el detalle de cada solicitud y autorizarla o denegarla. El sistema notifica automáticamente al partner sobre los cambios de estado relevantes, optimizando la comunicación.

La funcionalidad principal del flujo es la capacidad de convertir una solicitud aprobada en una o varias Órdenes de Compra formales. Un asistente guía al usuario en este proceso, permitiendo agrupar las líneas de producto por proveedor para generar los documentos de compra correspondientes. Esto minimiza la entrada manual de datos y reduce el riesgo de errores, asegurando la integridad de la información desde la petición inicial hasta la compra final.

### Funcionalidades Principales

*   **Portal de Solicitudes:** Interfaz dedicada para que los colaboradores registren y gestionen sus requerimientos de compra.
*   **Flujo de Aprobación:** Proceso de validación interno para controlar y autorizar las solicitudes antes de proceder con la compra.
*   **Conversión a Órdenes de Compra:** Herramienta para generar eficientemente Órdenes de Compra a partir de solicitudes aprobadas.
*   **Notificaciones Automáticas:** Comunicación constante con el partner sobre el progreso de sus solicitudes.
*   **Trazabilidad del Proceso:** Vinculación completa entre la solicitud de portal, la aprobación interna y la orden de compra final.

### Configuración Inicial

La implementación del módulo requiere una configuración mínima para estar operativo.

1.  **Asignación de Roles:** Se debe asignar el grupo de permisos "Aprobador de Solicitudes de Compra del Portal" a los usuarios internos que serán responsables de la validación de las solicitudes.
2.  **Acceso de colaboradores:** Es necesario verificar que los colaboradores correspondientes tengan el acceso al portal habilitado. La funcionalidad de solicitudes de compra aparecerá automáticamente en su interfaz.
