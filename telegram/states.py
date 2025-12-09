"""Состояния FSM для регистрации"""
from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния процесса регистрации"""
    waiting_for_full_name = State()  # Ожидание ввода полного ФИО
    confirming_full_name = State()  # Подтверждение введенного ФИО
