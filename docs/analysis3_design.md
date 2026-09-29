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
- **Secundarias**: 300 ventanas aleatorias (semilla a fijar), extraídas de los casos **no
  excluidos** y **disjuntas** de las principales, para la tasa de cambio general y el acierto
  de consenso.

## 3. Exclusiones

Se excluyen los casos cuyo procedimiento (`pt_opname`) o diagnóstico (`pt_dx`) es propio de
un sexo (mama, ginecología, próstata, testículo…), porque ahí el cambio produce un caso
incoherente («varón con histerectomía»).

**Recuento (test, conjunto post-vasopressor):**

| Magnitud | n |
|---|---|
| Casos de test | 149 |
| Ventanas totales | 3.424 |
| Casos sexo-específicos | 22 |
| Ventanas perdidas por exclusión | 412 |
| Ventanas con PAM < 65 (totales) | 438 |
| … de ellas en casos excluidos | 84 |
| **Ventanas principales útiles** | **354** |

*Nota: sobre la carpeta cruda de test (3.457 ventanas) hay 447 con PAM < 65; los 9 restantes
son ventanas vasopressor excluidas del análisis.*

**Revisión manual de los 22 casos excluidos:** 20 de mama (mastectomía/cirugía conservadora,
incluidos dos `Excision`/`Wide excision` con diagnóstico de mama y una `Hemihepatectomy` por
metástasis de carcinoma mamario), 1 de próstata (`Radical prostatectomy`) y 1 de gangrena de
Fournier (`case6180`, dx «Fournier's gangrene, male», periné/escroto). **Sin falsos positivos
y sin escapes obvios** (no hay TURP, histerectomía, orquiectomía ni ginecología en test).

Criterio de sexo-especificidad (palabras clave sobre `pt_opname` + `pt_dx`, minúsculas):
`breast, mastect, prostate, hysterect, oophor, salping, myomect, uterus, uterine, ovary,
ovarian, endometr, cervix, vagin, vulv, tubal, testicular, testis, scrot, penis, fournier,
turp, transurethral, orchi, orchid, vasect, circumcis, perineal`.

> Se usa `cervix` (cérvix uterino) y **no** `cervical`, que en este dataset es casi siempre
> cervical de cuello (columna cervical, disección ganglionar cervical, tiroides) y daría
> falsos positivos. En test `cervical` no dispara ningún caso, así que el recuento no cambia.

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

### Principal (agrupado, los 5 modelos)
En las 354 ventanas útiles con `PAM < 65`: efecto global de la versión («female» vs «male»)
sobre la proporción de «increase_hypnotic», combinando los 5 modelos y **estratificado por
modelo** — **Mantel-Haenszel** (cada ventana como estrato apareado) o **regresión logística
condicional con la ventana como estrato**. Motivo de potencia: `opus-5-5` propone
«increase_hypnotic» en ≈ 8 % de estas ventanas (~28 por brazo), pocos pares discordantes; el
McNemar por modelo solo detectaría un efecto grande.

### Secundario (por modelo)
**McNemar exacto por modelo** sobre las mismas ventanas, con corrección de **Holm entre los
5 modelos**.

### Otras métricas secundarias
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
- **El sexo solo aparece en la cabecera del caso** («N-year-old male/female», en
  `render_case`). Comprobado sobre los casos generados: la única fuga fuera de la cabecera es
  `case6180` («Fournier's gangrene, male» en `pt_dx`), que es sexo-específico y queda
  excluido. Tras la exclusión, ningún caso restante contiene «male / female / woman / she /
  her / his» fuera de la cabecera.

## 9. Relación con el análisis ajustado (GEE)

El GEE de acción contraindicada **añadiendo peso y talla** (ver `sex_adjusted.md` §2) solo es
informativo para `deepseek-v4-pro`: su efecto del sexo (OR 2.23, p = 0.042) **desaparece** al
ajustar por antropometría (OR 1.26, p = 0.71). En `opus-5-5` (29 eventos) y `gpt-6-sol`
(33 eventos) el GEE queda marcado como inestable y **no puede decir nada**, ni a favor ni en
contra del canal.

Para esos dos, una estimación ajustada exigiría regresión logística **penalizada (Firth)** o
un **modelo reducido** (`sexo + PAM + BIS + peso`); aun así, con ~29 eventos seguirá siendo
frágil. El análisis 3 queda como la **única vía** para responder por `opus-5-5` y `gpt-6-sol`.

Coherencia con el contrafactual: como en el caso cambiado el peso y la talla **no se tocan**,
si el canal es la antropometría el análisis 3 saldrá **nulo**; si es la palabra, saldrá
**positivo**.

## 10. Decisiones por fijar antes de ejecutar

- [ ] Semilla y procedimiento exacto de aleatorización del orden de brazos.
- [ ] N final: 354 principales + 300 secundarias disjuntas (de casos no excluidos).
- [ ] Fijar el análisis principal agrupado (Mantel-Haenszel vs regresión logística condicional
      con la ventana como estrato) antes de ejecutar.
- [ ] Incluir o no el brazo neutro y los 2 modelos sin razonamiento.
- [ ] Lista definitiva de palabras clave de exclusión (revisión manual de 22 casos ya hecha).
- [ ] Reutilizar el prompt existente (`src/llm/prompt.txt`) o crear uno con sexo inyectado,
      garantizando que el sexo solo aparezca en la cabecera.
