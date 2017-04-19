# encoding: utf-8

from datetime import datetime

from will.mixins import StorageMixin

from will.plugin import WillPlugin
from will.decorators import respond_to

RESPOND_TO = {
    u'HELP': u'^사용법$',
    u'START_POLL': u'^참여하실분$',
    u'END_POLL': u'^조사종료해$',
    u'ATTEND': u'^참석$',
    u'WILL_BE': u'^추가될기능$',
    u'hello': u'',
    u'안녕': u'',
    u'사과해': u'',
}

RESPOND_MSG = {
    u'NOT_END_POLL': u'진행중인 투표가 있네요. 먼저 종료해주세요.',
    u'GUIDE_POLL': u'참석하시면 저에게 \'{}\'이라고 답해주세요.'.format(RESPOND_TO['ATTEND']),
    u'ANSWERED': u'{} 님은 이미 참석한다고 답하셨어요.',
    u'THANKS': u'{} 님 답변 감사합니다.',
    u'RESULT': u'총 {}명의 다음의 회원들이 참석합니다.\n{}',
    u'NOT_MATCHED': u'그런 고오급 기능은 {}님이 만들어 주실꺼에요.',
    u'WILL_BE': u'Google Sheets와 연동...이 언젠가는 될꺼에요!',
}

NOT_MATCHED = '|'.join(RESPOND_TO.values())
NOT_MATCHED = u'^(?!' + NOT_MATCHED + u').*$'


class MeetingData(object):

    def __init__(self, title=None, date=None, proposer=None):
        self.title = title
        self.created_at = datetime.now()
        self.date = date
        self.participants = []
        self.proposer = proposer

    def add_participant(self, participant):
        self.participants.append(participant)


class MeetingManager(StorageMixin):
    _redis_meeting_key = 'ygy_will_bot:poll:meeting'

    def __init__(self):
        super(StorageMixin, self).__init__()
        # only one :) It's enough for now
        self.meeting = self.load(self._redis_meeting_key, MeetingData())

    def save_meeting(self):
        self.save(self._redis_meeting_key, self.meeting)


class PollPlugin(WillPlugin):

    def __init__(self):
        super(PollPlugin, self).__init__()
        self.poll_result = {}
        self.poll_start = False

    @respond_to(NOT_MATCHED)
    def not_matched(self, message):
        self.reply(message,
                   RESPOND_MSG['NOT_MATCHED'].format(
                       self._caller_name(message)))

    @respond_to(RESPOND_TO['WILL_BE'])
    def will_be(self, message):
        self.reply(message, RESPOND_MSG['WILL_BE'])

    @respond_to(RESPOND_TO['HELP'])
    def help_poll(self, message):
        msg = """
        다음의 명령어가 가능합니다.
        * {}
        * {}
        * {}
        """.format(RESPOND_TO['START_POLL'],
                   RESPOND_TO['END_POLL'], RESPOND_TO['WILL_BE'])
        self.reply(message, msg)

    @respond_to(RESPOND_TO['START_POLL'])
    def start_poll(self, message):
        if self.poll_start:
            self.reply(message, RESPOND_MSG['NOT_END_POLL'])
            return

        self.poll_start = True
        self.reply(message, RESPOND_MSG['GUIDE_POLL'])

        caller = self._caller_name(message)
        title = self._poll_title(message)

        self.meeting_manager = MeetingManager()
        self.meeting_manager.meeting.proposer = caller
        self.meeting_manager.meeting.title = title
        self.meeting_manager.save_meeting()

    def _caller_name(self, message):
        return message['from'].resource

    def _poll_title(self, message):
        return message['from'].resource

    @respond_to(RESPOND_TO['ATTEND'])
    def count_attend(self, message):
        if not self.poll_start:
            return

        caller = self._caller_name(message)

        if caller in self.meeting_manager.meeting.participants:
            self.reply(message, RESPOND_MSG['ANSWERED'].format(caller))
            return

        self.meeting_manager.meeting.add_participant(caller)
        self.reply(message, RESPOND_MSG['THANKS'].format(caller))
        self.meeting_manager.save_meeting()

    @respond_to(RESPOND_TO['END_POLL'])
    def end_poll(self, message):
        if not self.poll_start:
            return
        self.poll_start = False
        self.reply(message, RESPOND_MSG['RESULT'].format(
            len(self.meeting_manager.meeting.participants),
            self.meeting_manager.meeting.participants))
