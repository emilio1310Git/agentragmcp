def create_sample_documents():
    """
    Crea documentos de ejemplo para cada temática
    """
    print("📄 CREANDO DOCUMENTOS DE EJEMPLO...")
    
    base_path = Path("data/documents")
    base_path.mkdir(parents=True, exist_ok=True)
    
    sample_data = {
        "plants": [
            {
                "filename": "cuidados_basicos.txt",
                "content": """# Cuidados Básicos de Plantas

## Riego
Las plantas necesitan agua de forma regular, pero no en exceso. 
La frecuencia depende de la especie, estación y tipo de suelo.

### Manzano (Malus domestica)
- Riego profundo semanal en verano
- Reducir en invierno
- Evitar encharcamiento

## Luz Solar
La mayoría de plantas necesitan entre 6-8 horas de luz solar directa.

## Suelo
El suelo debe tener buen drenaje y estar enriquecido con materia orgánica.
"""
            },
            {
                "filename": "plantas_comunes.txt", 
                "content": """# Plantas Comunes en Jardinería

## Tomate (Solanum lycopersicum)
Planta anual de la familia Solanaceae. 
Requiere tutor, riego constante y mucha luz solar.

## Vid (Vitis vinifera)
Planta trepadora perenne. Requiere poda anual 
y protección contra heladas en invierno.

## Manzano (Malus domestica)
Árbol frutal caducifolio. Floración en primavera,
cosecha en otoño. Requiere polinización cruzada.
"""
            }
        ],
        
        "pathology": [
            {
                "filename": "enfermedades_comunes.txt",
                "content": """# Enfermedades Comunes en Plantas

## Mildiu en Vid
Enfermedad fúngica que afecta hojas y frutos.
Síntomas: manchas amarillentas en hojas, 
pelusa blanca en el envés.

Tratamiento: Fungicidas cúpricos preventivos.

## Sarna del Manzano
Causada por Venturia inaequalis.
Síntomas: manchas marrones en hojas y frutos.

Prevención: Poda para ventilación, 
tratamientos fungicidas en primavera.

## Oídio
Hongo que causa polvo blanco en hojas.
Afecta muchas especies. Tratamiento con azufre.
"""
            }
        ],
        
        "general": [
            {
                "filename": "botanica_basica.txt",
                "content": """# Conceptos Básicos de Botánica

## Fotosíntesis
Proceso por el cual las plantas convierten
luz solar, CO2 y agua en glucosa y oxígeno.

## Partes de la Planta
- Raíces: absorción de agua y nutrientes
- Tallo: soporte y transporte
- Hojas: fotosíntesis
- Flores: reproducción

## Clasificación Básica
- Monocotiledóneas: un cotiledón (gramineas)
- Dicotiledóneas: dos cotiledones (mayoría)

## Ciclo de Vida
Germinación → Crecimiento → Floración → 
Fructificación → Dispersión de semillas
"""
            }
        ]
    }
    
    # Crear archivos
    total_created = 0
    for topic, files in sample_data.items():
        topic_dir = base_path / topic
        topic_dir.mkdir(exist_ok=True)
        
        for file_info in files:
            file_path = topic_dir / file_info["filename"]
            
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info["content"])
                print(f"✅ Creado: {file_path}")
                total_created += 1
            else:
                print(f"⚠️ Ya existe: {file_path}")
    
    print(f"\n📊 RESUMEN: {total_created} archivos creados")
    return total_created > 0