import unittest
import os
import glob

from dss_engine import OpenDssEngine
from environment import Environment
from neural_network import Network
from memory import Memory
from random import random


def clear_dir(dir):
    for file in os.scandir(dir):
        if file.name.endswith(".cache"):
            os.unlink(file.path)


# class TestEngine(unittest.TestCase):

    # def test_engine_connection(self):
    #     engine = OpenDssEngine()
    #     with self.assertRaises(Exception):
    #         engine.test_connection()

    #     engine.open_file(os.path.dirname(__file__) + '/test_circuit/IEEE13Nodeckt.dss')
    #     self.assertEqual(engine.test_connection(), None)

    # def test_open_connection(self):
    #     engine = OpenDssEngine()
    #     engine.open_file(os.path.dirname(__file__) + '/test_circuit/IEEE13Nodeckt.dss')
    #     self.assertIsNot(engine._engine, None)
    #     self.assertIsNot(engine._ckt, None)
    #     self.assertIsNot(engine._file, None)

    # def test_kill_connection(self):
    #     engine = OpenDssEngine()
    #     engine.open_file(os.path.dirname(__file__) + '/test_circuit/IEEE13Nodeckt.dss')
    #     engine.kill_session()
    #     self.assertEqual(engine._engine, None)
    #     self.assertEqual(engine._ckt, None)
    #     self.assertEqual(engine._file, None)


# class TestNeuralNetwork(unittest.TestCase):

#     def test_network_sync(self):
#         env = Environment()
#         clear_dir(os.path.join(os.path.dirname(__file__) + "/cache"))
#         env._online_network = Network(len(env._model.get_state().state_space_repr(env._current_step, env._actions_taken, env._weekdays_map[env._model.get_weekday()])), len(env._possible_actions), env._model.get_file_name())
#         clear_dir(os.path.join(os.path.dirname(__file__) + "/cache"))
#         env._target_network = Network(len(env._model.get_state().state_space_repr(env._current_step, env._actions_taken, env._weekdays_map[env._model.get_weekday()])), len(env._possible_actions), env._model.get_file_name())

#         self.assertNotEqual(env._online_network, env._target_network)
#         env.sync_networks()
#         self.assertEquals(env._online_network, env._target_network)


class TestMemory(unittest.TestCase):

    # def test_max_len(self):
    #     mem = Memory(3)
    #     self.assertEqual(len(mem), 0)
    #     mem.add(1)
    #     mem.add(1)
    #     mem.add(1)
    #     self.assertEqual(len(mem), 3)
    #     mem.add(1)
    #     self.assertEqual(len(mem), 3)

    def test_sampling(self):
        mem = Memory(10)
        self.assertEqual(len(mem), 0)
        for i in range(10):
            mem.add(random())
        self.assertEqual(len(mem), 10)
        sample = mem.sample(5)
        self.assertEqual(len(sample), 5)


if __name__ == '__main__':
    unittest.main(verbosity=10)
