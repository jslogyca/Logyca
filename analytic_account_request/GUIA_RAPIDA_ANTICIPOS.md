# 🚀 Guía Rápida - Solicitud de Anticipos

## ✅ Checklist de Instalación

### 1. Instalar Módulo
```bash
./odoo-bin -u analytic_account_request -d nombre_bd
```

### 2. Configurar Grupos de Seguridad
- Ir a: `Ajustes → Usuarios y Compañías → Usuarios`
- Seleccionar cada usuario aprobador
- Activar: `Aprobador de Anticipos`

### 3. Configurar Parámetros Contables
Ir a: `Ajustes → Solicitudes de Anticipos`

Completar:
- ✅ **Aprobador Financiero**: Usuario que dará visto bueno
- ✅ **Diario de Anticipos**: Seleccionar diario contable
- ✅ **Cuenta CXP**: Cuenta de cuentas por pagar (crédito)
- ✅ **Cuenta CXC**: Cuenta de cuentas por cobrar (débito)

### 4. Verificar Acceso
- Formulario web: `/anticipo/formulario`
- Menú backend: `Solicitudes Web → Solicitudes Anticipos → Solicitudes`

---

## 📋 Flujo Rápido de Uso

### Para el Solicitante (Web):
1. Acceder a `/anticipo/formulario`
2. Aceptar autorización de descuento
3. Completar todos los campos obligatorios (*)
4. Adjuntar soporte (opcional)
5. Enviar solicitud
6. Recibir email de confirmación

### Para el Aprobador (Backend):
1. Recibir email de notificación
2. Abrir solicitud en Odoo
3. Revisar información
4. Presionar botón **"Aprobar"**

### Para Financiera (Backend):
1. Abrir solicitud aprobada
2. Presionar **"Visto Bueno Financiero"**

### Para Contabilidad (Backend):
1. Abrir solicitud con visto bueno
2. Completar campo **"Proveedor/Empleado"**
3. Presionar **"Causar"**
4. Se crea asiento en borrador
5. Publicar asiento manualmente

### Para Tesorería (Backend):
1. Realizar el pago físico
2. Presionar **"Marcar como Pagado"**

### Finalización (Backend):
1. Presionar **"Terminar"**
2. Solicitud completa ✅

---

## 🔴 Errores Comunes y Soluciones

### ❌ "Faltan parámetros de contabilización"
**Causa**: No están configurados diario o cuentas
**Solución**: Ir a Settings y configurar los 3 campos de contabilización

### ❌ "No se ha configurado el aprobador financiero"
**Causa**: No hay usuario asignado como aprobador financiero
**Solución**: Ir a Settings → Aprobador Financiero de Anticipos

### ❌ "Debe llenar el campo Proveedor/Empleado antes de causar"
**Causa**: Campo vacío antes de intentar causar
**Solución**: En la solicitud, completar "Proveedor/Empleado" antes de causar

### ❌ "Solo el aprobador designado puede aprobar esta solicitud"
**Causa**: Usuario incorrecto intenta aprobar
**Solución**: Solo el usuario seleccionado en el campo "Aprobador" puede aprobar

### ❌ No veo el botón "Causar"
**Verificar**:
- Estado = "Aprobado"
- Visto bueno financiero dado (check verde visible)
- Usuario tiene permisos de "Aprobador de Anticipos"

---

## 📊 Estados del Flujo

```
Draft (Borrador)
  ↓ [Enviar Solicitud]
Requested (Solicitado) → 📧 Email a solicitante y aprobador
  ↓ [Aprobar]
Approved (Aprobado)
  ↓ [Visto Bueno Financiero]
Approved + ✅ Visto Bueno
  ↓ [Causar] → Crea asiento contable
Accounted (Causado)
  ↓ [Marcar como Pagado] → 📧 Email de pago
Paid (Pagado)
  ↓ [Terminar] → 📧 Email de finalización
Done (Terminado)

* Desde Requested se puede: [Cancelar] → Cancelled
```

---

## 🎯 Campos Obligatorios en Formulario Web

✅ **Autorización**: Debe marcar "SI, Acepto"
✅ **Nombre del Colaborador**
✅ **Número de Cédula** (auto-completado)
✅ **Organización**
✅ **Tipo**: Directo / Prestación de Servicios
✅ **Equipo** (Departamento)
✅ **Tipo de Anticipo**: Viaje / Compra
✅ **Internacional**: SI / NO
✅ **Monto**
✅ **Compañía que debe legalizar el gasto**
✅ **Aprobador**
✅ **Girar a nombre de**
✅ **Número de Cédula (Beneficiario)**

---

## 💡 Tips Importantes

1. **Política de Legalización**: El anticipo debe legalizarse en 3 días
2. **Fecha de Legalización**: Se calcula automáticamente (fecha entrega + 3 días)
3. **Asiento Contable**: Se crea en borrador, debe publicarse manualmente
4. **Información de Viaje**: Solo visible si "Tipo de Anticipo" = Viaje
5. **Archivo Adjunto**: Opcional pero recomendado
6. **Email de Recordatorio**: Se envía al marcar como pagado

---

## 📧 Notificaciones por Email

| Evento | Destinatario | Contenido |
|--------|-------------|-----------|
| Solicitud enviada | Solicitante | Confirmación + número |
| Solicitud enviada | Aprobador | Notificación pendiente |
| Marcado como pagado | Solicitante | Pago + recordatorio legalización |
| Terminado | Solicitante | Finalización |

---

## 🔗 Enlaces Rápidos

- **Formulario Web**: `/anticipo/formulario`
- **Solicitudes Backend**: `Solicitudes Web → Solicitudes Anticipos`
- **Configuración**: `Ajustes → Solicitudes de Anticipos`
- **Usuarios**: `Ajustes → Usuarios y Compañías → Usuarios`

---

## 📞 ¿Necesitas Ayuda?

1. Revisar esta guía rápida
2. Ver documentación completa: `DOCUMENTACION_ANTICIPOS.md`
3. Verificar configuración en Settings
4. Contactar administrador del sistema
