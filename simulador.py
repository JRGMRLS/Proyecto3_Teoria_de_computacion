"""Simulador determinista de una cinta, con transiciones de cuatro elementos."""
from dataclasses import dataclass
from pathlib import Path
import argparse
import sys
import yaml


class ErrorEspecificacion(ValueError):
    pass


class CargadorUnico(yaml.SafeLoader):
    """Evita que una clave YAML repetida oculte una definición anterior."""


def mapa_unico(loader, node):
    resultado = {}
    for clave_node, valor_node in node.value:
        clave = loader.construct_object(clave_node, deep=True)
        if not isinstance(clave, str) or clave in resultado:
            raise ErrorEspecificacion('Las claves YAML deben ser textos únicos.')
        resultado[clave] = loader.construct_object(valor_node, deep=True)
    return resultado


CargadorUnico.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapa_unico)


def conjunto(valor, nombre):
    if not isinstance(valor, list) or not valor:
        raise ErrorEspecificacion(f'{nombre} debe ser una lista no vacía.')
    if any(not isinstance(x, str) or not x or any(c.isspace() for c in x) for x in valor):
        raise ErrorEspecificacion(f'{nombre}: use textos entre comillas, sin espacios.')
    if len(set(valor)) != len(valor):
        raise ErrorEspecificacion(f'{nombre} contiene elementos repetidos.')
    return set(valor)


@dataclass
class Maquina:
    estados: set
    alfabeto: set
    inicial: str
    blanco: str
    transiciones: dict

    @classmethod
    def cargar(cls, ruta):
        datos = yaml.load(Path(ruta).read_text(encoding='utf-8'), Loader=CargadorUnico)
        if not isinstance(datos, dict) or set(datos) != {'mt'}:
            raise ErrorEspecificacion('Se espera un objeto YAML con la clave mt.')
        mt = datos['mt']
        campos = {'estados', 'alfabeto', 'estado_inicial', 'blanco', 'transiciones'}
        if not isinstance(mt, dict) or set(mt) != campos:
            raise ErrorEspecificacion('mt debe contener exactamente: ' + ', '.join(sorted(campos)))
        estados = conjunto(mt['estados'], 'estados')
        alfabeto = conjunto(mt['alfabeto'], 'alfabeto')
        inicial, blanco = mt['estado_inicial'], mt['blanco']
        if not isinstance(inicial, str) or inicial not in estados:
            raise ErrorEspecificacion('El estado inicial no pertenece a estados.')
        if not isinstance(blanco, str) or blanco not in alfabeto:
            raise ErrorEspecificacion('El blanco no pertenece al alfabeto.')
        if not isinstance(mt['transiciones'], list):
            raise ErrorEspecificacion('transiciones debe ser una lista (puede estar vacía).')
        tabla = {}
        for numero, linea in enumerate(mt['transiciones'], 1):
            if not isinstance(linea, str) or len(linea.split()) != 4:
                raise ErrorEspecificacion(f'Transición {numero}: se esperan cuatro elementos.')
            origen, lectura, accion, destino = linea.split()
            if origen not in estados or destino not in estados:
                raise ErrorEspecificacion(f'Transición {numero}: estado no declarado.')
            if lectura not in alfabeto:
                raise ErrorEspecificacion(f'Transición {numero}: lectura fuera del alfabeto.')
            # = permite escribir incluso símbolos llamados L, R o que empiezan con =.
            tipo = 'mover' if accion in ('L', 'R') else 'escribir'
            valor = accion[1:] if tipo == 'escribir' and accion.startswith('=') else accion
            if tipo == 'escribir' and valor not in alfabeto:
                raise ErrorEspecificacion(f'Transición {numero}: escritura fuera del alfabeto.')
            if (origen, lectura) in tabla:
                raise ErrorEspecificacion(f'Transición {numero}: par estado/lectura repetido.')
            tabla[origen, lectura] = (tipo, valor, destino)
        return cls(estados, alfabeto, inicial, blanco, tabla)


class Simulador:
    def __init__(self, maquina, entrada):
        if any(s not in maquina.alfabeto for s in entrada):
            raise ErrorEspecificacion('La entrada contiene símbolos fuera del alfabeto.')
        self.maquina = maquina
        self.cinta = {i: s for i, s in enumerate(entrada) if s != maquina.blanco}
        self.cabezal = 0
        self.estado = maquina.inicial
        self.pasos = 0

    def leer(self, posicion):
        return self.cinta.get(posicion, self.maquina.blanco)

    def paso(self):
        transicion = self.maquina.transiciones.get((self.estado, self.leer(self.cabezal)))
        if transicion is None:
            return False
        tipo, valor, destino = transicion
        if tipo == 'mover':
            self.cabezal += 1 if valor == 'R' else -1
        elif valor == self.maquina.blanco:
            self.cinta.pop(self.cabezal, None)
        else:
            self.cinta[self.cabezal] = valor
        self.estado = destino
        self.pasos += 1
        return True

    def descripcion(self):
        izquierda = min(min(self.cinta, default=self.cabezal), self.cabezal)
        derecha = max(max(self.cinta, default=self.cabezal), self.cabezal)
        celdas = [f'[{self.estado}:{self.leer(i)}]' if i == self.cabezal else self.leer(i)
                  for i in range(izquierda, derecha + 1)]
        return f'{self.pasos}: cabeza={self.cabezal}; desde={izquierda}; ' + ' '.join(celdas)

    def resultado(self):
        if not self.cinta:
            return []
        return [self.leer(i) for i in range(min(self.cinta), max(self.cinta) + 1)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('maquina', help='Ruta del archivo YAML')
    parser.add_argument('entrada', help='Cadena; use "" para la cadena vacía')
    parser.add_argument('--tokens', action='store_true', help='Separar símbolos de entrada por espacios')
    args = parser.parse_args()
    try:
        maquina = Maquina.cargar(args.maquina)
        entrada = args.entrada.split() if args.tokens else list(args.entrada)
        simulador = Simulador(maquina, entrada)
    except (OSError, UnicodeError, yaml.YAMLError, ErrorEspecificacion) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    try:
        print(simulador.descripcion())
        while simulador.paso():
            print(simulador.descripcion())
    except KeyboardInterrupt:
        print('\nEjecución cancelada por el usuario; no es un resultado final.')
        return 130
    resultado = simulador.resultado()
    separador = ' ' if args.tokens else ''
    print(f'Detenida: no existe transición para ({simulador.estado}, {simulador.leer(simulador.cabezal)}).')
    print('Resultado:', separador.join(resultado) if resultado else '(cadena vacía)')
    print('Transiciones ejecutadas:', simulador.pasos)
    return 0


if __name__ == '__main__':
    sys.exit(main())
