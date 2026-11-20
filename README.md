# Proyecto 3 - Simulador de máquinas de Turing

Simulador determinista de una cinta y un lector. Lee la especificación YAML,
imprime la configuración inicial y todas las configuraciones siguientes, y
muestra el contenido final de la cinta. No tiene límites programados de pasos,
estados ni extensión de cinta; depende de los recursos disponibles del equipo.

## Instalación y ejecución

Se necesita Python 3.10 o posterior. Abra una terminal dentro de esta carpeta:

```bash
python -m pip install -r requirements.txt
python simulador.py maquinas/compresion.yaml 0011100110
python simulador.py maquinas/sustitucion.yaml "111#11#1"
```

Resultados esperados: `0010010` y `00010010`, respectivamente.
Para probar una entrada vacía use `""` como segundo argumento.
Para cancelar una máquina, presione Ctrl+C. Una cancelación no se presenta como
resultado final. Si la máquina no se detiene, la simulación sigue hasta cancelarla.

Cada línea muestra el número de transiciones, la posición del lector, la primera
posición visible y la cinta. `[q:1]` indica que el estado es q y el lector está
sobre un 1. Los índices pueden ser negativos. Las celdas fuera de la zona visible
contienen el símbolo blanco.

## Sintaxis YAML

```yaml
mt:
  estados: [q0, q1]
  alfabeto: ['0', '1', B]
  estado_inicial: q0
  blanco: B
  transiciones:
    - 'q0 1 0 q1'
    - 'q1 0 R q0'
```

Una cuádrupla tiene el formato `estado lectura acción siguiente_estado`.
`L` mueve una celda a la izquierda; `R` mueve una celda a la derecha. Otra
acción escribe el símbolo indicado y no mueve el lector. No se escribe y mueve
en la misma transición. El estado siempre cambia al destino especificado.
Para escribir literalmente L o R use `=L` o `=R`; el prefijo `=` permite
escribir cualquier símbolo declarado (para escribir `=`, use `==`).

Use comillas para los símbolos numéricos y las transiciones. Estados y símbolos
son textos no vacíos sin espacios. Para símbolos de varias letras use entrada
por tokens: `python simulador.py mi_maquina.yaml "rojo azul" --tokens`.
Sin esa opción cada carácter de entrada es una celda.

El alfabeto de entrada y de cinta es el mismo, como pide el proyecto. El blanco
se declara explícitamente y pertenece al alfabeto. Se permiten listas de
transiciones vacías; se prohíben pares estado/lectura repetidos, elementos no
declarados, claves YAML repetidas y campos incorrectos.

La ejecución se detiene cuando no existe transición para el estado y símbolo
actuales. Esto significa detención, no aceptación automática de un lenguaje.
El resultado incluye desde la primera hasta la última celda no blanca, sin
eliminar blancos internos. Una cinta totalmente blanca representa la cadena
vacía. No se interpreta la salida como número ni se aplica notación unaria.

## Máquinas de ejemplo

### Compresión de bloques de unos

Dominio previsto: cadenas sobre {0,1}, incluida la cadena vacía. `X` es una marca
de trabajo que no se usa en las entradas de ejemplo.

Se recorre la cinta recordando si el símbolo anterior era uno. Al encontrar otro
uno consecutivo, se marca con X. Se desplaza el sufijo una celda a la izquierda,
se borra la marca final y se regresa al inicio. Se repite hasta que no haya
unos consecutivos. El simulador no contiene esta lógica: está en el YAML.

| Entrada | Salida |
|---|---|
| 0011100110 | 0010010 |
| 111011 | 101 |
| 000 | 000 |
| 1111 | 1 |
| cadena vacía | cadena vacía |

### Sustitución de símbolos

Dominio previsto: cadenas sobre {1,#}, incluida la cadena vacía.
Cada 1 se reemplaza por 0 y cada # por 1. Después de escribir se avanza una celda.
Esta máquina implementa una sustitución; no calcula cantidades en binario.

| Entrada | Salida |
|---|---|
| 111#11#1 | 00010010 |
| 1#1 | 010 |
| ### | 111 |
| cadena vacía | cadena vacía |

El simulador admite cualquier entrada de su alfabeto; estas transformaciones
solo se garantizan en sus dominios previstos. B representa blanco, no un
carácter ordinario dentro de las cadenas de estos ejemplos.

## Organización

- `simulador.py`: validación YAML, cinta, ejecución y terminal.
- `maquinas/compresion.yaml`: transiciones de compresión.
- `maquinas/sustitucion.yaml`: transiciones de sustitución.
- `test_simulador.py`: pruebas automáticas.

Ejecute las pruebas con `python -m unittest -v`.

## Crecimiento (para el documento)

Sea n la longitud de la entrada. Con búsqueda promedio constante en los
diccionarios de Python, cada transición tiene costo promedio O(1), sin contar
la impresión. Estas cotas cuentan operaciones, no segundos medidos.

| Máquina | Transiciones, peor caso | Simulador mostrando todas las configuraciones |
|---|---|---|
| Compresión | Θ(n²) | Θ(n³) |
| Sustitución | Θ(n), exactamente 2n | Θ(n²) |

En compresión hay a lo sumo n-1 eliminaciones, cada una con un desplazamiento
y un regreso de O(n). La entrada formada solo por unos alcanza el orden
cuadrático. Cada descripción recorre la parte visible de la cinta; en esa
familia la suma del costo de mostrar todas las configuraciones es cúbica.
En sustitución hay una escritura y un movimiento por símbolo. La cinta mantiene
n celdas y se muestra en cada paso, por lo que la impresión cuesta Θ(n²).
Las cotas se entienden para n creciente; la entrada vacía cuesta O(1).
El espacio de trabajo es O(n) en ambos ejemplos, sin acumular la traza en memoria.
Si se guarda la salida en un archivo, su tamaño crece con la columna de impresión.

## Pendientes de entrega

Agregar integrantes y carnés confirmados, enlace del repositorio y enlace del
video. Preparar el documento final con diagrama de flujo y el video no listado
de máximo 7 minutos. Cada integrante debe aportar cambios reales al repositorio.
