# 📋 Módulo de Solicitud de Anticipos - Documentación Completa

## 📝 Descripción General

El módulo de **Solicitud de Anticipos** permite a los colaboradores solicitar anticipos de dinero a través de un formulario web público, con un flujo completo de aprobación, causación contable y seguimiento.

---

## 🎯 Características Principales

### 1. **Formulario Web Público**
- Accesible en: `/anticipo/formulario`
- 22 campos configurables
- Validación de autorización de descuento por nómina
- Carga de archivos adjuntos
- Campos dinámicos según tipo de anticipo

### 2. **Flujo de Estados**
```
Draft → Requested → Approved → Accounted → Paid → Done
         ↓
    Cancelled (opcional desde Requested)
```

### 3. **Integración Contable**
- Creación automática de asientos contables
- Configuración de cuentas CXP y CXC
- Diario personalizable
- Enlace directo al asiento desde la solicitud

### 4. **Notificaciones por Email**
- Confirmación al solicitante
- Notificación a aprobadores
- Aviso de pago
- Confirmación de finalización

---

## 📋 Campos del Formulario

### Autorización (Obligatorio)
- **Autorización descuento por nómina**: SI/NO con texto de política

### Información del Colaborador
1. **Nombre del Colaborador** (res.partner) - Filtrado por empleados activos
2. **Número de Cédula** (Char) - Auto-completado desde empleado
3. **Organización** (res.company)
4. **Tipo** (Selection): Directo / Prestación de Servicios
5. **Equipo** (hr.department) - Filtrado por compañía
6. **Aprobador** (res.users) - Del grupo de aprobadores

### Información del Anticipo
7. **Tipo de Anticipo** (Selection): Viaje / Compra
8. **Internacional** (Selection): SI / NO
9. **Monto** (Float)
10. **Compañía que debe legalizar el gasto** (res.company)

### Información de Viaje (Solo si Tipo = Viaje)
11. **Ciudad de Origen** (Char)
12. **Ciudad Destino** (Char)
13. **Fecha de Salida** (Date)
14. **Fecha de Regreso** (Date)

### Información del Pago
15. **Girar a nombre de** (Char)
16. **Número de Cédula (Beneficiario)** (Char)
17. **Entregar a** (Char)
18. **Fecha de entrega de anticipo** (Date)
19. **Fecha de presunta legalización** (Date) - Calculado: entrega + 3 días

### Documentación
20. **Adjuntar soporte** (ir.attachment) - Factura proforma / cuenta de cobro

### Adicionales
21. **Observaciones** (Text)
22. **Proveedor/Empleado** (res.partner) - No visible en web, se llena en backend

---

## 🔄 Flujo de Trabajo Detallado

### 1. **Creación de Solicitud (Draft → Requested)**
**Acción**: Usuario completa formulario web

**Proceso**:
- Sistema genera número de solicitud (ANT-00001)
- Validación de campos obligatorios
- Validación de autorización = "SI"
- Carga de archivo adjunto (opcional)
- Estado cambia a "Requested"

**Notificaciones**:
- ✉️ Email de confirmación al solicitante
- ✉️ Email al aprobador designado

---

### 2. **Aprobación (Requested → Approved)**
**Acción**: Aprobador presiona botón "Aprobar"

**Validaciones**:
- Solo el aprobador designado puede aprobar
- Estado debe ser "Requested"

**Proceso**:
- Estado cambia a "Approved"
- Se registra fecha de aprobación

---

### 3. **Visto Bueno Financiero (Approved)**
**Acción**: Aprobador financiero presiona "Visto Bueno Financiero"

**Validaciones**:
- Solo el aprobador financiero configurado en Settings
- Estado debe ser "Approved"

**Proceso**:
- Campo `financial_approved = True`
- Se registra fecha y usuario que aprobó
- Botón "Causar" se hace visible

**Configuración**:
```
Settings → Solicitudes de Anticipos → Aprobador Financiero de Anticipos
```

---

### 4. **Causación Contable (Approved → Accounted)**
**Acción**: Usuario presiona botón "Causar"

**Validaciones**:
- Estado = "Approved"
- `financial_approved = True`
- Campo `supplier_employee_id` debe estar lleno

