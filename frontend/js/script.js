let map;
let markers = [];
const API_BASE_URL = 'http://localhost:8000';

// Mapeado de colores para niveles de contaminación según estándares WHO/EU
const getColorForValue = (value, pollutant) => {
    const thresholds = {
        pm25: [12, 25, 50, 75],    // WHO guidelines
        pm10: [20, 40, 80, 120],   // WHO guidelines  
        no2: [40, 80, 120, 160],   // EU standards
        o3: [60, 120, 180, 240]    // EU standards
    };
    
    const levels = thresholds[pollutant] || [25, 50, 100, 150];
    
    if (value <= levels[0]) return '#00ff00'; // Verde - Bueno
    if (value <= levels[1]) return '#ffff00'; // Amarillo - Moderado
    if (value <= levels[2]) return '#ff8c00'; // Naranja - Insalubre para sensibles
    if (value <= levels[3]) return '#ff0000'; // Rojo - Insalubre
    return '#800080'; // Morado - Muy insalubre
};

// Obtener etiqueta de calidad del aire
const getQualityLabel = (value, pollutant) => {
    const thresholds = {
        pm25: [12, 25, 50, 75],
        pm10: [20, 40, 80, 120],
        no2: [40, 80, 120, 160],
        o3: [60, 120, 180, 240]
    };
    
    const levels = thresholds[pollutant] || [25, 50, 100, 150];
    const labels = ['Bueno', 'Moderado', 'Insalubre (Sensibles)', 'Insalubre', 'Muy Insalubre'];
    
    for (let i = 0; i < levels.length; i++) {
        if (value <= levels[i]) return labels[i];
    }
    return labels[4];
};

// Inicializar mapa centrado en España
function initMap() {
    map = L.map('map').setView([40.4168, -3.7038], 6);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

// Limpiar marcadores existentes
function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

// Actualizar estado de la aplicación
function updateStatus(message, isError = false) {
    const statusDiv = document.getElementById('status');
    statusDiv.innerHTML = `<p style="color: ${isError ? '#ff0000' : '#333'}">${message}</p>`;
}

// Añadir marcadores al mapa
function addMarkersToMap(data, pollutant) {
    clearMarkers();
    
    if (!data || data.length === 0) {
        updateStatus('No se encontraron datos para los parámetros seleccionados', true);
        return;
    }

    let validCount = 0;
    data.forEach(station => {
        const value = station[pollutant];
        if (value !== null && value !== undefined && !isNaN(value)) {
            const color = getColorForValue(value, pollutant);
            const quality = getQualityLabel(value, pollutant);
            
            const marker = L.circleMarker([station.latitude, station.longitude], {
                color: '#333',
                weight: 2,
                fillColor: color,
                fillOpacity: 0.8,
                radius: Math.max(6, Math.min(15, value / 5)) // Radio proporcional al valor
            }).addTo(map);
            
            marker.bindPopup(`
                <div style="font-family: Arial, sans-serif;">
                    <strong>${station.station_name}</strong><br>
                    <strong>${pollutant.toUpperCase()}:</strong> ${value.toFixed(1)} µg/m³<br>
                    <strong>Calidad:</strong> ${quality}<br>
                    <strong>Fecha:</strong> ${station.date}<br>
                    <strong>Coordenadas:</strong> ${station.latitude.toFixed(4)}, ${station.longitude.toFixed(4)}
                </div>
            `);
            
            markers.push(marker);
            validCount++;
        }
    });
    
    updateStatus(`Se han cargado ${validCount} estaciones con datos válidos`);
}

// Obtener datos de la API
async function fetchData(pollutant, date, hour = null) {
    updateStatus('Cargando datos...');
    
    try {
        let url = `${API_BASE_URL}/pollution?date=${date}`;
        if (hour !== null && hour !== '') {
            url += `&hour=${hour}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Error fetching data:', error);
        updateStatus(`Error al cargar datos: ${error.message}`, true);
        return [];
    }
}

// Cargar datos de prueba
async function loadSampleData() {
    updateStatus('Cargando datos de prueba...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/sample-data`);
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const result = await response.json();
        updateStatus(`Datos de prueba cargados: ${result.message}`);
        
        // Actualizar visualización con los datos de prueba
        setTimeout(() => updateVisualization(), 1000);
        
    } catch (error) {
        console.error('Error loading sample data:', error);
        updateStatus(`Error al cargar datos de prueba: ${error.message}`, true);
    }
}

// Actualizar estadísticas
function updateStats(data, pollutant) {
    const values = data
        .map(station => station[pollutant])
        .filter(value => value !== null && value !== undefined && !isNaN(value));
    
    if (values.length === 0) {
        document.getElementById('avg-value').textContent = '-';
        document.getElementById('max-value').textContent = '-';
        document.getElementById('min-value').textContent = '-';
        document.getElementById('station-count').textContent = '0';
        return;
    }
    
    const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
    const max = Math.max(...values);
    const min = Math.min(...values);
    
    document.getElementById('avg-value').textContent = `${avg.toFixed(1)} µg/m³`;
    document.getElementById('max-value').textContent = `${max.toFixed(1)} µg/m³`;
    document.getElementById('min-value').textContent = `${min.toFixed(1)} µg/m³`;
    document.getElementById('station-count').textContent = values.length;
}

// Actualizar tabla de datos
function updateDataTable(data, pollutant) {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = '';
    
    if (!data || data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5">No hay datos disponibles</td></tr>';
        return;
    }
    
    data.forEach(station => {
        const value = station[pollutant];
        if (value !== null && value !== undefined && !isNaN(value)) {
            const quality = getQualityLabel(value, pollutant);
            const color = getColorForValue(value, pollutant);
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${station.station_name}</td>
                <td>${station.latitude.toFixed(4)}</td>
                <td>${station.longitude.toFixed(4)}</td>
                <td>${value.toFixed(1)} µg/m³</td>
                <td><span style="color: ${color}; font-weight: bold;">${quality}</span></td>
            `;
            tableBody.appendChild(row);
        }
    });
}

// Función principal de actualización
async function updateVisualization() {
    const pollutant = document.getElementById('pollutant').value;
    const date = document.getElementById('date').value;
    const hour = document.getElementById('hour').value;
    
    const data = await fetchData(pollutant, date, hour);
    
    if (data && data.length > 0) {
        addMarkersToMap(data, pollutant);
        updateStats(data, pollutant);
        updateDataTable(data, pollutant);
    } else {
        clearMarkers();
        updateStats([], pollutant);
        updateDataTable([], pollutant);
    }
}

// Inicialización de la aplicación
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    
    // Event listeners
    document.getElementById('updateMap').addEventListener('click', updateVisualization);
    document.getElementById('loadSampleData').addEventListener('click', loadSampleData);
    
    // Actualización automática al cambiar controles
    document.getElementById('pollutant').addEventListener('change', updateVisualization);
    document.getElementById('date').addEventListener('change', updateVisualization);
    document.getElementById('hour').addEventListener('change', updateVisualization);
    
    updateStatus('Aplicación inicializada. Haz clic en "Cargar Datos de Prueba" para empezar.');
});
