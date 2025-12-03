// ================================================================
// CONFIGURACIÓN
// CAMBIA ESTA IP A LA DE TU RASPBERRY PI
// ================================================================
const API_URL = 'http://192.168.0.200:8000/api';
const UPDATE_INTERVAL = 3000; // Actualizar cada 3 segundos

// ================================================================
// VARIABLES GLOBALES
// ================================================================
let tempChart, humChart;

// Colores del tema terminal
const COLORS = {
    green: '#00ff00',
    darkGreen: '#00aa00',
    black: '#000000',
    red: '#ff0000'
};

// Colores para cada sensor en los gráficos
const SENSOR_COLORS = ['#00ff00', '#00ffff', '#ffff00', '#ff00ff'];

// ================================================================
// CONFIGURACIÓN DE CHART.JS
// ================================================================
Chart.defaults.color = COLORS.green;
Chart.defaults.borderColor = '#003300';

const chartConfig = {
    type: 'line',
    options: {
        responsive: true,
        maintainAspectRatio: true,
        interaction: {
            intersect: false,
            mode: 'index'
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    color: COLORS.green,
                    font: {
                        family: "'Press Start 2P', monospace",
                        size: 10
                    },
                    padding: 20
                }
            }
        },
        scales: {
            x: {
                ticks: {
                    color: COLORS.darkGreen,
                    font: {
                        family: "'Press Start 2P', monospace",
                        size: 8
                    },
                    maxRotation: 45,
                    minRotation: 45
                },
                grid: {
                    color: '#003300'
                }
            },
            y: {
                beginAtZero: false,
                ticks: {
                    color: COLORS.darkGreen,
                    font: {
                        family: "'Press Start 2P', monospace",
                        size: 8
                    }
                },
                grid: {
                    color: '#003300'
                }
            }
        }
    }
};

// ================================================================
// INICIALIZACIÓN DE GRÁFICOS
// ================================================================
function initCharts() {
    const ctxTemp = document.getElementById('tempChart').getContext('2d');
    tempChart = new Chart(ctxTemp, {
        ...chartConfig,
        data: {
            labels: [],
            datasets: []
        }
    });
    
    const ctxHum = document.getElementById('humChart').getContext('2d');
    humChart = new Chart(ctxHum, {
        ...chartConfig,
        data: {
            labels: [],
            datasets: []
        }
    });
}

// ================================================================
// TARJETAS DE PLANTAS
// ================================================================
function createPlantaCard(data) {
    const { sensor, planta, medicion } = data;
    
    const alertaTemp = medicion.alerta_temp;
    const alertaHum = medicion.alerta_humedad;
    const tieneAlerta = alertaTemp || alertaHum;
    
    return `
        <div class="planta-card ${tieneAlerta ? 'alerta' : ''}">
            <div class="planta-header">
                <div>
                    <div class="planta-nombre">🌱 ${planta?.nombre || 'Sin planta'}</div>
                    <div class="planta-ubicacion">${sensor.ubicacion}</div>
                </div>
                <div class="planta-ubicacion">${sensor.nombre}</div>
            </div>
            
            <div class="planta-datos">
                <div class="dato">
                    <div class="dato-label">TEMPERATURA</div>
                    <div class="dato-valor ${alertaTemp ? 'alerta' : ''}">
                        ${medicion.temperatura.toFixed(1)}°C
                    </div>
                </div>
                <div class="dato">
                    <div class="dato-label">HUMEDAD</div>
                    <div class="dato-valor ${alertaHum ? 'alerta' : ''}">
                        ${medicion.humedad.toFixed(1)}%
                    </div>
                </div>
            </div>
            
            ${planta ? `
                <div class="planta-rangos">
                    <div class="rango-item">🌡️ TEMP: ${planta.temp_min}°C - ${planta.temp_max}°C</div>
                    <div class="rango-item">💧 HUM: ${planta.humedad_min}% - ${planta.humedad_max}%</div>
                </div>
            ` : ''}
            
            ${tieneAlerta ? '<div class="alerta-text">⚠️ FUERA DE RANGO</div>' : ''}
        </div>
    `;
}

async function updatePlantas() {
    try {
        const response = await fetch(`${API_URL}/mediciones/ultimas`);
        const data = await response.json();
        
        const container = document.getElementById('plantasContainer');
        container.innerHTML = data.map(createPlantaCard).join('');
        
    } catch (error) {
        console.error('❌ Error al actualizar plantas:', error);
    }
}

// ================================================================
// GRÁFICOS
// ================================================================
async function updateCharts() {
    try {
        // Obtener lista de sensores
        const sensoresRes = await fetch(`${API_URL}/sensores`);
        const sensores = await sensoresRes.json();
        
        const datasetsTemp = [];
        const datasetsHum = [];
        let labels = [];
        
        // Obtener datos de cada sensor
        for (let i = 0; i < sensores.length; i++) {
            const sensor = sensores[i];
            const medicionesRes = await fetch(`${API_URL}/mediciones/sensor/${sensor.id}?limit=30`);
            
            if (!medicionesRes.ok) continue;
            
            const mediciones = await medicionesRes.json();
            
            if (mediciones.length > 0 && labels.length === 0) {
                labels = mediciones.map(m => m.hora);
            }
            
            const color = SENSOR_COLORS[i % SENSOR_COLORS.length];
            
            datasetsTemp.push({
                label: sensor.nombre,
                data: mediciones.map(m => m.temperatura),
                borderColor: color,
                backgroundColor: 'transparent',
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: color,
                pointBorderColor: COLORS.black,
                pointBorderWidth: 1
            });
            
            datasetsHum.push({
                label: sensor.nombre,
                data: mediciones.map(m => m.humedad),
                borderColor: color,
                backgroundColor: 'transparent',
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: color,
                pointBorderColor: COLORS.black,
                pointBorderWidth: 1
            });
        }
        
        // Actualizar gráficos
        tempChart.data.labels = labels;
        tempChart.data.datasets = datasetsTemp;
        tempChart.update('none');
        
        humChart.data.labels = labels;
        humChart.data.datasets = datasetsHum;
        humChart.update('none');
        
    } catch (error) {
        console.error('❌ Error al actualizar gráficos:', error);
    }
}

// ================================================================
// ESTADÍSTICAS GENERALES
// ================================================================
async function updateEstadisticas() {
    try {
        const response = await fetch(`${API_URL}/estadisticas`);
        const stats = await response.json();
        
        document.getElementById('sensoresActivos').textContent = stats.sensores_activos;
        document.getElementById('totalPlantas').textContent = stats.plantas;
        document.getElementById('totalMediciones').textContent = stats.total_mediciones;
        
        // Actualizar estado de conexión
        document.getElementById('statusText').textContent = 'CONNECTED';
        document.getElementById('statusText').style.color = COLORS.green;
        
    } catch (error) {
        console.error('❌ Error al actualizar estadísticas:', error);
        document.getElementById('statusText').textContent = 'ERROR';
        document.getElementById('statusText').style.color = COLORS.red;
    }
}

// ================================================================
// ACTUALIZACIÓN COMPLETA
// ================================================================
async function updateAll() {
    await Promise.all([
        updatePlantas(),
        updateCharts(),
        updateEstadisticas()
    ]);
}

// ================================================================
// INICIALIZACIÓN
// ================================================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Iniciando Jardín IoT Monitor...');
    console.log(`📡 API URL: ${API_URL}`);
    
    initCharts();
    updateAll();
    
    // Auto-actualización
    setInterval(updateAll, UPDATE_INTERVAL);
    console.log(`✓ Auto-actualización cada ${UPDATE_INTERVAL/1000} segundos`);
});