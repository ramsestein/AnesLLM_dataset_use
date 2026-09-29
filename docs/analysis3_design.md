# Análisis 3 — Contrafactual de sexo (diseño previo a ejecución)

> Documento de diseño fijado **antes** de ejecutar el experimento. Cualquier cambio de
> método debe reflejarse aquí y en su propio commit.

## 1. Objetivo

Aislar el efecto de la **palabra** de sexo en el prompt («male» vs «female»), manteniendo
idéntico el resto del caso. Si el cambio de sexo modifica la decisión del modelo, el efecto
es atribuible a la mención del sexo y no a diferencias reales del paciente.

## 2. Ventanas

- **Principales**: las 438 ventanas de prueba con `PAM < 65` del conjunto de test tras la
  exclusión de vasopressor (3.424 ventanas), donde está la señal del análisis previo.
- **Secundarias**: 300 ventanas aleatorias (semilla a fijar) para la tasa de cambio general
  y el acierto de consenso.

## 3. Exclusiones

Se excluyen los casos cuyo procedimiento (`pt_opname`) o diagnóstico (`pt_dx`) es propio de
un sexo (mama, ginecología, próstata, testículo…), porque ahí el cambio produce un caso
incoherente («varón con histerectomía»).

**Recuento (test, conjunto post-vasopressor):**

| Magnitud | n |
|---|---|
| Casos de test | 149 |
| Ventanas totales | 3.424 |
| Casos sexo-específicos | 21 |
| Ventanas perdidas por exclusión | 391 |
| Ventanas con PAM < 65 (totales) | 438 |
| … de ellas en casos excluidos | 83 |
| **Ventanas principales útiles** | **355** |

*Nota: sobre la carpeta cruda de test (3.457 ventanas) hay 447 con PAM < 65; los 9 restantes
son ventanas vasopressor excluidas del análisis.*

Criterio de sexo-especificidad (palabras clave sobre `pt_opname` + `pt_dx`, minúsculas):
`breast, mastect, prostate, hysterect, oophor, salping, myomect, uterus, uterine, ovary,
ovarian, endometr, cervix, cervical, vagin, vulv, tubal, testicular, testis, scrot, penis`.

## 4. Brazos

1. Versión **«male»** y versión **«female»** del mismo caso, ejecutadas a la vez y en **orden
   aleatorio** (misma semilla), para que la variabilidad entre ejecuciones afecte igual a
   ambas.
2. **Opcional**: tercer brazo neutro sin sexo («a 54-year-old patient») para comprobar si la
   palabra importa en sí misma, no solo la dirección del sexo.

## 5. Modelos

- **Principales (los 5 que razonan)**: `deepseek-v4-pro`, `deepseek-flash`,
  `gemini-3.1-pro-preview`, `gpt-6-sol`, `claude-opus-5-5`.
- **Contraste sin razonamiento (opcional)**: `opus-4-8`, `gpt-5.4`.

## 6. Resultados

### Principal
En las ventanas con `PAM < 65`: proporción de «increase_hypnotic» con la versión femenina
frente a la masculina **de la misma ventana**. **McNemar exacto por modelo**, con corrección
de **Holm entre los 5 modelos**.

### Secundarios
- Proporción de **cualquier acción contraindicada** (red flag) por versión.
- Proporción de ventanas en que **cambia la acción** entre versiones y **dirección** del cambio.
- **Acierto de consenso** por versión.

## 7. Coste estimado

| Configuración | Llamadas |
|---|---|
| 740 ventanas × 2 versiones × 5 modelos | ≈ 7.400 |
| + brazo neutro | ≈ 11.000 |

## 8. Cautelas a declarar

- El **peso y la talla no cambian**: el cambio aísla la palabra, no un paciente del otro sexo
  real. Cualquier diferencia observada no equivale a disparidad clínica.
- Con 149 casos, algunas ventanas comparten caso; la inferencia debe agruparse por caso si se
  comparan tasas entre versiones más allá del McNemar por pares.

## 9. Relación con el análisis ajustado (GEE)

El GEE de acción contraindicada **añadiendo peso y talla** (ver `sex_adjusted.md` §2) muestra
que el efecto del sexo que quedaba en `deepseek-v4-pro` (OR 2.23 → 1.26, p 0.042 → 0.71)
**desaparece** al ajustar por antropometría. El canal probable es la antropometría, no la
palabra; el análisis 3 pierde urgencia como explicación causal pero sigue siendo útil para
aislar el efecto de la palabra en sí.

## 10. Decisiones por fijar antes de ejecutar

- [ ] Semilla y procedimiento exacto de aleatorización del orden de brazos.
- [ ] N final de ventanas principales (355) y secundarias (300) tras exclusiones.
- [ ] Incluir o no el brazo neutro y los 2 modelos sin razonamiento.
- [ ] Lista definitiva de palabras clave de exclusión (validada caso a caso).
- [ ] Reutilizar el prompt existente (`src/llm/prompt.txt`) o crear uno con sexo inyectado.
