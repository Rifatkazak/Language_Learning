import streamlit as st
from core.session import (
    PAGE_HOME, PAGE_QUICK, PAGE_FLASH, PAGE_QUIZ, PAGE_GAMES,
    PAGE_CHALLENGE, PAGE_WORDLIST, PAGE_ADD, PAGE_STATS, PAGE_CONV,
)
import views.home as home
import views.quick_actions as quick_actions
import views.flashcard as flashcard
import views.quiz as quiz
import views.games as games
import views.challenge as challenge
import views.word_list as word_list
import views.add_word as add_word
import views.stats as stats
import views.ai_conversation as ai_conversation


def route(page_name: str, words: list, custom_words: list) -> None:
    handlers = {
        PAGE_HOME:      lambda: home.render(words, custom_words),
        PAGE_QUICK:     lambda: quick_actions.render(words, custom_words),
        PAGE_FLASH:     lambda: flashcard.render(words, custom_words),
        PAGE_QUIZ:      lambda: quiz.render(words, custom_words),
        PAGE_GAMES:     lambda: games.render(words, custom_words),
        PAGE_CHALLENGE: lambda: challenge.render(words, custom_words),
        PAGE_WORDLIST:  lambda: word_list.render(words, custom_words),
        PAGE_ADD:       lambda: add_word.render(words, custom_words),
        PAGE_STATS:     lambda: stats.render(words, custom_words),
        PAGE_CONV:      lambda: ai_conversation.render(words, custom_words),
    }
    fn = handlers.get(page_name, handlers[PAGE_HOME])
    fn()