**Proceso**:
1. Lee configuración de Settings:
   - Diario de Anticipos
   - Cuenta CXP
   - Cuenta CXC

2. Crea asiento contable (`account.move`):
   ```
   REF: "CONTABILIZACION ANTICIPOS ANT-00001"
   Estado: Borrador (draft)
   
   Líneas:
   - CXP (Crédito): $monto - Tercero: supplier_employee_id
   - CXC (Débito): $monto - Tercero: supplier_employee_id
   
   name (ambas líneas): contenido del campo Observaciones
   ```

3. Estado cambia a "Accounted"

**Configuración requerida**:
```
Settings → Solicitudes de Anticipos:
- Diario de Anticipos (account.journal)
- Cuenta CXP para Anticipos (account.account)
- Cuenta CXC para Anticipos (account.account)
```

---

### 5. **Pago (Accounted → Paid)**
**Acción**: Usuario presiona "Marcar como Pagado"

**Validaciones**:
- Estado = "Accounted"

**Proceso**:
- Estado cambia a "Paid"

**Notificaciones**:
- ✉️ Email al solicitante indicando que el anticipo fue pagado
- ⚠️ Recordatorio de legalización en 3 días

---

### 6. **Finalización (Paid → Done)**
**Acción**: Usuario presiona "Terminar"

**Validaciones**:
- Estado = "Paid"

**Proceso**:
- Estado cambia a "Done"

**Notificaciones**:
- ✉️ Email al solicitante confirmando finalización

---

### 7. **Cancelación (Requested → Cancelled)**
**Acción**: Aprobador presiona "Cancelar"

**Validaciones**:
- Estado = "Requested"

**Proceso**:
- Abre wizard para ingresar razón de cancelación
- Estado cambia a "Cancelled"

---

## ⚙️ Configuración Inicial

### 1. **Grupos de Seguridad**

Asignar usuarios al grupo:
```
Ajustes → Usuarios → [Usuario] → Permisos → Aprobador de Anticipos
```

### 2. **Configuración de Anticipos**

Ir a: `Ajustes → Solicitudes de Anticipos`

Configurar:
1. **Aprobador Financiero de Anticipos**: Usuario que dará visto bueno financiero
2. **Diario de Anticipos**: Diario contable para asientos
3. **Cuenta CXP**: Cuenta de Cuentas por Pagar (movimiento al crédito)
4. **Cuenta CXC**: Cuenta de Cuentas por Cobrar (movimiento al débito)

### 3. **Verificación de Secuencia**

La secuencia se crea automáticamente:
- Código: `advance.request`
- Prefijo: `ANT-`
- Formato: `ANT-00001`

---

## 📧 Templates de Email

### 1. **Confirmación al Solicitante**
- **Cuando**: Solicitud enviada (Draft → Requested)
- **Para**: Solicitante
- **Contiene**: Número de solicitud, tipo, monto, aprobador, recordatorio de política

### 2. **Notificación a Aprobadores**
- **Cuando**: Solicitud enviada (Draft → Requested)
- **Para**: Aprobador designado
- **Contiene**: Datos completos de la solicitud

### 3. **Notificación de Pago**
- **Cuando**: Marcado como pagado (Accounted → Paid)
- **Para**: Solicitante
- **Contiene**: Confirmación de pago, recordatorio de legalización, fecha límite

### 4. **Confirmación de Finalización**
- **Cuando**: Solicitud terminada (Paid → Done)
- **Para**: Solicitante
- **Contiene**: Resumen final de la solicitud

---

## 🔐 Permisos

### Usuario Base
- **Leer**: Todas las solicitudes
- **Crear**: No
- **Modificar**: No
- **Eliminar**: No

### Aprobador de Anticipos
- **Leer**: Todas las solicitudes
- **Crear**: Sí
- **Modificar**: Sí
- **Eliminar**: Sí
- **Acciones especiales**:
  - Aprobar solicitudes
  - Dar visto bueno financiero
  - Causar
  - Marcar como pagado
  - Terminar
  - Cancelar

---

## 🎨 Vistas Disponibles

