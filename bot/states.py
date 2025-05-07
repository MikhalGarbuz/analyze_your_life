from aiogram.fsm.state import State, StatesGroup

class DefineParam(StatesGroup):
    NAME = State()
    ROLE = State()
    TYPE = State()
    CLASS_MIN = State()
    CLASS_MAX = State()
    CONFIRM = State()

class EnterValue(StatesGroup):
    WAIT_VALUE = State()

class DefineExp(StatesGroup):
    NAME      = State()
    CONFIRM   = State()

class EnterData(StatesGroup):
    DATE = State()
    SELECT_EXP = State()
    SELECT_PARAM = State()
    WAIT_VALUE = State()
    CONFIRM_SAVE = State()

class DeleteExp(StatesGroup):
    SELECT  = State()  
    CONFIRM = State()

class ShowStats(StatesGroup):
    SELECT_EXP = State()