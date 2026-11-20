"""Pruebas: python -m unittest -v"""
from itertools import product
from pathlib import Path
import re
import tempfile
import unittest
import yaml
from simulador import Maquina, Simulador, ErrorEspecificacion

BASE = Path(__file__).parent


def ejecutar(maquina, entrada):
    sim = Simulador(maquina, entrada)
    # El límite solo detecta errores en pruebas; no pertenece al simulador.
    for _ in range(20000):
        if not sim.paso():
            return sim
    raise AssertionError('La máquina de prueba no terminó.')


class Pruebas(unittest.TestCase):
    def test_compresion_exhaustiva(self):
        maquina = Maquina.cargar(BASE / 'maquinas/compresion.yaml')
        for n in range(9):
            for bits in product('01', repeat=n):
                cadena = ''.join(bits)
                with self.subTest(cadena=cadena):
                    sim = ejecutar(maquina, cadena)
                    self.assertEqual(''.join(sim.resultado()), re.sub('1+', '1', cadena))

    def test_sustitucion_exhaustiva(self):
        maquina = Maquina.cargar(BASE / 'maquinas/sustitucion.yaml')
        for n in range(9):
            for simbolos in product('1#', repeat=n):
                cadena = ''.join(simbolos)
                sim = ejecutar(maquina, cadena)
                self.assertEqual(''.join(sim.resultado()), cadena.translate(str.maketrans('1#', '01')))
                self.assertEqual(sim.pasos, 2 * n)

    def test_cinta_izquierda_y_blanco_interno(self):
        maquina = Maquina({'a','b','c','d','fin'}, {'X','B'}, 'a', 'B', {
            ('a','B'): ('mover','L','b'), ('b','B'): ('escribir','X','c'),
            ('c','X'): ('mover','R','d'), ('d','B'): ('mover','R','fin')})
        sim = ejecutar(maquina, ['B', 'X'])
        self.assertEqual(sim.resultado(), ['X','B','X'])
        self.assertIn(-1, sim.cinta)

    def test_validacion_yaml(self):
        base = {'estados':['q'], 'alfabeto':['0','B'], 'estado_inicial':'q',
                'blanco':'B', 'transiciones':['q 0 R q']}
        cambios = [ {'estado_inicial':'otro'}, {'blanco':'?'},
                    {'transiciones':['q 0 R otro']}, {'transiciones':['q ? R q']},
                    {'transiciones':['q 0 ? q']}, {'transiciones':['q 0 R q','q 0 L q']},
                    {'transiciones':['q 0 R']}, {'alfabeto':[0,'B']} ]
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / 'prueba.yaml'
            for cambio in cambios:
                ruta.write_text(yaml.safe_dump({'mt':base | cambio}), encoding='utf-8')
                with self.subTest(cambio=cambio), self.assertRaises(ErrorEspecificacion):
                    Maquina.cargar(ruta)
            ruta.write_text('mt: {}\nmt: {}\n', encoding='utf-8')
            with self.assertRaises(ErrorEspecificacion):
                Maquina.cargar(ruta)

    def test_simbolos_multicaracter_y_escritura_reservada(self):
        datos = {'mt': {'estados':['q','fin'], 'alfabeto':['hola','R','B'],
                       'estado_inicial':'q', 'blanco':'B', 'transiciones':['q hola =R fin']}}
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / 'prueba.yaml'
            ruta.write_text(yaml.safe_dump(datos), encoding='utf-8')
            sim = ejecutar(Maquina.cargar(ruta), ['hola'])
            self.assertEqual(sim.resultado(), ['R'])

    def test_entrada_invalida(self):
        maquina = Maquina.cargar(BASE / 'maquinas/compresion.yaml')
        with self.assertRaises(ErrorEspecificacion):
            Simulador(maquina, ['?'])


if __name__ == '__main__':
    unittest.main()
