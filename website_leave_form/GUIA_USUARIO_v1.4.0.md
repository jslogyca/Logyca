# Guía Rápida de Usuario - Nuevas Funcionalidades v1.4.0

## 📧 1. Notificación a Talento y Cultura

### ¿Qué es?
Permite que ciertos tipos de ausencias (como Incapacidades y Licencias) envíen las notificaciones directamente al departamento de Talento y Cultura, en lugar del líder directo del empleado.

### ¿Cómo configurarlo?

#### Paso 1: Acceder a Tipos de Ausencia
1. Menú **Ausencias**
2. Click en **Configuración**
3. Click en **Tipos de Ausencia**

#### Paso 2: Configurar el Tipo de Ausencia
1. Abrir el tipo de ausencia que deseas configurar (ejemplo: "Incapacidad Médica")
2. Buscar la sección **"Configuración Web"**
3. Marcar el checkbox: ✅ **"Notificar a Talento y Cultura"**
4. Click en **Guardar**

![Ejemplo de configuración](screenshot aquí)

### ¿Qué sucede ahora?
- ✅ Las solicitudes de este tipo de ausencia se enviarán automáticamente a **todos** los usuarios del grupo "HR Manager"
- ✅ El empleado NO necesita seleccionar un aprobador
- ✅ Talento y Cultura recibirá el email con los botones de aprobación/rechazo

### Requisitos
⚠️ **Importante:** Los usuarios de Talento y Cultura deben tener asignado el rol **"HR Manager"** en:
- Menú **Ajustes > Usuarios y Compañías > Usuarios**
- Seleccionar usuario
- En pestaña **"Derechos de Acceso"**, marcar **"Responsable"** en la sección de Ausencias

---

## ⏰ 2. Aprobación Automática de Ausencias Pendientes

### ¿Qué es?
Sistema que aprueba automáticamente todas las ausencias que llevan mucho tiempo en estado "Pendiente", evitando que se acumulen solicitudes sin respuesta.

### Opciones de Uso

#### Opción A: Activar Aprobación Automática Mensual (Recomendado)

**¿Cuándo usar?** Si deseas que el sistema apruebe automáticamente todas las ausencias pendientes el primer día de cada mes.

**Pasos:**
1. Ir a **Ajustes > Técnico > Automatización > Acciones Planificadas**
2. Buscar: "Aprobación Automática de Ausencias Pendientes"
3. Abrir el registro
4. Marcar como ✅ **Activo**
5. Verificar que:
   - Intervalo: **1 Mes(es)**
   - Próxima Ejecución: Primer día del próximo mes a las 01:00 AM

**Resultado:**
- El sistema revisará todas las ausencias en estado "Enviado/Pendiente"
- Aprobará automáticamente las que estén pendientes hasta la fecha actual
- Enviará emails de confirmación a empleados y aprobadores

---

#### Opción B: Aprobación Manual desde la Interfaz

**¿Cuándo usar?** Para hacer una limpieza puntual de ausencias pendientes.

**Pasos:**
1. Activar **Modo Desarrollador**:
   - Ir a **Ajustes**
   - Buscar "Activar el modo de desarrollador"
   - Click en **Activar**

2. Ir a **Ausencias > Formularios Web > Formularios Web de Ausencias**

3. Aplicar filtros (opcional):
   - Estado: **Enviado**
   - Fecha de Solicitud: <= Fecha deseada

4. Seleccionar los registros (marcar checkboxes)

5. Click en **Acción ⚙️** > **Ejecutar Código Python**

6. Ingresar el siguiente código:
   ```python
   records.auto_approve_pending_leaves()
   ```

7. Click en **Ejecutar**

---

#### Opción C: Aprobación con Fecha Específica (Python Shell)

**¿Cuándo usar?** Para desarrollo o cuando necesitas especificar una fecha de corte exacta.

**Ejemplo 1: Aprobar todo hasta hoy**
```python
self.env['website.leave.form'].auto_approve_pending_leaves()
```

