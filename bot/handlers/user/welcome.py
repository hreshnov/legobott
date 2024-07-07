from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
import asyncio

# [IMPORT DATABASE REQUESTS]
from bot.database.requests import set_user
from bot.keyboards.joinkb import main_kb

from aiogram.types.chat_join_request import ChatJoinRequest

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    set_user(user_id)

    await message.answer(f'Привіт, <b>{user_name}</b>', reply_markup=main_kb, parse_mode='HTML')

@router.chat_join_request()
async def accept(event: ChatJoinRequest):
    await event.approve()
