// Configuración de la API - CAMBIA LA IP A LA DE TU RASPBERRY
const API_URL = 'http://192.168.0.200:8000/api';
const UPDATE_INTERVAL = 3000; // 3 segundos

let tempChart, humChart;

// Colores verde terminal
const greenColor = '#00ff00';
const darkGreen = '#00aa00';
const black = '#000000';
const redColor = '#ff0000';

// Configurar gráficos estilo terminal
Chart.defaults.color = greenColor;
Chart.defaults.borderColor = '#003300';

const chartConfig = {
    type: 'line',
    options: {
        responsive: true,
        interaction: {
            intersect: false,
            mode: 'index'
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    color: greenColor,
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
                    color: darkGreen,
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
                    color: darkGreen,
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

// Colores para cada sensor
const sensorColors = ['#00ff00', '#00ffff', '#ffff00'];

// Inicializar gráficos
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

// Crear tarjeta de planta
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
                    <div class="rango-item">TEMP: ${planta.temp_min}°C - ${planta.temp_max}°C</div>
                    <div class="rango-item">HUM: ${planta.humedad_min}% - ${planta.humedad_max}%</div>
                </div>
            ` : ''}
            
            ${tieneAlerta ? '<div style="color: #ff0000; text-align: center; margin-top: 10px; font-size: 0.5em;">⚠️ FUERA DE RANGO</div>' : ''}
        </div>
    `;
}

// Actualizar tarjetas de plantas
async function updatePlantas() {
    try {
        const response = await fetch(`${API_URL}/mediciones/ultimas`);
        const data = await response.json();
        
        const container = document.getElementById('plantasContainer');
        container.innerHTML = data.map(createPlantaCard).join('');
        
    } catch (error) {
        console.error('Error al actualizar plantas:', error);
    }
}

// Actualizar gráficos
async function updateCharts() {
    try {
        // Obtener datos de todos los sensores
        const sensoresRes = await fetch(`${API_URL}/sensores`);
        const sensores = await sensoresRes.json();
        
        const datasetsTemp = [];
        const datasetsHum = [];
        let labels = [];
        
        for (let i = 0; i < sensores.length; i++) {
            const sensor = sensores[i];
            const medicionesRes = await fetch(`${API_URL}/mediciones/sensor/${sensor.id}?limit=30`);
            const mediciones = await medicionesRes.json();
            
            if (mediciones.length > 0 && labels.length === 0) {
                labels = mediciones.map(m => m.hora);
            }
            
            datasetsTemp.push({
                label: sensor.nombre,
                data: mediciones.map(m => m.temperatura),
                borderColor: sensorColors[i % sensorColors.length],
                backgroundColor: 'transparent',
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: sensorColors[i % sensorColors.length]
            });
            
            datasetsHum.push({
                label: sensor.nombre,
                data: mediciones.map(m => m.humedad),
                borderColor: sensorColors[i % sensorColors.length],
                backgroundColor: 'transparent',
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: sensorColors[i % sensorColors.length]
            });
        }
        
        tempChart.data.labels = labels;
        tempChart.data.datasets = datasetsTemp;
        tempChart.update('none');
        
        humChart.data.labels = labels;
        humChart.data.datasets = datasetsHum;
        humChart.update('none');
        
    } catch (error) {
        console.error('Error al actualizar gráficos:', error);
    }
}

// Actualizar estadísticas generales
async function updateEstadisticas() {
    try {
        const response = await fetch(`${API_URL}/estadisticas`);
        const stats = await response.json();
        
        document.getElementById('sensoresActivos').textContent = stats.sensores_activos;
        document.getElementById('totalPlantas').textContent = stats.plantas;
        document.getElementById('totalMediciones').textContent = stats.total_mediciones;
        
        document.getElementById('statusText').textContent = 'CONNECTED';
        document.getElementById('statusText').style.color = '#00ff00';
        
    } catch (error) {
        console.error('Error al actualizar estadísticas:', error);
        document.getElementById('statusText').textContent = 'ERROR';
        document.getElementById('statusText').style.color = '#ff0000';
    }
}

// Actualizar todo
async function updateAll() {
    await updatePlantas();
    await updateCharts();
    await updateEstadisticas();
}

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Iniciando Jardín IoT Monitor...');
    initCharts();
    updateAll();
    
    // Actualizar cada 3 segundos
    setInterval(updateAll, UPDATE_INTERVAL);
    console.log('✓ Auto-actualización activada');
});