### 1. **Vista Tree (Lista)**
Muestra:
- Número
- Fecha de solicitud
- Colaborador
- Compañía
- Tipo de anticipo
- Monto
- Aprobador
- Estado (con colores)

### 2. **Vista Form (Formulario)**
Secciones:
- Botones de acción en header
- Título con número
- Alerta de visto bueno financiero
- Autorización
- Información del colaborador
- Información del anticipo
- Información de viaje (condicional)
- Información del pago
- Documentación
- Observaciones
- Información contable
- Razón de cancelación (si aplica)
- Auditoría

### 3. **Vista Search (Búsqueda)**
Filtros:
- Por estado (draft, requested, approved, etc.)
- Por tipo (viaje, compra)
- Por colaborador
- Por compañía
- Por aprobador

Agrupación por:
- Estado
- Colaborador
- Compañía
- Tipo de anticipo
- Aprobador

---

## 📊 Reportes y Análisis

### Datos Rastreados
- Fecha de solicitud
- Fecha de aprobación
- Fecha de visto bueno financiero
- Fecha de causación
- Fecha de pago
- Todas las modificaciones de campos (tracking=True)

### Información de Auditoría
- Historial completo en chatter
- Seguidores automáticos
- Actividades programables

---

## 🔍 Casos de Uso

### Caso 1: Anticipo para Viaje Nacional
```
1. Colaborador completa formulario web
   - Tipo: Viaje
   - Internacional: NO
   - Ciudades y fechas
   
2. Aprobador revisa y aprueba

3. Financiera da visto bueno

4. Contabilidad llena campo Proveedor/Empleado y causa

5. Tesorería marca como pagado

6. Se finaliza la solicitud
```

### Caso 2: Anticipo para Compra
```
1. Colaborador completa formulario web
   - Tipo: Compra
   - Adjunta factura proforma
   
2. Flujo igual al caso 1 (pasos 2-6)
```

---

## ⚠️ Puntos Importantes

### Política de Legalización
- **Plazo**: 3 días posteriores al recibo
- **Cálculo automático**: `delivery_date + 3 días`
- **Recordatorio**: En email de pago

### Validaciones Críticas
1. **Autorización**: Debe ser "SI" para enviar
2. **Aprobador correcto**: Solo el designado puede aprobar
3. **Visto bueno financiero**: Requerido antes de causar
4. **Proveedor/Empleado**: Requerido para causar

### Flujo Contable
- Asiento se crea en **borrador**
- Usuario debe publicar manualmente el asiento
- Al causar, la solicitud pasa automáticamente a "Accounted"

---

## 🚀 Instalación

1. Copiar módulo a addons
2. Actualizar lista de aplicaciones
3. Instalar módulo
4. Configurar grupos de seguridad
5. Configurar parámetros en Settings
6. Acceder al formulario: `/anticipo/formulario`

---

## 📱 Acceso al Formulario Web

**URL**: `https://tu-dominio.com/anticipo/formulario`

**Características**:
- Acceso público (no requiere login)
- Responsive (móvil y desktop)
- Validaciones en tiempo real
- Auto-completado de campos
- Mensajes de éxito/error

---

## 🐛 Troubleshooting

### Error: "Faltan parámetros de contabilización"
**Solución**: Configurar diario y cuentas en Settings → Solicitudes de Anticipos

### Error: "No se ha configurado el aprobador financiero"
**Solución**: Asignar usuario en Settings → Aprobador Financiero de Anticipos

### Error: "Debe llenar el campo Proveedor/Empleado"
**Solución**: Completar campo en formulario backend antes de causar

### No aparece botón "Causar"
**Verificar**:
1. Estado = "Approved"
2. Visto bueno financiero dado
3. Usuario pertenece a grupo de aprobadores

---

## 📞 Soporte

Para dudas o problemas:
- Revisar esta documentación
- Verificar configuración en Settings
- Revisar permisos de usuario
- Contactar administrador del sistema

---

## 🔄 Actualización del Módulo

```bash
./odoo-bin -u analytic_account_request -d nombre_bd
```

---

**Versión**: 1.0.0
**Última actualización**: 2024
**Autor**: LOGYCA
