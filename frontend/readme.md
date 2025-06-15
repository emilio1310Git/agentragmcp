# Frontend - Monitor de Calidad del Aire

## 📁 Estructura del Proyecto

```
frontend/
├── index.html          # Página principal de la aplicación
├── css/
│   └── styles.css      # Estilos CSS con variables y diseño responsive
├── js/
│   └── script.js       # Lógica JavaScript principal
└── README.md           # Este archivo
```

## 🚀 Funcionalidades

### **Visualización Interactiva:**
- Mapa de España con marcadores de estaciones de monitoreo
- Código de colores basado en estándares WHO/EU
- Popups informativos con detalles de cada estación

### **Panel de Control:**
- Selector de contaminante (PM2.5, PM10, NO2, O3)
- Selector de fecha y hora
- Botones para cargar datos y actualizar visualización

### **Estadísticas en Tiempo Real:**
- Promedio, máximo y mínimo de contaminantes
- Número de estaciones activas
- Tabla detallada con datos de cada estación

### **Gestión de Datos:**
- Integración completa con API FastAPI
- Carga de datos de prueba sintéticos
- Gestión de errores y estados de carga

## 🛠️ Instalación y Uso

### **1. Preparar los Archivos:**
```bash
# Crear estructura de carpetas
mkdir -p frontend/css frontend/js

# Copiar cada archivo a su ubicación correspondiente
# (ver contenido arriba para cada archivo)
```

### **2. Configurar Servidor:**
```bash
# Asegúrate de que tu API FastAPI esté ejecutándose
uvicorn main:app --reload
```

### **3. Abrir la Aplicación:**
- Abre `frontend/index.html` en tu navegador
- O usa un servidor local: `python -m http.server 8080`

### **4. Probar Funcionalidades:**
1. Haz clic en "Cargar Datos de Prueba"
2. Experimenta con diferentes contaminantes
3. Cambia fechas y horas
4. Observa las actualizaciones en tiempo real

## 🎨 Personalización

### **Colores y Temas:**
Modifica las variables CSS en `styles.css`:
```css
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    /* ... más variables ... */
}
```

### **Configuración API:**
Cambia la URL base en `script.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### **Umbrales de Contaminación:**
Ajusta los niveles en `script.js`:
```javascript
const thresholds = {
    pm25: [12, 25, 50, 75],  // Valores WHO
    // ... otros contaminantes ...
};
```

## 📱 Características Técnicas

- **Responsive Design:** Funciona en desktop, tablet y móvil
- **Mapas Interactivos:** Leaflet.js para visualización geográfica
- **Estándares Web:** HTML5, CSS3, ES6+
- **Sin Dependencias:** Excepto Leaflet para mapas
- **Cross-browser:** Compatible con navegadores modernos

## 🔧 Solución de Problemas

### **CORS Error:**
Si aparece error de CORS, asegúrate de que tu API FastAPI tenga configurado:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **No se cargan los datos:**
1. Verifica que la API esté ejecutándose en `http://localhost:8000`
2. Comprueba la consola del navegador para errores
3. Prueba primero con "Cargar Datos de Prueba"

### **Mapa no aparece:**
1. Verifica conexión a internet (requiere Leaflet CDN)
2. Comprueba que no haya errores JavaScript en consola
3. Asegúrate de que `leaflet.css` se carga correctamente