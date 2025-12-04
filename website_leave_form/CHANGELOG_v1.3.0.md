# Changelog - Versión 1.3.0

## Fecha: Noviembre 2025

### Nuevas Funcionalidades

#### 1. Imagen Guía para Incapacidades Médicas
- Se agregó una imagen guía informativa en el formulario web de ausencias
- La imagen muestra los aspectos que se deben tener en cuenta al reportar incapacidades médicas
- La imagen es clickeable y se puede ver en tamaño completo en una nueva pestaña
- Ubicación: Aparece en la parte superior del formulario, antes de los mensajes de éxito/error

**Ubicación de la imagen:**
- Directorio: `website_leave_form/static/src/img/guia_incapacidades.png`
- Para reemplazar la imagen, simplemente reemplace el archivo con el mismo nombre

#### 2. Restricción de Un Día Por Semestre
- Se agregó un nuevo campo en la configuración de tipos de ausencia: "Un día por semestre"
- Cuando este campo está activado para un tipo de ausencia, el sistema valida que el empleado no pueda solicitar más de un día de este tipo por semestre
- El sistema verifica automáticamente si ya existe una solicitud aprobada o pendiente en el mismo semestre

**Configuración:**
1. Ir a Recursos Humanos > Configuración > Tipos de Ausencia
2. Seleccionar el tipo de ausencia que desea restringir
3. Activar el campo "Un día por semestre" en la sección "Configuración Web"

**Comportamiento:**
- El semestre se calcula de la siguiente manera:
  - **Primer semestre:** Enero 1 - Junio 30
  - **Segundo semestre:** Julio 1 - Diciembre 31
- Si el empleado intenta crear una segunda solicitud del mismo tipo en el mismo semestre, recibirá un mensaje de error indicando que ya tiene una solicitud en ese semestre
- La validación considera solicitudes en estado: confirmado, aprobado o validado
- En el formulario web, cuando se selecciona un tipo con esta restricción, aparece una alerta amarilla informativa

**Mensaje de error:**
```
Ya tienes una solicitud de [Tipo de Ausencia] en el [primer/segundo] semestre de [año]. 
Solo se permite un día por semestre.
```

### Mejoras Técnicas

1. **Modelo `hr.leave.type`:**
   - Nuevo campo: `one_day_per_semester` (Boolean)
   - Ubicación: `models/hr_leave_type.py`

2. **Vista de Configuración:**
   - Actualizada la vista de formulario de tipos de ausencia
   - Ubicación: `views/hr_leave_type_views.xml`

3. **Template Web:**
   - Agregada tarjeta con imagen guía
   - Agregada alerta informativa para tipos con restricción
   - Agregado atributo `data-one-day-per-semester` en las opciones del select
   - Ubicación: `views/website_leave_form_templates.xml`

4. **Controlador:**
   - Agregada validación de límite de semestre en el método `submit_leave`
   - Ubicación: `controllers/website_leave_controller.py`

5. **JavaScript:**
   - Agregada lógica para mostrar/ocultar alerta cuando se selecciona un tipo con restricción
   - El ícono ⏱️ se muestra junto a los tipos con esta restricción

### Instrucciones de Actualización

1. **Actualizar el módulo:**
   ```bash
   # Copiar el módulo actualizado a la carpeta de addons
   # Reiniciar el servidor de Odoo
   # Actualizar el módulo desde la interfaz de Odoo
   ```

2. **Configurar tipos de ausencia con restricción:**
   - Ir a Recursos Humanos > Configuración > Tipos de Ausencia
   - Seleccionar los tipos que requieren restricción (ejemplo: "Día por calamidad doméstica")
   - Activar el checkbox "Un día por semestre"

3. **Verificar la imagen guía:**
   - Acceder al formulario web: `/ausencias/formulario`
   - Verificar que la imagen se muestra correctamente
   - Si necesita cambiar la imagen, reemplace el archivo en `static/src/img/guia_incapacidades.png`

### Notas Importantes

- La validación se ejecuta tanto en el backend como en el frontend
- El frontend muestra una alerta informativa preventiva
- El backend valida antes de crear la solicitud para garantizar la integridad
- Los semestres son fijos: Enero-Junio y Julio-Diciembre

### Compatibilidad

- Odoo 17.0
- Compatible con versiones anteriores del módulo
- No requiere migración de datos
