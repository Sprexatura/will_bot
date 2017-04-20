#!/usr/bin/python
# -*- coding:utf-8 -*-
# encoding: utf-8

from datetime import datetime

from will.plugin import WillPlugin
from will.decorators import respond_to, periodic, hear, randomly, route, rendered_template, require_settings


class QuestionData(object):
    def __init__(self, answer, created_at=None, questioned_at=None, score=0):
        self.created_at = created_at or datetime.now()
        self.questioned_at = questioned_at or datetime.now()
        self.answer = answer
        self.score = score

    def refresh_questioned_at(self):
        self.questioned_at = datetime.now()

    def to_dict(self):
        return {
            'created_at': self.created_at,
            'questioned_at': self.questioned_at,
            'answer': self.answer,
            'score': self.score
        }


class SimSimPlugin(WillPlugin):
    _redis_key = 'questions'

    def __init__(self):
        self._load_questions()

    def _load_questions(self):
        data = self.load(self._redis_key, {})
        safe_data = {question: [QuestionData(**datum) for datum in question_data if isinstance(datum, dict)]
                     for question, question_data in data.items()}
        self._questions = safe_data

    def _save_questions(self):
        safe_data = {question: [datum.to_dict() for datum in question_data]
                     for question, question_data in self._questions.items()}
        self.save(self._redis_key, safe_data)

    def _register(self, question, answer):
        self._load_questions()

        if question not in self._questions:
            self._questions[question] = []
        self._questions[question].append(QuestionData(answer))

        self._save_questions()

    def _answer(self, question):
        self._load_questions()

        question_data = self._questions.get(question)
        if not question_data:
            return

        datum = self._find_highest_score_question(question_data)
        datum.refresh_questioned_at()
        self._save_questions()
        return datum.answer

    def _find_recently_answered_question(self):
        self._load_questions()
        now = datetime.now()
        for question, data in self._questions.items():
            for datum in data:
                if (now - datum.questioned_at).seconds < 10:
                    return datum

    @staticmethod
    def _find_highest_score_question(data):
        result = None
        highest = 0
        for datum in data:
            if datum.score >= highest:
                highest = datum.score
                result = datum
        return result


    @respond_to(u'질문 (?P<question>".*") 대답 (?P<answer>".*")')
    def register(self, message, question, answer):
        def _is_valid_request():
            return question and answer

        if not _is_valid_request():
            self.reply(message, u'뭐라구요?')
            return

        self._register(question, answer)

    @respond_to(u'상연아 (?P<question>".*")')
    def answer(self, message, question):
        answer = self._answer(question)
        if not answer:
            self.reply(message, u'아 뭐라 말해야될지 모르겠다.')
            return

        self.reply(message, answer)

    @hear(u'(?P<laugh>ㅋ+)')
    def log_laugh_at_answer(self, message, laugh):
        question_data = self._find_recently_answered_question()
        question_data.score += len(laugh)
