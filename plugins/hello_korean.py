# encoding: utf-8

from will.plugin import WillPlugin
from will.decorators import respond_to, periodic, hear, randomly, route, rendered_template, require_settings


class BonjourPlugin(WillPlugin):

    @respond_to(u'안녕')
    def say_hi_will(self, message):
        self.reply(message, u'안녕하세요')

    @respond_to(u'사과해')
    def say_sorry_will(self, message):
        self.reply(message, u'기본 설정에 문제가 있었습니다. 죄송합니다.')
