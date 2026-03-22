# Metodología y Teoría de los Cálculos

Documentación técnica de los modelos matemáticos y fisiológicos que usa el agente para determinar los objetivos calóricos personalizados.

---

## Índice

1. [Tasa Metabólica Basal (TMB / BMR)](#1-tasa-metabólica-basal-tmb--bmr)
2. [Gasto Energético Total Diario (GETD / TDEE)](#2-gasto-energético-total-diario-getd--tdee)
3. [Cálculo del Objetivo Calórico](#3-cálculo-del-objetivo-calórico)
4. [Límites de Seguridad](#4-límites-de-seguridad)
5. [Estimación de Macronutrientes](#5-estimación-de-macronutrientes)
6. [Supuestos y Limitaciones](#6-supuestos-y-limitaciones)
7. [Referencias](#7-referencias)

---

## 1. Tasa Metabólica Basal (TMB / BMR)

### ¿Qué es?

La **Tasa Metabólica Basal** (TMB) es la cantidad mínima de energía que el cuerpo necesita para mantener sus funciones vitales en reposo absoluto: respiración, circulación sanguínea, regulación de temperatura, síntesis celular, etc. Representa entre el **60–75% del gasto energético total** de una persona sedentaria.

### Ecuación de Mifflin-St Jeor

El agente usa la **ecuación de Mifflin-St Jeor (1990)**, considerada la más precisa para la población general según múltiples meta-análisis:

```
Hombres:  TMB = (10 × peso_kg) + (6.25 × talla_cm) − (5 × edad) + 5
Mujeres:  TMB = (10 × peso_kg) + (6.25 × talla_cm) − (5 × edad) − 161
```

#### Ejemplo

Para un hombre de **80 kg, 171 cm, 30 años**:

```
TMB = (10 × 80) + (6.25 × 171) − (5 × 30) + 5
    = 800 + 1068.75 − 150 + 5
    = 1723.75 ≈ 1724 cal/día
```

### ¿Por qué Mifflin-St Jeor y no otras ecuaciones?

| Ecuación | Año | Precisión (vs calorimetría indirecta) | Observaciones |
|----------|-----|---------------------------------------|---------------|
| Harris-Benedict (revisada) | 1984 | ±10–15% | Sobreestima en obesos |
| Mifflin-St Jeor | 1990 | ±5–8% | Más precisa para peso normal y sobrepeso |
| Katch-McArdle | 1975 | ±3–5% | Requiere % de grasa corporal (no disponible) |
| Schofield | 1985 | ±10% | Diseñada para poblaciones infantiles y mayores |

Mifflin-St Jeor es el **estándar recomendado por la Academy of Nutrition and Dietetics** cuando no se dispone de medición de composición corporal.

---

## 2. Gasto Energético Total Diario (GETD / TDEE)

### ¿Qué es?

El **Gasto Energético Total Diario** (TDEE, por sus siglas en inglés) representa las calorías que el cuerpo gasta a lo largo de un día real, incluyendo actividad física, digestión (efecto térmico de los alimentos) y movimiento espontáneo.

### Método del Factor de Actividad

Se calcula multiplicando la TMB por un **factor de actividad** (también llamado PAL — *Physical Activity Level*):

```
TDEE = TMB × Factor_de_Actividad
```

| Nivel | Factor | Descripción |
|-------|--------|-------------|
| `sedentary`   | 1.20  | Trabajo de escritorio, sin ejercicio |
| `light`       | 1.375 | Ejercicio ligero 1–3 días/semana |
| `moderate`    | 1.55  | Ejercicio moderado 3–5 días/semana |
| `active`      | 1.725 | Ejercicio intenso 6–7 días/semana |
| `very_active` | 1.90  | Trabajo físico o entrenamiento doble diario |

Estos factores provienen de los valores PAL del **Institute of Medicine (IOM)** y son ampliamente validados en la literatura científica.

#### Ejemplo (continuación)

```
TDEE = 1724 × 1.55   (nivel moderado)
     = 2672 cal/día
```

Esto significa que esa persona necesita **2,672 cal/día** para mantener su peso actual con su nivel de actividad.

### Componentes del TDEE

El gasto total se descompone así (valores aproximados para adulto activo):

```
TDEE
 ├── TMB (~65%)          → Metabolismo basal
 ├── TEF (~10%)          → Efecto térmico de los alimentos (digestión)
 ├── NEAT (~15%)         → Termogénesis por actividad no ejercicio (caminar, gesticular)
 └── EAT (~10%)          → Actividad física planificada (ejercicio)
```

> **NEAT** (*Non-Exercise Activity Thermogenesis*) es el componente más variable entre individuos y el más difícil de estimar. Es por esto que los factores de actividad son aproximaciones.

---

## 3. Cálculo del Objetivo Calórico

### Principio del balance energético

El peso corporal está gobernado por la **primera ley de la termodinámica** aplicada a sistemas biológicos:

```
ΔPeso = Energía_ingerida − Energía_gastada
```

- Si **ingieres > gastas** → superávit → ganancia de peso
- Si **ingieres < gastas** → déficit → pérdida de peso
- Si **ingieres = gastas** → equilibrio → mantenimiento

### Equivalencia calórica del tejido adiposo

Un kilogramo de tejido adiposo humano contiene aproximadamente **7,700 kilocalorías** de energía almacenada:

```
1 kg de grasa ≈ 7,700 kcal
```

> **Nota:** Este valor es una aproximación ampliamente usada. El tejido adiposo real contiene ~87% de grasa pura (9 kcal/g), agua, proteínas y minerales. La cifra exacta varía entre 7,000 y 8,000 kcal/kg según la composición corporal individual. 7,700 es el valor de consenso clínico.

### Déficit / superávit diario necesario

Para lograr un cambio de peso objetivo en un plazo determinado:

```
Cambio_total (kcal) = kg_a_cambiar × 7,700

Ajuste_diario (kcal/día) = Cambio_total / (semanas × 7)
```

#### Ejemplo — Perder 5 kg en 8 semanas

```
Cambio_total = 5 kg × 7,700 = 38,500 kcal

Ajuste_diario = 38,500 / (8 × 7) = 38,500 / 56 = 687.5 ≈ 688 kcal/día

Objetivo = TDEE − Ajuste = 2,672 − 688 = 1,984 cal/día
```

### Objetivo según tipo de meta

| Meta | Fórmula |
|------|---------|
| Perder peso | `Objetivo = TDEE − min(déficit_calculado, 1,000)` |
| Ganar peso  | `Objetivo = TDEE + min(superávit_calculado, 500)` |
| Mantener    | `Objetivo = TDEE` |

---

## 4. Límites de Seguridad

El agente aplica **caps de seguridad** para evitar déficits o superávits extremos que sean peligrosos o contraproducentes.

### Límite máximo de déficit: 1,000 kcal/día

```python
MAX_DAILY_DEFICIT = 1000  # kcal/día
```

**Justificación fisiológica:**

- Un déficit de 1,000 kcal/día equivale a perder ~0.9 kg/semana.
- Déficits mayores aumentan el riesgo de **pérdida de masa muscular**, ya que el cuerpo recurre al catabolismo proteico cuando la energía disponible es insuficiente.
- El **Very Low Calorie Diet (VLCD)** — dietas de < 800 kcal/día — solo se aplican bajo supervisión médica estricta.
- La Academia Americana de Medicina de la Obesidad recomienda no superar 0.5–1 kg/semana de pérdida para preservar masa magra.

**¿Qué pasa si el objetivo calculado supera el límite?**

```
Si déficit_calculado > 1,000 → se usa 1,000
→ El plazo real será mayor al plazo solicitado
```

El agente no modifica el plazo indicado por el usuario; simplemente aplica un déficit seguro y el peso se perderá a un ritmo más gradual que el esperado.

### Límite máximo de superávit: 500 kcal/día

```python
MAX_DAILY_SURPLUS = 500  # kcal/día
```

**Justificación fisiológica:**

- Un superávit de 500 kcal/día permite ganar ~0.45 kg/semana.
- Superávits mayores tienden a generar **ganancia de grasa desproporcionada** respecto a la masa muscular, especialmente sin entrenamiento de fuerza intensivo.
- La síntesis proteica muscular (*muscle protein synthesis*) tiene una tasa máxima de aproximadamente 0.25–0.5 kg de músculo por semana en condiciones óptimas. Aportar más calorías no acelera este proceso.

---

## 5. Estimación de Macronutrientes

Los macros mostrados en el plan son **estimaciones generadas por el modelo de lenguaje** basadas en la composición típica de los alimentos seleccionados. No se calculan algorítmicamente en el código; son producidos por Claude a partir de tablas nutricionales de referencia.

### Distribución recomendada por meta

| Macro | Perder peso | Mantener | Ganar peso |
|-------|-------------|----------|------------|
| Proteína | 1.6–2.2 g/kg peso | 1.2–1.6 g/kg | 1.6–2.2 g/kg |
| Grasa | 20–35% de calorías | 25–35% | 25–35% |
| Carbohidratos | Resto | Resto | Resto |

**La proteína alta en déficit** es especialmente importante porque:
1. Preserva la masa muscular durante la pérdida de peso
2. Tiene el mayor efecto térmico (~25–30% de las calorías de proteína se usan en su digestión)
3. Genera mayor saciedad que carbohidratos o grasas

---

## 6. Supuestos y Limitaciones

| Supuesto | Limitación real |
|----------|----------------|
| Composición corporal homogénea | Personas con alta masa muscular tienen TMB mayor; el agente subestima su gasto |
| Factor de actividad constante | El nivel de actividad varía día a día; el factor es un promedio semanal |
| 7,700 kcal = 1 kg grasa | La pérdida real incluye agua y músculo, no solo grasa |
| TDEE estable | Al perder peso, el TDEE baja — el agente no recalcula dinámicamente |
| Calorías de los alimentos exactas | Las etiquetas nutricionales tienen ±20% de margen de error permitido por la FDA |
| Adaptación metabólica | Con dieta prolongada, el metabolismo se adapta reduciendo el TDEE (efecto "meseta") |

### Recomendación práctica

Recalibrar el perfil en `config.json` cada **3–4 semanas** actualizando el peso actual. Esto permite que el agente recalcule el TDEE y el déficit con datos más precisos, compensando la adaptación metabólica.

---

## 7. Referencias

- Mifflin MD, St Jeor ST, et al. *"A new predictive equation for resting energy expenditure in healthy individuals."* Am J Clin Nutr. 1990;51(2):241-7.
- Frankenfield D, et al. *"Comparison of predictive equations for resting metabolic rate in healthy nonobese and obese adults."* J Am Diet Assoc. 2005;105(5):775-789.
- Hall KD, et al. *"Quantification of the effect of energy imbalance on bodyweight."* Lancet. 2011;378(9793):826-837.
- Institute of Medicine. *Dietary Reference Intakes for Energy, Carbohydrate, Fiber, Fat, Protein and Amino Acids.* Washington DC: National Academies Press; 2005.
- Trexler ET, et al. *"Metabolic adaptation to weight loss: implications for the athlete."* J Int Soc Sports Nutr. 2014;11(1):7.
- Helms ER, et al. *"A systematic review of dietary protein during caloric restriction in resistance trained lean athletes."* J Int Soc Sports Nutr. 2014;11(1):20.