**Ejemplo 2: Aprobar todo hasta una fecha específica**
```python
from datetime import date

# Aprobar ausencias hasta el 30 de noviembre de 2025
fecha_corte = date(2025, 11, 30)
resultado = self.env['website.leave.form'].auto_approve_pending_leaves(cutoff_date=fecha_corte)

# Ver resultado
print(resultado)
# Output ejemplo:
# {
#     'total_pending': 15,
#     'approved': 14,
#     'errors': 1,
#     'error_messages': ['Error en ID 123: ...'],
#     'cutoff_date': datetime.date(2025, 11, 30)
# }
```

---

### ¿Qué hace el sistema exactamente?

1. ✅ Busca todas las ausencias en estado **"Enviado"** (pendientes de aprobación)
2. ✅ Filtra solo las que tienen fecha de solicitud <= fecha de corte
3. ✅ Aprueba cada ausencia en el sistema
4. ✅ Envía email de confirmación al empleado
5. ✅ Envía copia del email al aprobador original
6. ✅ Registra logs detallados de cada operación
7. ✅ Si una falla, continúa con las siguientes

### Revisar Logs

Para ver qué pasó durante la aprobación automática:

1. Ir a **Ajustes > Técnico > Estructura de la Base de Datos > Logging**
2. Buscar por:
   - **Ruta:** `website.leave.form`
   - **Función:** `auto_approve_pending_leaves`
3. Revisar mensajes de éxito y errores

---

## 🎯 Casos de Uso Recomendados

### Escenario 1: Cierre de Mes
**Situación:** Es fin de mes y hay ausencias pendientes que necesitan cerrarse.

**Solución:**
- Ejecutar manualmente desde la UI (Opción B)
- O esperar al cron automático del primer día del mes

### Escenario 2: Proceso Específico
**Situación:** Solo incapacidades deben ir a Talento y Cultura.

**Solución:**
1. Marcar solo el tipo "Incapacidad" con "Notificar a Talento y Cultura"
2. Los demás tipos seguirán el flujo normal al líder

### Escenario 3: Migración de Datos
**Situación:** Tienes ausencias antiguas pendientes que deseas aprobar en lote.

**Solución:**
- Usar Opción C con fecha de corte específica
- Revisar resultado retornado para validar

---

## ⚠️ Advertencias y Buenas Prácticas

### Para Notificación a Talento y Cultura:
- ❌ No marcar todos los tipos de ausencia, solo los que realmente lo requieran
- ✅ Verificar que los usuarios de TyC tienen email configurado
- ✅ Probar con un tipo primero antes de configurar masivamente

### Para Aprobación Automática:
- ❌ No activar el cron sin antes probarlo manualmente
- ❌ No ejecutar en horario laboral la primera vez (puede generar muchos emails)
- ✅ Revisar logs después de cada ejecución
- ✅ Informar al equipo antes de activar el cron automático
- ✅ Hacer backup antes de ejecutar por primera vez

---

## 🆘 Troubleshooting

### Problema: "No se envían emails a Talento y Cultura"
**Solución:**
1. Verificar que el checkbox esté marcado en el tipo de ausencia
2. Ir a Ajustes > Usuarios y verificar que los usuarios de TyC tienen el rol "HR Manager"
3. Verificar que los usuarios tienen email configurado
4. Revisar logs: Ajustes > Técnico > Logging

### Problema: "La aprobación automática no funciona"
**Solución:**
1. Verificar que el cron esté activo
2. Verificar que las ausencias estén en estado "Enviado"
3. Revisar fecha de próxima ejecución del cron
4. Revisar logs de ejecución

### Problema: "Algunas ausencias no se aprobaron"
**Solución:**
1. Ir a Ajustes > Técnico > Logging
2. Buscar mensajes de error en la función `auto_approve_pending_leaves`
3. Los errores individuales no detienen el proceso completo
4. Corregir el error y volver a ejecutar

---

## 📞 Soporte

Para dudas o problemas con estas funcionalidades, contactar al equipo de desarrollo o crear un ticket en el sistema de soporte.

---

**Última actualización:** Noviembre 2025  
**Versión del módulo:** 1.4.0
