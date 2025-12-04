# Changelog - Versión 1.3.1

## Fecha: Noviembre 2025

### Nueva Validación de Duración

#### Restricción de Duración Máxima de 1 Día

Para los tipos de ausencia que tienen activado el campo "Un día por semestre", ahora se valida que la duración de la solicitud no exceda 1 día (24 horas).

**Implementación:**

1. **Validación Frontend (JavaScript):**
   - Cuando el usuario selecciona un tipo con restricción de semestre
   - Se valida automáticamente la duración al cambiar las fechas
   - Si la duración excede 24 horas, se muestra una alerta
   - Se previene el envío del formulario si la validación falla

2. **Validación Backend (Python):**
   - Validación adicional en el servidor antes de crear la solicitud
   - Calcula la diferencia entre fecha inicio y fecha fin
   - Si excede 1 día, rechaza la solicitud con mensaje de error claro

**Mensaje de Alerta (Frontend):**
```
⏱️ Este tipo de ausencia solo permite una duración máxima de 1 día (24 horas).

Duración seleccionada: X.XX días

Por favor, ajusta las fechas.
```

**Mensaje de Error (Backend):**
```
Este tipo de ausencia solo permite una duración máxima de 1 día (24 horas). 
La duración seleccionada es de X.XX días.
```

### Mejoras en la Interfaz

#### Alerta Actualizada

La alerta amarilla que se muestra cuando se selecciona un tipo con restricción ahora incluye información sobre ambas restricciones:

```
⏱️ Restricción de Tiempo: Este tipo de ausencia tiene las siguientes restricciones:

• Duración máxima: Solo puedes solicitar 1 día (24 horas o menos)
• Frecuencia: Solo se permite un día por semestre

Si ya tienes una solicitud aprobada o pendiente de este tipo en el 
semestre actual, no podrás crear una nueva.
```

### Flujo de Validación Completo

```
Usuario selecciona tipo con restricción (one_day_per_semester = True)
           ↓
[Frontend] Muestra alerta con ambas restricciones:
           - Duración máxima: 1 día
           - Frecuencia: 1 vez por semestre
           ↓
Usuario ingresa fechas
           ↓
[Frontend] Valida duración en tiempo real:
           ├─► Si > 24 horas → Muestra alerta y previene envío
           └─► Si ≤ 24 horas → Permite continuar
           ↓
Usuario envía formulario
           ↓
[Backend] Valida en submit_leave():
           ├─► 1. Valida duración ≤ 1 día
           │   ├─► Si > 1 día → Rechaza con error
           │   └─► Si ≤ 1 día → Continúa
           │
           ├─► 2. Valida semestre
           │   ├─► Calcula semestre (Ene-Jun o Jul-Dic)
           │   ├─► Busca ausencias existentes
           │   ├─► Si existe → Rechaza con error
           │   └─► Si no existe → Continúa
           │
           └─► 3. Crea la solicitud exitosamente
```

### Casos de Uso

#### Caso 1: Solicitud Válida

```
✅ Tipo: Día por Calamidad ⏱️
✅ Fecha inicio: 15/03/2025 08:00
✅ Fecha fin: 15/03/2025 17:00
✅ Duración: 9 horas (0.38 días)
✅ Resultado: APROBADO
```

#### Caso 2: Duración Excedida

```
❌ Tipo: Día por Calamidad ⏱️
❌ Fecha inicio: 15/03/2025 08:00
❌ Fecha fin: 16/03/2025 17:00
❌ Duración: 33 horas (1.38 días)
❌ Resultado: RECHAZADO
   Frontend: Alerta antes de enviar
   Backend: Error si se intenta enviar
```

#### Caso 3: Exactamente 1 Día

```
✅ Tipo: Día por Calamidad ⏱️
✅ Fecha inicio: 15/03/2025 08:00
✅ Fecha fin: 16/03/2025 08:00
✅ Duración: 24 horas (1.00 día exacto)
✅ Resultado: APROBADO
```

### Archivos Modificados

1. **`views/website_leave_form_templates.xml`**
   - Actualizada la alerta de restricción con información de duración
   - Agregado JavaScript para validar duración en tiempo real
   - Agregado evento de validación en el submit del formulario

2. **`controllers/website_leave_controller.py`**
   - Agregada validación de duración antes de la validación de semestre
   - Cálculo de duración en días con 2 decimales
   - Mensaje de error descriptivo con la duración calculada

3. **`__manifest__.py`**
   - Versión actualizada a 17.0.1.3.1

### Notas Técnicas

**Cálculo de Duración:**
```python
duration = date_to - date_from
duration_in_days = duration.total_seconds() / (24 * 3600)
```

**Orden de Validaciones:**
1. Primero se valida la duración (más rápido)
2. Si pasa, se valida el semestre (requiere consulta BD)
3. Si ambas pasan, se crea la solicitud

**Ventajas:**
- Validación dual (frontend + backend)
- Feedback inmediato al usuario
- Prevención de errores antes del envío
- Seguridad adicional en el servidor

### Compatibilidad

- ✅ Compatible con versión 1.3.0
- ✅ No requiere migración de datos
- ✅ Retrocompatible con tipos sin restricción
- ✅ Odoo 17.0

### Actualización desde v1.3.0

No se requieren pasos adicionales. Simplemente:
1. Actualizar el módulo
2. Reiniciar el servidor
3. Las validaciones se aplicarán automáticamente

---

**Desarrollado:** Noviembre 2025  
**Versión:** 1.3.1  
**Estado:** ✅ Completado y Probado
