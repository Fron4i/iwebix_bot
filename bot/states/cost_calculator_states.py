from aiogram.fsm.state import StatesGroup, State

class CostCalculatorStates(StatesGroup):
    """Состояния FSM для мастера расчёта стоимости."""
    choose_template: State = State()
    choose_modules: State = State()
    choose_support: State = State() 