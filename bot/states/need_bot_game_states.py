from aiogram.fsm.state import StatesGroup, State

class NeedBotGameStates(StatesGroup):
    question: State = State()
    answer: State = State()
    coupon: State = State() 